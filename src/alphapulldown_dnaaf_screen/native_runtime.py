"""Docker-native RunPod execution for the isolated Milestone 2 benchmark."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from .provenance import git_metadata, sha256_file
from .remote import (
    parse_env_file,
    read_fasta_manifest,
    read_milestone2_sample_sheet,
    read_milestone2_scenarios,
    shell_join,
    stable_run_id,
)
from .validation import ValidationError, require

DOCKER_NATIVE_RUNTIME = "docker-native"
MILESTONE2_SCREEN = "milestone2"
AF2_PIPELINE = "alphafold2"
# AlphaPulldown names an AF2 feature from the normalized FASTA header
# identifier, not our internal record ID. The benchmark headers deliberately
# include the accession, so retaining this distinction is required for reuse.
NATIVE_MMS2_AF2_FEATURE_PATTERN = "{fasta_identifier}.pkl.xz"
BASE_IMAGE = "nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu20.04"
BASE_IMAGE_DIGEST = "sha256:1da6cf17f9c651323905c8cf5fd63a781a9a2fc0d28a477ca21df80a7bfaa00c"
ALPHAPULLDOWN_SOURCE_REVISION = "1c99b15ce3fef42374c24a5bd83ce8241117d5f6"
ALPHAPULLDOWN_WHEEL_SHA256 = "67a8496560fddf9c9570015bf88545e48502fad7cc12f995dc69a5999a0ad75a"
UNBUILT_IMAGE_DIGEST = "UNBUILT"
BLOCKED_SCENARIO_ID = "chlamy_dnaaf18_ift46_positive"
FORBIDDEN_EXECUTABLES = {
    "snakemake",
    "apptainer",
    "singularity",
    "docker",
    "podman",
}
APPTAINER_ENV_PREFIXES = ("APPTAINER_", "SINGULARITY_")


def _required_path(values: dict[str, str], key: str) -> Path:
    require(bool(values.get(key)), f"Missing required Docker-native config key: {key}")
    path = Path(values[key])
    require(path.is_absolute(), f"{key} must be an absolute path: {path}")
    return path


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _is_true(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class NativeRuntimeConfig:
    project_root: Path
    execution_stage: str
    container_runtime: str
    fasta_manifest: Path
    fasta_dir: Path
    input_dir: Path
    feature_dir: Path
    output_dir: Path
    log_dir: Path
    tmp_dir: Path
    provenance_dir: Path
    image_lock: Path
    feature_mode: str
    feature_pattern: str
    data_pipeline: str
    fold_backend: str
    base_image_digest: str
    derived_image_digest: str
    expected_alphapulldown_version: str
    expected_alphapulldown_revision: str
    max_template_date: str
    backend_weights_dir: Path | None = None

    @classmethod
    def from_env(cls, values: dict[str, str]) -> "NativeRuntimeConfig":
        runtime = values.get("CONTAINER_RUNTIME", "")
        require(
            runtime == DOCKER_NATIVE_RUNTIME,
            f"CONTAINER_RUNTIME must be {DOCKER_NATIVE_RUNTIME!r}, got {runtime!r}",
        )
        for key, value in values.items():
            if key.startswith(APPTAINER_ENV_PREFIXES) and value.strip():
                raise ValidationError(
                    f"{key} is incompatible with CONTAINER_RUNTIME={DOCKER_NATIVE_RUNTIME}; "
                    "RunPod Docker-native execution must not use SIF or nested runtimes"
                )

        stage = values.get("REMOTE_EXECUTION_STAGE", "")
        require(stage in {"cpu", "gpu"}, "REMOTE_EXECUTION_STAGE must be cpu or gpu")
        require(
            values.get("FEATURE_MODE") == "mmseqs2",
            "Docker-native Milestone 2 requires FEATURE_MODE=mmseqs2",
        )
        require(
            values.get("FEATURE_FILE_PATTERN", NATIVE_MMS2_AF2_FEATURE_PATTERN)
            == NATIVE_MMS2_AF2_FEATURE_PATTERN,
            "Docker-native Milestone 2 requires AlphaPulldown FASTA-identifier .pkl.xz feature files",
        )
        data_pipeline = values.get("NATIVE_DATA_PIPELINE", AF2_PIPELINE).lower()
        fold_backend = values.get("NATIVE_FOLD_BACKEND", AF2_PIPELINE).lower()
        require(
            data_pipeline == AF2_PIPELINE and fold_backend == AF2_PIPELINE,
            "Docker-native Milestone 2 supports AlphaFold2 only; AF3 selectors are prohibited",
        )
        require(
            not _is_true(values.get("NATIVE_ENABLE_ALPHAJUDGE")),
            "AlphaJudge analysis is not supported by the Docker-native Milestone 2 runtime",
        )

        weights = (
            Path(values["BACKEND_WEIGHTS_DIR"])
            if values.get("BACKEND_WEIGHTS_DIR")
            else None
        )
        if weights is not None:
            require(weights.is_absolute(), "BACKEND_WEIGHTS_DIR must be absolute when set")

        config = cls(
            project_root=_required_path(values, "REMOTE_PROJECT_ROOT"),
            execution_stage=stage,
            container_runtime=runtime,
            fasta_manifest=_required_path(values, "FASTA_MANIFEST"),
            fasta_dir=_required_path(values, "FASTA_DIR"),
            input_dir=_required_path(values, "ALPHAPULLDOWN_INPUT_DIR"),
            feature_dir=_required_path(values, "FEATURE_DIR"),
            output_dir=_required_path(values, "OUTPUT_DIR"),
            log_dir=_required_path(values, "LOG_DIR"),
            tmp_dir=_required_path(values, "TMP_DIR"),
            provenance_dir=_required_path(values, "PROVENANCE_DIR"),
            image_lock=_required_path(values, "NATIVE_IMAGE_LOCK"),
            feature_mode="mmseqs2",
            feature_pattern=NATIVE_MMS2_AF2_FEATURE_PATTERN,
            data_pipeline=data_pipeline,
            fold_backend=fold_backend,
            base_image_digest=values.get("ALPHAPULLDOWN_BASE_IMAGE_DIGEST", ""),
            derived_image_digest=values.get(
                "ALPHAPULLDOWN_DERIVED_IMAGE_DIGEST", UNBUILT_IMAGE_DIGEST
            ),
            expected_alphapulldown_version=values.get(
                "ALPHAPULLDOWN_EXPECTED_VERSION", "2.5.0"
            ),
            expected_alphapulldown_revision=values.get(
                "ALPHAPULLDOWN_EXPECTED_REVISION", ""
            ),
            max_template_date=values.get("MAX_TEMPLATE_DATE", "2050-01-01"),
            backend_weights_dir=weights,
        )
        validate_milestone2_isolation(config)
        validate_image_lock(config)
        return config


def load_native_config(path: Path) -> NativeRuntimeConfig:
    return NativeRuntimeConfig.from_env(parse_env_file(path))


def validate_milestone2_isolation(config: NativeRuntimeConfig) -> None:
    root = _resolved(config.project_root)
    expected_manifest = root / "data/processed/benchmarks/fasta/fasta_manifest.tsv"
    target_universe_manifest = root / "data/processed/fasta/fasta_manifest.tsv"
    expected_input_dir = root / "data/processed/benchmarks/alphapulldown_inputs"
    expected_scenarios = root / "data/processed/benchmarks/milestone2_scenarios.json"

    require(
        _resolved(config.fasta_manifest) == expected_manifest,
        "Docker-native Milestone 2 must use the independent benchmark FASTA manifest",
    )
    require(
        _resolved(config.fasta_manifest) != target_universe_manifest,
        "The 62-target FASTA manifest is prohibited for Milestone 2",
    )
    require(
        _resolved(config.input_dir) == expected_input_dir,
        "Docker-native Milestone 2 must use benchmark-only AlphaPulldown inputs",
    )
    require(
        _resolved(config.input_dir.parent / "milestone2_scenarios.json")
        == expected_scenarios,
        "Docker-native Milestone 2 must read only milestone2_scenarios.json",
    )

    distinct_paths = {
        _resolved(config.feature_dir),
        _resolved(config.output_dir),
        _resolved(config.log_dir),
        _resolved(config.tmp_dir),
        _resolved(config.provenance_dir),
    }
    require(len(distinct_paths) == 5, "Milestone 2 runtime paths must be distinct")
    for path in distinct_paths:
        require(
            "milestone2_benchmark" in path.parts,
            f"Milestone 2 runtime path is outside its isolated namespace: {path}",
        )

    scenarios = read_milestone2_scenarios(config.input_dir)
    require(
        BLOCKED_SCENARIO_ID in scenarios,
        f"Missing blocked scenario declaration: {BLOCKED_SCENARIO_ID}",
    )
    blocked = scenarios[BLOCKED_SCENARIO_ID]
    require(
        blocked.get("execution_status") != "ready_from_versioned_records",
        "Blocked Chlamydomonas scenario must not be runnable",
    )
    read_milestone2_sample_sheet(config.input_dir)


def validate_image_lock(config: NativeRuntimeConfig) -> dict[str, object]:
    require(config.image_lock.is_file(), f"Missing native image lock: {config.image_lock}")
    payload = json.loads(config.image_lock.read_text(encoding="utf-8"))
    require(payload.get("base_image") == BASE_IMAGE, "Native image lock has wrong base image")
    require(
        payload.get("base_image_digest") == BASE_IMAGE_DIGEST,
        "Native image lock has wrong immutable base image digest",
    )
    require(
        config.base_image_digest == BASE_IMAGE_DIGEST,
        "ALPHAPULLDOWN_BASE_IMAGE_DIGEST does not match the pinned image lock",
    )
    require(
        payload.get("alphapulldown_wheel_sha256") == ALPHAPULLDOWN_WHEEL_SHA256,
        "Native image lock has wrong AlphaPulldown wheel checksum",
    )
    require(
        payload.get("expected_alphapulldown_revision") == ALPHAPULLDOWN_SOURCE_REVISION,
        "Native image lock has wrong AlphaPulldown source revision",
    )
    return payload


def _manifest_rows(config: NativeRuntimeConfig) -> dict[str, dict[str, str]]:
    rows = read_fasta_manifest(config.fasta_manifest)
    sample_rows = read_milestone2_sample_sheet(config.input_dir)
    required_ids = {
        record_id
        for row in sample_rows
        for record_id in row["record_ids"].split("+")
        if record_id
    }
    require(
        set(rows) == required_ids,
        "Benchmark FASTA manifest must contain exactly the runnable Milestone 2 records",
    )
    return rows


def _fasta_paths(config: NativeRuntimeConfig) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for record_id, row in _manifest_rows(config).items():
        manifest_path = Path(row.get("fasta_path", ""))
        fasta_name = manifest_path.name or f"{record_id}.fasta"
        path = config.fasta_dir / fasta_name
        require(path.is_file(), f"Missing versioned benchmark FASTA: {path}")
        paths[record_id] = path
    return paths


def _feature_path(
    config: NativeRuntimeConfig, *, record_id: str, fasta_path: Path
) -> Path:
    """Return the exact AlphaPulldown AF2 feature path for one benchmark FASTA."""

    identifier = _alphapulldown_fasta_identifier(fasta_path)

    return config.feature_dir / config.feature_pattern.format(
        record_id=record_id,
        fasta_identifier=identifier,
    )


def _alphapulldown_fasta_identifier(fasta_path: Path) -> str:
    """Mirror the normalized identifier observed in AlphaPulldown AF2 outputs."""

    for line in fasta_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(">"):
            identifier = line[1:].split(maxsplit=1)[0]
            normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", identifier).strip("_")
            require(bool(normalized), f"FASTA header has no usable identifier: {fasta_path}")
            return normalized
    raise ValidationError(f"Missing FASTA header: {fasta_path}")


def feature_commands(config: NativeRuntimeConfig) -> list[list[str]]:
    validate_stage(config, command="features")
    commands: list[list[str]] = []
    for record_id, fasta_path in sorted(_fasta_paths(config).items()):
        command = [
            "create_individual_features.py",
            f"--fasta_paths={fasta_path}",
            "--data_dir=",
            f"--output_dir={config.feature_dir}",
            "--save_msa_files=False",
            "--use_precomputed_msas=True",
            f"--max_template_date={config.max_template_date}",
            "--compress_features=True",
            "--data_pipeline=alphafold2",
            "--use_mmseqs2=True",
            "--skip_existing=True",
        ]
        _validate_native_command(command)
        expected = _feature_path(
            config, record_id=record_id, fasta_path=fasta_path
        )
        require(
            expected.suffixes[-2:] == [".pkl", ".xz"],
            f"Unexpected feature target for {record_id}: {expected}",
        )
        commands.append(command)
    return commands


def prediction_commands(
    config: NativeRuntimeConfig, *, scenario_id: str | None = None
) -> list[list[str]]:
    validate_stage(config, command="predict")
    require(
        config.backend_weights_dir is not None,
        "Prediction requires BACKEND_WEIGHTS_DIR to name the AlphaFold2 model-weights directory",
    )
    require(
        config.backend_weights_dir.is_dir(),
        f"Prediction model-weights directory does not exist: {config.backend_weights_dir}",
    )
    fasta_paths = _fasta_paths(config)
    commands: list[list[str]] = []
    if scenario_id == BLOCKED_SCENARIO_ID:
        raise ValidationError(
            f"{BLOCKED_SCENARIO_ID} is blocked because versioned sequence records are absent"
        )
    rows = read_milestone2_sample_sheet(config.input_dir)
    if scenario_id is not None:
        rows = [row for row in rows if row["scenario_id"] == scenario_id]
        require(bool(rows), f"Unknown or non-runnable Milestone 2 scenario: {scenario_id}")

    for row in rows:
        selected_scenario_id = row["scenario_id"]
        require(
            selected_scenario_id != BLOCKED_SCENARIO_ID,
            f"{BLOCKED_SCENARIO_ID} is blocked because versioned sequence records are absent",
        )
        record_ids = [item for item in row["record_ids"].split("+") if item]
        for record_id in record_ids:
            require(
                record_id in fasta_paths,
                f"Scenario record is absent from manifest: {record_id}",
            )
            feature_path = _feature_path(
                config, record_id=record_id, fasta_path=fasta_paths[record_id]
            )
            require(feature_path.is_file(), f"Missing required AF2 feature file: {feature_path}")
        feature_identifiers = [
            _alphapulldown_fasta_identifier(fasta_paths[record_id])
            for record_id in record_ids
        ]
        output_path = config.output_dir / "predictions" / selected_scenario_id
        command = [
            "run_structure_prediction.py",
            f"--input={'+'.join(feature_identifiers)}",
            f"--output_directory={output_path}",
            "--protein_delimiter=+",
            f"--data_directory={config.backend_weights_dir}",
            f"--features_directory={config.feature_dir}",
            "--fold_backend=alphafold2",
            # The MMseqs2 feature metadata contains fields unsupported by the
            # optional ModelCIF converter; PDB and confidence outputs remain.
            "--convert_to_modelcif=False",
        ]
        _validate_native_command(command)
        commands.append(command)
    return commands


def _validate_native_command(command: Sequence[str]) -> None:
    require(bool(command), "Native command is empty")
    executable = Path(command[0]).name
    require(
        executable not in FORBIDDEN_EXECUTABLES,
        f"Nested/container orchestrator command is prohibited: {executable}",
    )
    require(
        executable in {"create_individual_features.py", "run_structure_prediction.py"},
        f"Unsupported Docker-native executable: {executable}",
    )
    rendered = "\n".join(command).lower()
    require("alphafold3" not in rendered and "_af3_input.json" not in rendered, "AF3 is prohibited")
    require("alphajudge" not in rendered, "AlphaJudge is prohibited in the native runtime")


def validate_stage(config: NativeRuntimeConfig, *, command: str) -> None:
    require(command in {"features", "predict"}, f"Unsupported native stage command: {command}")
    required_stage = "cpu" if command == "features" else "gpu"
    require(
        config.execution_stage == required_stage,
        f"{command} requires REMOTE_EXECUTION_STAGE={required_stage}",
    )


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def validate_host_runtime(
    config: NativeRuntimeConfig,
    *,
    command: str,
    dry_run: bool,
    which: Callable[[str], str | None] = shutil.which,
    runner: CommandRunner | None = None,
) -> None:
    validate_stage(config, command=command)
    if not dry_run:
        require(platform.system() == "Linux", "Docker-native execution requires Linux")
        executable = (
            "create_individual_features.py"
            if command == "features"
            else "run_structure_prediction.py"
        )
        require(which(executable) is not None, f"Missing AlphaPulldown command: {executable}")
        require(
            config.derived_image_digest not in {"", UNBUILT_IMAGE_DIGEST},
            "A real derived image digest is required before scientific execution",
        )
        lock = validate_image_lock(config)
        require(
            lock.get("derived_image_digest") == config.derived_image_digest,
            "Derived image digest must be promoted into image-lock.json before execution",
        )
        require(
            bool(config.expected_alphapulldown_revision),
            "ALPHAPULLDOWN_EXPECTED_REVISION must be pinned before scientific execution",
        )
    if command == "predict" and not dry_run:
        require(which("nvidia-smi") is not None, "GPU prediction requires nvidia-smi")
        run = runner or _run_capture
        result = run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader",
            ]
        )
        require(result.returncode == 0, f"NVIDIA GPU preflight failed: {result.stderr.strip()}")


def _run_capture(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True, capture_output=True)


def runtime_identity(
    config: NativeRuntimeConfig,
    *,
    package_version: str | None = None,
    source_revision: str | None = None,
) -> dict[str, str]:
    if package_version is None:
        try:
            package_version = importlib.metadata.version("alphapulldown")
        except importlib.metadata.PackageNotFoundError:
            package_version = "not-installed"
    if source_revision is None:
        source_revision = os.environ.get("ALPHAPULLDOWN_SOURCE_REVISION", "unknown")
    return {
        "base_image": BASE_IMAGE,
        "base_image_digest": config.base_image_digest,
        "derived_image_digest": config.derived_image_digest,
        "alphapulldown_version": package_version,
        "alphapulldown_revision": source_revision,
    }


def validate_runtime_identity(
    config: NativeRuntimeConfig,
    identity: dict[str, str],
    *,
    allow_uninstalled: bool = False,
) -> None:
    require(
        identity["base_image_digest"] == BASE_IMAGE_DIGEST,
        "Runtime base image digest does not match the pinned build",
    )
    require(
        allow_uninstalled or identity["alphapulldown_version"] != "not-installed",
        "AlphaPulldown package metadata is unavailable in the scientific runtime",
    )
    if identity["alphapulldown_version"] != "not-installed":
        require(
            identity["alphapulldown_version"] == config.expected_alphapulldown_version,
            "Installed AlphaPulldown version does not match ALPHAPULLDOWN_EXPECTED_VERSION",
        )
    if config.expected_alphapulldown_revision:
        require(
            identity["alphapulldown_revision"] != "unknown",
            "Installed AlphaPulldown source revision is unavailable",
        )
        require(
            identity["alphapulldown_revision"] == config.expected_alphapulldown_revision,
            "Installed AlphaPulldown revision does not match ALPHAPULLDOWN_EXPECTED_REVISION",
        )


def _plan_input_paths(config: NativeRuntimeConfig, *, command: str) -> list[Path]:
    paths = [
        config.image_lock,
        config.fasta_manifest,
        config.input_dir.parent / "milestone2_scenarios.json",
        config.input_dir / "milestone2_sample_sheet.tsv",
    ]
    if command == "features":
        paths.extend(_fasta_paths(config).values())
    else:
        for record_id, fasta_path in sorted(_fasta_paths(config).items()):
            paths.append(
                _feature_path(config, record_id=record_id, fasta_path=fasta_path)
            )
    return paths


def write_native_provenance(
    config: NativeRuntimeConfig,
    *,
    run_id: str,
    stage_command: str,
    commands: list[list[str]],
    dry_run: bool,
    status: str,
    identity: dict[str, str],
) -> Path:
    run_dir = config.provenance_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    input_paths = _plan_input_paths(config, command=stage_command)
    for path in input_paths:
        require(path.is_file(), f"Provenance input is missing: {path}")
    payload: dict[str, object] = {
        "run_id": run_id,
        "utc_timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": status,
        "dry_run": dry_run,
        "stage_command": stage_command,
        "container_runtime": config.container_runtime,
        "execution_stage": config.execution_stage,
        "screen": MILESTONE2_SCREEN,
        "git": git_metadata(config.project_root),
        "runtime": identity,
        "commands": commands,
        "command_strings": [shell_join(command) for command in commands],
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)} for path in input_paths
        ],
        "paths": {
            "fasta_manifest": str(config.fasta_manifest),
            "input_dir": str(config.input_dir),
            "feature_dir": str(config.feature_dir),
            "output_dir": str(config.output_dir),
            "log_dir": str(config.log_dir),
            "tmp_dir": str(config.tmp_dir),
            "provenance_dir": str(config.provenance_dir),
        },
        "feature_semantics": {
            "data_pipeline": config.data_pipeline,
            "fold_backend": config.fold_backend,
            "feature_mode": config.feature_mode,
            "feature_pattern": config.feature_pattern,
            "alphajudge_enabled": False,
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["provenance_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    path = run_dir / "native_run_provenance.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def execute_commands(
    commands: list[list[str]],
    *,
    runner: Callable[..., subprocess.CompletedProcess[object]] = subprocess.run,
) -> None:
    for command in commands:
        _validate_native_command(command)
        runner(command, check=True)


def plan_native_run(
    config: NativeRuntimeConfig, *, command: str, scenario_id: str | None = None
) -> tuple[str, list[list[str]]]:
    require(
        command == "predict" or scenario_id is None,
        "--scenario is supported only for prediction",
    )
    screen = f"milestone2-{command}" + (f"-{scenario_id}" if scenario_id else "")
    run_id = stable_run_id("native", screen=screen)
    commands = (
        feature_commands(config)
        if command == "features"
        else prediction_commands(config, scenario_id=scenario_id)
    )
    return run_id, commands
