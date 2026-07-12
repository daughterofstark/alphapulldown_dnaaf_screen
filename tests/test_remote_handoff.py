from __future__ import annotations

import json
import platform
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from alphapulldown_dnaaf_screen.remote import (
    create_run_provenance,
    feature_generation_command,
    load_remote_config,
    missing_features,
    parse_env_file,
    prediction_command,
    require_linux,
    stable_run_id,
)
from alphapulldown_dnaaf_screen.validation import ValidationError


def write_fixture(root: Path) -> Path:
    processed = root / "data" / "processed"
    ap = processed / "alphapulldown"
    fasta = processed / "fasta"
    config = root / "config" / "remote"
    results = root / "results"
    setup_dirs = [
        ap,
        fasta,
        config,
        results / "features",
        results / "predictions",
        results / "logs",
    ]
    for path in setup_dirs:
        path.mkdir(parents=True, exist_ok=True)

    (ap / "control_sample_sheet.csv").write_text("Q5TEA3+Q96LB3\nQ8N136+Q9NQC8\n")
    (ap / "transport_baits.txt").write_text("Q5TEA3\nQ8N136\n")
    (ap / "ift_b_preys.txt").write_text("Q96LB3\nQ8WYA0\nQ86WT1\nQ8N4P2\n")
    (ap / "full_screen_pairs.tsv").write_text(
        "bait_accession\tprey_accession\nQ5TEA3\tQ96LB3\nQ5TEA3\tQ86WT1\n"
    )
    (fasta / "fasta_manifest.tsv").write_text(
        "record_id\taccession\n"
        "HUMAN_DNAAF9\tQ5TEA3\n"
        "HUMAN_DNAAF18\tQ8N136\n"
        "HUMAN_IFT74\tQ96LB3\n"
        "HUMAN_IFT81\tQ8WYA0\n"
        "HUMAN_IFT46\tQ9NQC8\n"
        "HUMAN_IFT70A\tQ86WT1\n"
        "HUMAN_IFT70B\tQ8N4P2\n"
    )
    (config / "feature_generation.example.yaml").write_text("stage: feature_generation\n")
    (config / "prediction.example.yaml").write_text("stage: prediction\n")
    env = config / "paths.env"
    env.write_text(
        "\n".join(
            [
                f"REMOTE_PROJECT_ROOT={root}",
                "AP_WORKFLOW_DIR=${REMOTE_PROJECT_ROOT}/workflow",
                "CONDA_ENV_NAME=alphapulldown",
                "AP_SNAKEMAKE_VERSION=2.5.0",
                "FEATURE_CONFIG=${REMOTE_PROJECT_ROOT}/config/remote/"
                "feature_generation.example.yaml",
                "PREDICTION_CONFIG=${REMOTE_PROJECT_ROOT}/config/remote/prediction.example.yaml",
                "FASTA_MANIFEST=${REMOTE_PROJECT_ROOT}/data/processed/fasta/fasta_manifest.tsv",
                "ALPHAPULLDOWN_INPUT_DIR=${REMOTE_PROJECT_ROOT}/data/processed/alphapulldown",
                "FASTA_DIR=${REMOTE_PROJECT_ROOT}/data/processed/fasta",
                "FEATURE_DIR=${REMOTE_PROJECT_ROOT}/results/features",
                "OUTPUT_DIR=${REMOTE_PROJECT_ROOT}/results/predictions",
                "LOG_DIR=${REMOTE_PROJECT_ROOT}/results/logs",
                "TMP_DIR=${REMOTE_PROJECT_ROOT}/results/tmp",
                "PROVENANCE_DIR=${REMOTE_PROJECT_ROOT}/results/provenance",
                "DATABASES_DIR=${REMOTE_PROJECT_ROOT}/databases",
                "FEATURE_MODE=localdb",
                "FEATURE_FILE_PATTERN={record_id}.pkl",
                "SNAKEMAKE_CORES=4",
                "",
            ]
        )
    )
    return env


class RemoteHandoffTests(unittest.TestCase):
    def test_config_parsing_expands_previous_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = write_fixture(Path(tmp))
            values = parse_env_file(env)
            self.assertEqual(values["FEATURE_DIR"], f"{tmp}/results/features")

    def test_missing_path_failure_for_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = write_fixture(Path(tmp))
            text = env.read_text().replace("REMOTE_PROJECT_ROOT=", "#REMOTE_PROJECT_ROOT=")
            env.write_text(text)
            with self.assertRaises(ValidationError):
                load_remote_config(env)

    def test_stable_run_ids(self) -> None:
        self.assertEqual(
            stable_run_id("prediction", screen="controls", timestamp="20260713T000000Z"),
            "prediction-controls-20260713T000000Z",
        )

    def test_command_construction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_remote_config(write_fixture(Path(tmp)))
            command = feature_generation_command(config, dry_run=True)
            self.assertIn("snakemake", command[0])
            self.assertIn("--dry-run", command)
            self.assertIn(f"feature_dir={tmp}/results/features", command)

    def test_feature_coverage_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = load_remote_config(write_fixture(root))
            missing = missing_features(config, "controls")
            self.assertEqual(len(missing), 4)
            for record_id in ["HUMAN_DNAAF9", "HUMAN_DNAAF18", "HUMAN_IFT74", "HUMAN_IFT46"]:
                (root / "results" / "features" / f"{record_id}.pkl").write_text("feature")
            self.assertEqual(missing_features(config, "controls"), [])

    def test_prediction_command_requires_no_full_screen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_remote_config(write_fixture(Path(tmp)))
            with self.assertRaises(ValidationError):
                prediction_command(config, screen="full", dry_run=True)

    def test_prediction_command_for_controls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_remote_config(write_fixture(Path(tmp)))
            command = prediction_command(config, screen="controls", dry_run=True)
            self.assertIn("screen=controls", command)
            self.assertIn("--dry-run", command)

    def test_no_local_execution_on_macos(self) -> None:
        with mock.patch.object(platform, "system", return_value="Darwin"):
            with self.assertRaises(ValidationError):
                require_linux()
            require_linux(allow_dry_run=True)

    def test_provenance_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = load_remote_config(write_fixture(root))
            path = create_run_provenance(
                config=config,
                run_id="test-run",
                command=["snakemake", "--dry-run"],
                input_paths=[config.fasta_manifest],
            )
            payload = json.loads(path.read_text())
            self.assertEqual(payload["run_id"], "test-run")
            self.assertEqual(payload["command"], ["snakemake", "--dry-run"])

    def test_no_hardcoded_cluster_paths(self) -> None:
        root = Path.cwd()
        checked = [
            *Path("scripts/remote").glob("*.sh"),
            *Path("config/remote").glob("*"),
            *Path("docs/software").glob("*GUIDE.md"),
        ]
        forbidden = ["/Users/", "/well/", "/ceph/", "/scratch/", "medhasharma"]
        for path in checked:
            text = (root / path).read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, f"{path} contains hardcoded path token {token}")


if __name__ == "__main__":
    unittest.main()
