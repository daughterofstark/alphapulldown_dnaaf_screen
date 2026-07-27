"""Remote execution planning helpers for Linux AlphaPulldown handoff."""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import os
import platform
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .provenance import git_metadata, sha256_file
from .validation import ValidationError, require, validate_accession

SUPPORTED_SCREENS = {"controls", "transport", "full", "milestone2"}
SUPPORTED_FEATURE_MODES = {"localdb", "mmseqs2"}
DEFAULT_FEATURE_PATTERN = "{record_id}_af3_input.json"
UPSTREAM_CLI_ARGUMENT_KEYS = {
    "create_feature_arguments",
    "structure_inference_arguments",
    "analyze_structure_arguments",
    "recursive_report_arguments",
}
UPSTREAM_CONFIG_KEYS = {
    "input_files",
    "protein_delimiter",
    "exclude_permutations",
    "output_directory",
    "databases_directory",
    "backend_weights_directory",
    "feature_directory",
    "only_generate_features",
    "enable_structure_analysis",
    "generate_recursive_report",
    "recursive_report_arguments",
    "create_feature_arguments",
    "structure_inference_arguments",
    "analyze_structure_arguments",
    "mem_safety_factor",
    "max_mem_mb",
    "feature_create_ram_scaling",
    "feature_create_ram_bytes",
    "feature_create_ram_per_residue_mb",
    "structure_inference_ram_scaling",
    "structure_inference_ram_bytes",
    "structure_inference_ram_per_token_sq_mb",
    "structure_inference_runtime_minutes",
    "max_total_length_alphafold2",
    "max_total_length_alphafold3",
    "max_total_length",
    "max_protein_length",
    "length_filter_fetch_uniprot",
    "alphafold_inference_threads",
    "slurm_partition",
    "slurm_qos",
    "structure_inference_gpus_per_task",
    "structure_inference_gpu_model",
    "structure_inference_gpu_vram_headroom",
    "structure_inference_gpu_tiers",
    "slurm_exclude_nodes",
    "structure_inference_max_runtime",
    "structure_inference_unified_memory",
    "structure_inference_xla_mem_fraction",
    "prediction_container",
    "analysis_container",
}


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            raise ValidationError(f"{path}:{line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        require(bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key)), f"Invalid env key: {key}")
        values[key] = _expand_env_value(value, values)
    return values


def _expand_env_value(value: str, values: dict[str, str]) -> str:
    pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1) or match.group(2)
        if key in values:
            return values[key]
        return os.environ.get(key, match.group(0))

    return pattern.sub(replace, value)


def stable_run_id(prefix: str, *, screen: str | None = None, timestamp: str | None = None) -> str:
    stamp = timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    pieces = [prefix]
    if screen:
        pieces.append(screen)
    pieces.append(stamp)
    return "-".join(pieces)


@dataclass(frozen=True)
class RemoteConfig:
    project_root: Path
    workflow_dir: Path
    conda_env_name: str
    alphapulldown_snakemake_version: str
    feature_config: Path
    prediction_config: Path
    fasta_manifest: Path
    alphapulldown_input_dir: Path
    fasta_dir: Path
    feature_dir: Path
    output_dir: Path
    log_dir: Path
    tmp_dir: Path
    provenance_dir: Path
    databases_dir: Path | None
    backend_weights_dir: Path | None
    feature_mode: str
    feature_pattern: str = DEFAULT_FEATURE_PATTERN
    apptainer_prediction_sif: Path | None = None
    apptainer_prefix: Path | None = None
    snakemake_profile: Path | None = None
    slurm_profile: Path | None = None
    snakemake_cores: str = "8"
    snakemake_jobs: str = "50"

    @classmethod
    def from_env(cls, values: dict[str, str]) -> "RemoteConfig":
        def required_path(key: str) -> Path:
            require(bool(values.get(key)), f"Missing required remote config key: {key}")
            return Path(values[key])

        project_root = required_path("REMOTE_PROJECT_ROOT")
        databases = Path(values["DATABASES_DIR"]) if values.get("DATABASES_DIR") else None
        backend_weights = (
            Path(values["BACKEND_WEIGHTS_DIR"]) if values.get("BACKEND_WEIGHTS_DIR") else None
        )
        profile = _optional_path(values.get("SNAKEMAKE_PROFILE"))
        slurm = _optional_path(values.get("SLURM_PROFILE"))
        apptainer_prediction_sif = (
            Path(values["APPTAINER_PREDICTION_SIF"])
            if values.get("APPTAINER_PREDICTION_SIF")
            else None
        )
        if apptainer_prediction_sif is not None:
            require(
                apptainer_prediction_sif.is_absolute(),
                "APPTAINER_PREDICTION_SIF must be an absolute path",
            )
        apptainer_prefix = (
            Path(values["APPTAINER_PREFIX"]) if values.get("APPTAINER_PREFIX") else None
        )
        output_dir = required_path("OUTPUT_DIR")
        feature_dir = Path(values.get("FEATURE_DIR", str(output_dir / "features")))
        feature_mode = values.get("FEATURE_MODE", "localdb")
        require(
            feature_mode in SUPPORTED_FEATURE_MODES,
            f"Unsupported FEATURE_MODE {feature_mode!r}; expected one of "
            f"{sorted(SUPPORTED_FEATURE_MODES)}",
        )
        default_pattern = (
            "{record_id}.pkl.xz" if feature_mode == "mmseqs2" else DEFAULT_FEATURE_PATTERN
        )
        return cls(
            project_root=project_root,
            workflow_dir=required_path("AP_WORKFLOW_DIR"),
            conda_env_name=values.get("CONDA_ENV_NAME", "snake"),
            alphapulldown_snakemake_version=values.get("AP_SNAKEMAKE_VERSION", "2.5.0"),
            feature_config=required_path("FEATURE_CONFIG"),
            prediction_config=required_path("PREDICTION_CONFIG"),
            fasta_manifest=required_path("FASTA_MANIFEST"),
            alphapulldown_input_dir=required_path("ALPHAPULLDOWN_INPUT_DIR"),
            fasta_dir=required_path("FASTA_DIR"),
            feature_dir=feature_dir,
            output_dir=output_dir,
            log_dir=required_path("LOG_DIR"),
            tmp_dir=required_path("TMP_DIR"),
            provenance_dir=required_path("PROVENANCE_DIR"),
            databases_dir=databases,
            backend_weights_dir=backend_weights,
            feature_mode=feature_mode,
            feature_pattern=values.get("FEATURE_FILE_PATTERN", default_pattern),
            apptainer_prediction_sif=apptainer_prediction_sif,
            apptainer_prefix=apptainer_prefix,
            snakemake_profile=profile,
            slurm_profile=slurm,
            snakemake_cores=values.get("SNAKEMAKE_CORES", "8"),
            snakemake_jobs=values.get("SNAKEMAKE_JOBS", "50"),
        )


def _optional_path(value: str | None) -> Path | None:
    if value is None:
        return None
    text = str(value).strip().strip("'").strip('"').strip()
    if not text or text == ".":
        return None
    return Path(text)


def load_remote_config(path: Path) -> RemoteConfig:
    return RemoteConfig.from_env(parse_env_file(path))


def require_linux(*, allow_dry_run: bool = False) -> None:
    if platform.system() != "Linux" and not allow_dry_run:
        raise ValidationError(
            "Remote execution scripts are intended for Linux. "
            "Use dry-run/unit tests only on non-Linux systems."
        )


def read_fasta_manifest(path: Path) -> dict[str, dict[str, str]]:
    require(path.exists(), f"Missing FASTA manifest: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    return {row["record_id"]: row for row in rows}


def _accession_to_record(config: RemoteConfig) -> dict[str, str]:
    manifest = read_fasta_manifest(config.fasta_manifest)
    return {row["accession"]: record_id for record_id, row in manifest.items()}


def _record_to_fasta_path(config: RemoteConfig) -> dict[str, Path]:
    manifest = read_fasta_manifest(config.fasta_manifest)
    paths: dict[str, Path] = {}
    for record_id, row in manifest.items():
        manifest_path = Path(row.get("fasta_path", ""))
        fasta_name = manifest_path.name or f"{record_id}.fasta"
        paths[record_id] = config.fasta_dir / fasta_name
    return paths


def _fasta_spec_for_accession(config: RemoteConfig, accession: str) -> str:
    accession_to_record = _accession_to_record(config)
    require(accession in accession_to_record, f"Accession missing from FASTA manifest: {accession}")
    record_id = accession_to_record[accession]
    fasta_path = _record_to_fasta_path(config)[record_id]
    return str(fasta_path)


def _milestone2_manifest_path(input_dir: Path) -> Path:
    return input_dir.parent / "milestone2_scenarios.json"


def read_milestone2_scenarios(input_dir: Path) -> dict[str, dict[str, object]]:
    path = _milestone2_manifest_path(input_dir)
    require(path.exists(), f"Missing Milestone 2 scenario manifest: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(
        payload.get("target_universe_fallback") == "prohibited",
        "Milestone 2 benchmark must explicitly prohibit target-universe fallback",
    )
    rows = payload.get("scenarios")
    require(isinstance(rows, list), f"Milestone 2 scenarios must be a list: {path}")
    scenarios: dict[str, dict[str, object]] = {}
    for row in rows:
        require(isinstance(row, dict), f"Malformed Milestone 2 scenario row in {path}")
        scenario_id = str(row.get("scenario_id", ""))
        require(bool(scenario_id), f"Milestone 2 scenario missing scenario_id in {path}")
        require(scenario_id not in scenarios, f"Duplicate Milestone 2 scenario ID: {scenario_id}")
        scenarios[scenario_id] = row
    return scenarios


def excluded_milestone2_scenario_ids(input_dir: Path) -> set[str]:
    payload = json.loads(_milestone2_manifest_path(input_dir).read_text(encoding="utf-8"))
    excluded = payload.get("excluded_scenario_ids", [])
    require(isinstance(excluded, list), "Milestone 2 excluded_scenario_ids must be a list")
    return {str(item) for item in excluded}


def read_milestone2_sample_sheet(input_dir: Path) -> list[dict[str, str]]:
    path = input_dir / "milestone2_sample_sheet.tsv"
    require(path.exists(), f"Missing Milestone 2 sample sheet: {path}")
    scenarios = read_milestone2_scenarios(input_dir)
    excluded = excluded_milestone2_scenario_ids(input_dir)
    ready_ids = [
        scenario_id
        for scenario_id, scenario in scenarios.items()
        if scenario.get("execution_status") == "ready_from_versioned_records"
    ]
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    require(rows, f"Milestone 2 sample sheet is empty: {path}")
    require(
        {"scenario_id", "record_ids", "accessions"}.issubset(rows[0].keys()),
        f"Milestone 2 sample sheet must contain scenario_id, record_ids, accessions: {path}",
    )
    seen: list[str] = []
    for row in rows:
        scenario_id = row["scenario_id"]
        require(scenario_id not in excluded, f"Milestone 2 scenario is explicitly excluded: {scenario_id}")
        require(scenario_id in scenarios, f"Unknown Milestone 2 scenario ID: {scenario_id}")
        scenario = scenarios[scenario_id]
        status = scenario.get("execution_status")
        require(
            status == "ready_from_versioned_records",
            f"Milestone 2 scenario {scenario_id} is blocked because versioned sequence "
            f"records are absent; status={status}",
        )
        expected_records = [str(item) for item in scenario.get("target_record_ids", [])]
        actual_records = [item for item in row["record_ids"].split("+") if item]
        require(
            actual_records == expected_records,
            f"Milestone 2 scenario {scenario_id} record_ids do not match the scenario manifest",
        )
        accessions = [item for item in row["accessions"].split("+") if item]
        require(
            len(accessions) == len(actual_records),
            f"Milestone 2 scenario {scenario_id} has mismatched record/accession counts",
        )
        for accession in accessions:
            validate_accession(accession)
        seen.append(scenario_id)
    require(
        seen == ready_ids,
        "Milestone 2 sample sheet must contain exactly the ready human scenarios in manifest order",
    )
    return rows


def accessions_for_screen(screen: str, input_dir: Path) -> list[str]:
    require(screen in SUPPORTED_SCREENS, f"Unsupported screen: {screen}")
    if screen == "controls":
        path = input_dir / "control_sample_sheet.csv"
        require(path.exists(), f"Missing control sample sheet: {path}")
        accessions: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                accessions.extend(line.strip().split("+"))
        return sorted(set(accessions))
    if screen == "transport":
        paths = [input_dir / "transport_baits.txt", input_dir / "ift_b_preys.txt"]
        accessions = []
        for path in paths:
            require(path.exists(), f"Missing transport input file: {path}")
            accessions.extend(
                line.strip() for line in path.read_text().splitlines() if line.strip()
            )
        return sorted(set(accessions))
    if screen == "milestone2":
        rows = read_milestone2_sample_sheet(input_dir)
        accessions = []
        for row in rows:
            accessions.extend(row["accessions"].split("+"))
        return sorted(set(accessions))
    path = input_dir / "full_screen_pairs.tsv"
    require(path.exists(), f"Missing full-screen pairs table: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    accessions = []
    for row in rows:
        accessions.extend([row["bait_accession"], row["prey_accession"]])
    return sorted(set(accessions))


def validate_accession_files(config: RemoteConfig) -> None:
    validated_any = False
    if (config.alphapulldown_input_dir / "control_sample_sheet.csv").exists():
        validated_any = True
        for accession in accessions_for_screen("controls", config.alphapulldown_input_dir):
            validate_accession(accession)
    if (
        (config.alphapulldown_input_dir / "transport_baits.txt").exists()
        or (config.alphapulldown_input_dir / "ift_b_preys.txt").exists()
    ):
        validated_any = True
        for accession in accessions_for_screen("transport", config.alphapulldown_input_dir):
            validate_accession(accession)
    if (config.alphapulldown_input_dir / "milestone2_sample_sheet.tsv").exists():
        validated_any = True
        for accession in accessions_for_screen("milestone2", config.alphapulldown_input_dir):
            validate_accession(accession)
    require(validated_any, f"No supported AlphaPulldown input files found in {config.alphapulldown_input_dir}")


def expected_feature_paths(config: RemoteConfig, accessions: list[str]) -> dict[str, Path]:
    accession_to_record = _accession_to_record(config)
    missing_records = [
        accession for accession in accessions if accession not in accession_to_record
    ]
    require(not missing_records, f"Accessions missing from FASTA manifest: {missing_records}")
    paths = {}
    for accession in accessions:
        record_id = accession_to_record[accession]
        filename = config.feature_pattern.format(record_id=record_id, accession=accession)
        paths[accession] = config.feature_dir / filename
    return paths


def missing_features(config: RemoteConfig, screen: str) -> list[Path]:
    accessions = accessions_for_screen(screen, config.alphapulldown_input_dir)
    paths = expected_feature_paths(config, accessions)
    return [path for path in paths.values() if not path.exists()]


InspectRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def validate_configured_sif(
    config: RemoteConfig,
    *,
    inspect_runner: InspectRunner | None = None,
) -> None:
    """Validate a configured production SIF before Snakemake can start."""
    if config.apptainer_prediction_sif is None:
        return
    sif = config.apptainer_prediction_sif
    require(sif.exists(), f"Configured APPTAINER_PREDICTION_SIF does not exist: {sif}")
    require(sif.is_file(), f"Configured APPTAINER_PREDICTION_SIF is not a file: {sif}")
    require(sif.stat().st_size > 0, f"Configured APPTAINER_PREDICTION_SIF is empty: {sif}")
    runner = inspect_runner or _run_apptainer_inspect
    result = runner(["apptainer", "inspect", str(sif)])
    require(
        result.returncode == 0,
        "Configured APPTAINER_PREDICTION_SIF failed `apptainer inspect`: "
        f"{sif}\n{result.stderr.strip()}",
    )


def _run_apptainer_inspect(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True, capture_output=True)


def write_feature_input_file(config: RemoteConfig, output_dir: Path) -> Path:
    manifest = read_fasta_manifest(config.fasta_manifest)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "feature_inputs.txt"
    fasta_paths = [str(_record_to_fasta_path(config)[record_id]) for record_id in sorted(manifest)]
    path.write_text("\n".join(fasta_paths) + "\n", encoding="utf-8")
    return path


def write_prediction_input_files(
    config: RemoteConfig, *, screen: str, output_dir: Path
) -> list[Path]:
    require(screen in SUPPORTED_SCREENS, f"Unsupported screen: {screen}")
    require(screen != "full", "Full screen is definition-only until explicitly approved")
    output_dir.mkdir(parents=True, exist_ok=True)
    if screen == "controls":
        source = config.alphapulldown_input_dir / "control_sample_sheet.csv"
        require(source.exists(), f"Missing control sample sheet: {source}")
        path = output_dir / "control_sample_sheet.fasta_paths.csv"
        lines = []
        for line in source.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            fasta_specs = [
                _fasta_spec_for_accession(config, item) for item in line.strip().split("+")
            ]
            lines.append("+".join(fasta_specs))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return [path]

    if screen == "milestone2":
        rows = read_milestone2_sample_sheet(config.alphapulldown_input_dir)
        record_to_fasta = _record_to_fasta_path(config)
        path = output_dir / "milestone2_sample_sheet.fasta_paths.txt"
        lines = []
        for row in rows:
            fasta_specs = [
                str(record_to_fasta[record_id])
                for record_id in row["record_ids"].split("+")
                if record_id
            ]
            lines.append("+".join(fasta_specs))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return [path]

    bait_source = config.alphapulldown_input_dir / "transport_baits.txt"
    prey_source = config.alphapulldown_input_dir / "ift_b_preys.txt"
    require(bait_source.exists(), f"Missing transport bait file: {bait_source}")
    require(prey_source.exists(), f"Missing IFT-B prey file: {prey_source}")
    output_paths = [
        output_dir / "transport_baits.fasta_paths.txt",
        output_dir / "ift_b_preys.fasta_paths.txt",
    ]
    for source, output_path in zip([bait_source, prey_source], output_paths, strict=True):
        lines = [
            _fasta_spec_for_accession(config, line.strip())
            for line in source.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_paths


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    def emit(value: object, indent: int = 0) -> list[str]:
        prefix = " " * indent
        lines: list[str] = []
        if isinstance(value, dict):
            if not value:
                lines.append(f"{prefix}{{}}")
                return lines
            for key, item in value.items():
                if key in UPSTREAM_CLI_ARGUMENT_KEYS and isinstance(item, dict):
                    lines.append(f"{prefix}{key}: {_yaml_inline_dict(item)}")
                    continue
                if isinstance(item, (dict, list)):
                    if not item:
                        lines.append(f"{prefix}{key}: {_yaml_scalar_empty(item)}")
                    else:
                        lines.append(f"{prefix}{key}:")
                        lines.extend(emit(item, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: {_yaml_scalar(item)}")
        elif isinstance(value, list):
            if not value:
                lines.append(f"{prefix}[]")
                return lines
            for item in value:
                if isinstance(item, (dict, list)):
                    if not item:
                        lines.append(f"{prefix}- {_yaml_scalar_empty(item)}")
                    else:
                        lines.append(f"{prefix}-")
                        lines.extend(emit(item, indent + 2))
                else:
                    lines.append(f"{prefix}- {_yaml_scalar(item)}")
        else:
            lines.append(f"{prefix}{_yaml_scalar(value)}")
        return lines

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(emit(payload)) + "\n", encoding="utf-8")


def _yaml_inline_dict(value: dict[object, object]) -> str:
    if not value:
        return "{}"
    parts = []
    for key, item in value.items():
        parts.append(f"{_yaml_scalar(key)}: {_yaml_scalar(item)}")
    return "{" + ", ".join(parts) + "}"


def _yaml_scalar_empty(value: object) -> str:
    if isinstance(value, list):
        return "[]"
    if isinstance(value, dict):
        return "{}"
    return _yaml_scalar(value)


def _validate_cli_argument_map(name: str, arguments: dict[str, object]) -> None:
    for key, value in arguments.items():
        key_text = str(key)
        value_text = str(value)
        require(key_text.startswith("--"), f"{name} key must be a CLI flag: {key_text}")
        require(
            "\n" not in key_text and "\r" not in key_text,
            f"{name} key contains an embedded newline: {key_text!r}",
        )
        require(
            "\n" not in value_text and "\r" not in value_text,
            f"{name} value for {key_text} contains an embedded newline",
        )


def upstream_cli_parameters(arguments: dict[str, object]) -> str:
    """Mirror AlphaPulldownSnakemake 2.5.0's CLI argument rendering."""
    _validate_cli_argument_map("upstream CLI arguments", arguments)
    return " ".join([f"{key}={value}" for key, value in arguments.items()])


def _base_upstream_config(config: RemoteConfig, *, input_files: list[Path]) -> dict[str, object]:
    data_pipeline = "alphafold2" if config.feature_mode == "mmseqs2" else "alphafold3"
    fold_backend = "alphafold2" if config.feature_mode == "mmseqs2" else "alphafold3"
    prediction_container = (
        "docker://kosinskilab/alphafold2:2.5.0"
        if config.feature_mode == "mmseqs2"
        else "docker://kosinskilab/alphafold3:2.5.0"
    )
    if config.apptainer_prediction_sif is not None:
        prediction_container = str(config.apptainer_prediction_sif)
    payload: dict[str, object] = {
        "input_files": [str(path) for path in input_files],
        "protein_delimiter": "+",
        "exclude_permutations": True,
        "output_directory": str(config.output_dir),
        "databases_directory": str(config.databases_dir or ""),
        "backend_weights_directory": str(config.backend_weights_dir or ""),
        "feature_directory": [],
        "only_generate_features": False,
        "enable_structure_analysis": True,
        "generate_recursive_report": True,
        "recursive_report_arguments": {},
        "create_feature_arguments": {
            "--save_msa_files": False,
            "--use_precomputed_msas": True,
            "--max_template_date": "2050-01-01",
            "--compress_features": True,
            "--data_pipeline": data_pipeline,
        },
        "structure_inference_arguments": {
            "--fold_backend": fold_backend,
        },
        "analyze_structure_arguments": {
            "--contact_thresh": 8.0,
            "--pae_filter": 100.0,
            "--models_to_analyse": "all",
        },
        "mem_safety_factor": 1.25,
        "max_mem_mb": 0,
        "feature_create_ram_scaling": 1.1,
        "structure_inference_ram_scaling": 1.1,
        "max_total_length_alphafold2": 5000,
        "max_total_length_alphafold3": 7000,
        "max_protein_length": 0,
        "length_filter_fetch_uniprot": False,
        "alphafold_inference_threads": int(config.snakemake_cores),
        "slurm_partition": "",
        "slurm_qos": "",
        "structure_inference_gpus_per_task": 1,
        "structure_inference_gpu_model": "",
        "structure_inference_max_runtime": 10080,
        "structure_inference_unified_memory": True,
        "structure_inference_xla_mem_fraction": "auto",
        "prediction_container": prediction_container,
        "analysis_container": "docker://kosinskilab/alphajudge:latest",
    }
    if config.feature_mode == "mmseqs2":
        feature_args = payload["create_feature_arguments"]
        require(isinstance(feature_args, dict), "Internal error: feature args must be a dict")
        feature_args["--use_mmseqs2"] = True
        feature_args["--skip_existing"] = True
    for name in [
        "create_feature_arguments",
        "structure_inference_arguments",
        "analyze_structure_arguments",
    ]:
        arguments = payload[name]
        require(isinstance(arguments, dict), f"Internal error: {name} must be a dict")
        _validate_cli_argument_map(name, arguments)
    return payload


def write_resolved_feature_config(config: RemoteConfig, *, run_id: str) -> tuple[Path, Path]:
    run_dir = config.provenance_dir / run_id
    feature_inputs = write_feature_input_file(config, run_dir)
    payload = _base_upstream_config(config, input_files=[feature_inputs])
    payload["only_generate_features"] = True
    path = run_dir / "feature_generation.config.yaml"
    _write_yaml(path, payload)
    return path, feature_inputs


def write_resolved_prediction_config(
    config: RemoteConfig, *, screen: str, run_id: str
) -> tuple[Path, list[Path]]:
    run_dir = config.provenance_dir / run_id
    input_files = write_prediction_input_files(config, screen=screen, output_dir=run_dir)
    payload = _base_upstream_config(config, input_files=input_files)
    payload["only_generate_features"] = False
    path = run_dir / f"prediction.{screen}.config.yaml"
    _write_yaml(path, payload)
    return path, input_files


def snakemake_base_command(
    config: RemoteConfig,
    *,
    configfile: Path,
    dry_run: bool,
    profile: Path | None = None,
) -> list[str]:
    command = ["snakemake"]
    snakefile = config.workflow_dir / "workflow" / "Snakefile"
    command.extend(["--snakefile", str(snakefile)])
    command.extend(["--directory", str(config.workflow_dir), "--configfile", str(configfile)])
    command.extend(["--software-deployment-method", "apptainer"])
    if config.apptainer_prefix is not None:
        command.extend(["--apptainer-prefix", str(config.apptainer_prefix)])
    selected_profile = profile if profile is not None else config.snakemake_profile
    selected_profile_text = "" if selected_profile is None else str(selected_profile).strip()
    if selected_profile_text and selected_profile_text != ".":
        command.extend(["--profile", selected_profile_text])
    else:
        command.extend(["--cores", config.snakemake_cores])
    if dry_run:
        command.extend(["--dry-run", "--printshellcmds"])
    return command


def feature_generation_command(config: RemoteConfig, *, dry_run: bool) -> list[str]:
    return snakemake_base_command(config, configfile=config.feature_config, dry_run=dry_run)


def prediction_command(
    config: RemoteConfig,
    *,
    screen: str,
    dry_run: bool,
    executor: str = "desktop",
) -> list[str]:
    require(screen in SUPPORTED_SCREENS, f"Unsupported screen: {screen}")
    require(screen != "full", "Full screen is definition-only until explicitly approved")
    profile = config.slurm_profile if executor == "slurm" else config.snakemake_profile
    command = snakemake_base_command(
        config, configfile=config.prediction_config, dry_run=dry_run, profile=profile
    )
    if executor == "slurm":
        require(config.slurm_profile is not None, "SLURM executor requires SLURM_PROFILE")
        command.extend(["--executor", "slurm"])
        command.extend(["--jobs", config.snakemake_jobs])
    return command


def shell_join(command: list[str]) -> str:
    return " ".join(_quote(part) for part in command)


def _quote(value: str) -> str:
    if re.match(r"^[A-Za-z0-9_./:=+-]+$", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def create_run_provenance(
    *,
    config: RemoteConfig,
    run_id: str,
    command: list[str],
    input_paths: list[Path],
) -> Path:
    output_dir = config.provenance_dir / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "utc_timestamp": dt.datetime.now(dt.UTC).isoformat(),
        "git": git_metadata(config.project_root),
        "command": command,
        "command_string": shell_join(command),
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in input_paths
            if path.exists() and path.is_file()
        ],
        "config": {
            "feature_config": str(config.feature_config),
            "prediction_config": str(config.prediction_config),
            "feature_mode": config.feature_mode,
            "databases_dir": str(config.databases_dir) if config.databases_dir else "",
            "backend_weights_dir": str(config.backend_weights_dir)
            if config.backend_weights_dir
            else "",
            "apptainer_prediction_sif": str(config.apptainer_prediction_sif)
            if config.apptainer_prediction_sif
            else "",
            "apptainer_prefix": str(config.apptainer_prefix) if config.apptainer_prefix else "",
        },
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    payload["provenance_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    path = output_dir / "run_provenance.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
