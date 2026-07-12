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

from .provenance import git_metadata, sha256_file
from .validation import ValidationError, require, validate_accession

SUPPORTED_SCREENS = {"controls", "transport", "full"}
DEFAULT_FEATURE_PATTERN = "{record_id}.pkl"


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
    feature_mode: str
    feature_pattern: str = DEFAULT_FEATURE_PATTERN
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
        profile = Path(values["SNAKEMAKE_PROFILE"]) if values.get("SNAKEMAKE_PROFILE") else None
        slurm = Path(values["SLURM_PROFILE"]) if values.get("SLURM_PROFILE") else None
        return cls(
            project_root=project_root,
            workflow_dir=required_path("AP_WORKFLOW_DIR"),
            conda_env_name=values.get("CONDA_ENV_NAME", "alphapulldown"),
            alphapulldown_snakemake_version=values.get("AP_SNAKEMAKE_VERSION", "2.5.0"),
            feature_config=required_path("FEATURE_CONFIG"),
            prediction_config=required_path("PREDICTION_CONFIG"),
            fasta_manifest=required_path("FASTA_MANIFEST"),
            alphapulldown_input_dir=required_path("ALPHAPULLDOWN_INPUT_DIR"),
            fasta_dir=required_path("FASTA_DIR"),
            feature_dir=required_path("FEATURE_DIR"),
            output_dir=required_path("OUTPUT_DIR"),
            log_dir=required_path("LOG_DIR"),
            tmp_dir=required_path("TMP_DIR"),
            provenance_dir=required_path("PROVENANCE_DIR"),
            databases_dir=databases,
            feature_mode=values.get("FEATURE_MODE", "localdb"),
            feature_pattern=values.get("FEATURE_FILE_PATTERN", DEFAULT_FEATURE_PATTERN),
            snakemake_profile=profile,
            slurm_profile=slurm,
            snakemake_cores=values.get("SNAKEMAKE_CORES", "8"),
            snakemake_jobs=values.get("SNAKEMAKE_JOBS", "50"),
        )


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
    path = input_dir / "full_screen_pairs.tsv"
    require(path.exists(), f"Missing full-screen pairs table: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    accessions = []
    for row in rows:
        accessions.extend([row["bait_accession"], row["prey_accession"]])
    return sorted(set(accessions))


def validate_accession_files(config: RemoteConfig) -> None:
    for accession in accessions_for_screen("controls", config.alphapulldown_input_dir):
        validate_accession(accession)
    for accession in accessions_for_screen("transport", config.alphapulldown_input_dir):
        validate_accession(accession)


def expected_feature_paths(config: RemoteConfig, accessions: list[str]) -> dict[str, Path]:
    manifest = read_fasta_manifest(config.fasta_manifest)
    accession_to_record = {row["accession"]: record_id for record_id, row in manifest.items()}
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


def snakemake_base_command(config: RemoteConfig, *, configfile: Path, dry_run: bool) -> list[str]:
    command = ["snakemake"]
    snakefile = config.workflow_dir / "workflow" / "Snakefile"
    if snakefile.exists():
        command.extend(["--snakefile", str(snakefile)])
    command.extend(["--directory", str(config.project_root), "--configfile", str(configfile)])
    if config.snakemake_profile:
        command.extend(["--profile", str(config.snakemake_profile)])
    else:
        command.extend(["--cores", config.snakemake_cores])
    if dry_run:
        command.extend(["--dry-run", "--printshellcmds"])
    return command


def feature_generation_command(config: RemoteConfig, *, dry_run: bool) -> list[str]:
    command = snakemake_base_command(config, configfile=config.feature_config, dry_run=dry_run)
    command.extend(
        [
            "--config",
            f"feature_mode={config.feature_mode}",
            f"feature_dir={config.feature_dir}",
            f"fasta_dir={config.fasta_dir}",
        ]
    )
    if config.databases_dir:
        command.extend(["databases_directory=" + str(config.databases_dir)])
    return command


def prediction_command(
    config: RemoteConfig,
    *,
    screen: str,
    dry_run: bool,
    executor: str = "desktop",
) -> list[str]:
    require(screen in SUPPORTED_SCREENS, f"Unsupported screen: {screen}")
    require(screen != "full", "Full screen is definition-only until explicitly approved")
    command = snakemake_base_command(config, configfile=config.prediction_config, dry_run=dry_run)
    if executor == "slurm":
        require(config.slurm_profile is not None, "SLURM executor requires SLURM_PROFILE")
        command.extend(["--executor", "slurm", "--profile", str(config.slurm_profile)])
        command.extend(["--jobs", config.snakemake_jobs])
    command.extend(
        [
            "--config",
            f"screen={screen}",
            f"feature_dir={config.feature_dir}",
            f"output_dir={config.output_dir}",
        ]
    )
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
        },
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    payload["provenance_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    path = output_dir / "run_provenance.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
