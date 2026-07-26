from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from alphapulldown_dnaaf_screen.remote import (
    accessions_for_screen,
    load_remote_config,
    missing_features,
    prediction_command,
    write_resolved_feature_config,
    write_resolved_prediction_config,
)
from alphapulldown_dnaaf_screen.validation import ValidationError

SCENARIO_MANIFEST = Path("data/processed/benchmarks/milestone2_scenarios.json")
BENCHMARK_CONFIG = Path("config/benchmarks/milestone2_benchmark.example.yaml")
BENCHMARK_REMOTE_ENV = Path("config/benchmarks/milestone2_remote.example.env")
BENCHMARK_FASTA_MANIFEST = Path("data/processed/benchmarks/fasta/fasta_manifest.tsv")
BENCHMARK_AP_INPUTS = Path("data/processed/benchmarks/alphapulldown_inputs")
BENCHMARK_SAMPLE_SHEET = BENCHMARK_AP_INPUTS / "milestone2_sample_sheet.tsv"
GIRISH_PANEL = Path("data/processed/screens/girish_refined_first_run_panel.json")
FIRST_PASS_PANEL = Path("data/processed/screens/first_pass_interaction_panel.json")
FASTA_DIR = Path("data/processed/fasta")

EXPECTED_SCENARIO_IDS = [
    "chlamy_dnaaf18_ift46_positive",
    "human_dnaaf18_ift46_negative",
    "human_dnaaf9_ift74_ift81_known",
    "human_dnaaf9_ift46_ift74_ift81_exploratory",
    "human_dnaaf9_ift80_ift172_exploratory",
    "human_dnai1_ift46_ift74_ift81_exploratory",
    "human_dnai2_ift46_ift74_ift81_exploratory",
    "human_dnai1_dnai2_ift46_ift74_ift81_exploratory",
    "human_dnai1_dnai2_ift80_ift172_exploratory",
]

EXCLUDED_SCENARIO_IDS = {
    "human_dnaaf9_ift74",
    "human_dnaaf9_ift81",
    "ift74_ift81",
    "human_dnaaf18_ift46_ift74_ift81",
}

RUNNABLE_SCENARIO_IDS = EXPECTED_SCENARIO_IDS[1:]

EXPECTED_BENCHMARK_RECORDS = {
    "HUMAN_DNAAF18",
    "HUMAN_IFT46",
    "HUMAN_DNAAF9",
    "HUMAN_IFT74",
    "HUMAN_IFT81",
    "HUMAN_IFT80",
    "HUMAN_IFT172",
    "HUMAN_DNAI1",
    "HUMAN_DNAI2",
}

EXPECTED_BENCHMARK_ACCESSIONS = {
    "Q8N136",
    "Q9NQC8",
    "Q5TEA3",
    "Q96LB3",
    "Q8WYA0",
    "Q9P2H3",
    "Q9UG01",
    "Q9UI46",
    "Q9GZS0",
}

FORBIDDEN_MANIFEST_TOKENS = {
    "data/processed/targets/validated_targets.json",
    "data/processed/targets/validated_targets.tsv",
    "data/processed/uniprot/targets_uniprot_verified.json",
    "data/processed/uniprot/targets_uniprot_verified.tsv",
    "validated_targets",
    "targets_uniprot_verified",
}


class Milestone2BenchmarkTests(unittest.TestCase):
    def load_manifest(self) -> dict[str, object]:
        return json.loads(SCENARIO_MANIFEST.read_text(encoding="utf-8"))

    def scenarios(self) -> list[dict[str, object]]:
        manifest = self.load_manifest()
        scenarios = manifest["scenarios"]
        self.assertIsInstance(scenarios, list)
        return scenarios

    def test_exactly_expected_nine_scenario_ids_are_emitted(self) -> None:
        scenario_ids = [str(row["scenario_id"]) for row in self.scenarios()]
        self.assertEqual(scenario_ids, EXPECTED_SCENARIO_IDS)
        self.assertEqual(len(scenario_ids), 9)

    def test_excluded_scenario_ids_are_absent_and_recorded_as_prohibited(self) -> None:
        manifest = self.load_manifest()
        scenario_ids = {str(row["scenario_id"]) for row in self.scenarios()}
        self.assertTrue(EXCLUDED_SCENARIO_IDS.isdisjoint(scenario_ids))
        self.assertEqual(set(manifest["excluded_scenario_ids"]), EXCLUDED_SCENARIO_IDS)

    def test_all_target_record_ids_are_existing_internal_fasta_records(self) -> None:
        for row in self.scenarios():
            for record_id in row["target_record_ids"]:
                fasta = FASTA_DIR / f"{record_id}.fasta"
                self.assertTrue(fasta.exists(), f"Missing existing internal FASTA record {record_id}")

    def test_source_panel_record_ids_are_existing_internal_records(self) -> None:
        girish_ids = {row["set_id"] for row in json.loads(GIRISH_PANEL.read_text(encoding="utf-8"))}
        first_pass_ids = {
            row["pair_id"] for row in json.loads(FIRST_PASS_PANEL.read_text(encoding="utf-8"))
        }
        allowed_source_ids = girish_ids | first_pass_ids
        for row in self.scenarios():
            for record_id in row["source_panel_record_ids"]:
                self.assertIn(record_id, allowed_source_ids)

    def test_chlamydomonas_scenario_has_no_target_fallback(self) -> None:
        row = next(
            row
            for row in self.scenarios()
            if row["scenario_id"] == "chlamy_dnaaf18_ift46_positive"
        )
        self.assertEqual(row["target_record_ids"], [])
        self.assertEqual(
            row["execution_status"],
            "blocked_until_external_sequence_records_are_versioned",
        )
        self.assertIn("GR_SET_001", row["source_panel_record_ids"])
        self.assertIn("EXT_CR_ODA16__CR_IFT46", row["source_panel_record_ids"])

    def test_benchmark_has_own_input_config_output_and_provenance_paths(self) -> None:
        text = BENCHMARK_CONFIG.read_text(encoding="utf-8")
        expected_paths = {
            "data/processed/benchmarks/milestone2_scenarios.json",
            "data/processed/benchmarks/alphapulldown_inputs",
            "config/benchmarks/resolved/milestone2",
            "results/milestone2_benchmark",
            "results/milestone2_benchmark/logs",
            "results/provenance/milestone2_benchmark",
        }
        for path in expected_paths:
            self.assertIn(path, text)

    def test_no_benchmark_path_points_to_the_62_target_manifest(self) -> None:
        benchmark_text = "\n".join(
            [
                SCENARIO_MANIFEST.read_text(encoding="utf-8"),
                BENCHMARK_CONFIG.read_text(encoding="utf-8"),
            ]
        )
        for token in FORBIDDEN_MANIFEST_TOKENS:
            self.assertNotIn(token, benchmark_text)

    def test_benchmark_manifest_cannot_fall_back_to_target_universe(self) -> None:
        manifest = self.load_manifest()
        self.assertEqual(manifest["target_universe_fallback"], "prohibited")
        config_text = BENCHMARK_CONFIG.read_text(encoding="utf-8")
        self.assertRegex(config_text, re.compile(r'target_universe_fallback:\s+"prohibited"'))

    def test_benchmark_sample_sheet_emits_exactly_eight_runnable_human_scenarios(self) -> None:
        rows = read_tsv(BENCHMARK_SAMPLE_SHEET)
        self.assertEqual([row["scenario_id"] for row in rows], RUNNABLE_SCENARIO_IDS)
        self.assertNotIn("chlamy_dnaaf18_ift46_positive", {row["scenario_id"] for row in rows})
        self.assertTrue(EXCLUDED_SCENARIO_IDS.isdisjoint({row["scenario_id"] for row in rows}))

    def test_benchmark_fasta_manifest_is_independent_and_minimal(self) -> None:
        rows = read_tsv(BENCHMARK_FASTA_MANIFEST)
        self.assertEqual({row["record_id"] for row in rows}, EXPECTED_BENCHMARK_RECORDS)
        self.assertEqual({row["accession"] for row in rows}, EXPECTED_BENCHMARK_ACCESSIONS)
        text = BENCHMARK_FASTA_MANIFEST.read_text(encoding="utf-8")
        for token in FORBIDDEN_MANIFEST_TOKENS:
            self.assertNotIn(token, text)
        self.assertNotEqual(
            BENCHMARK_FASTA_MANIFEST,
            Path("data/processed/fasta/fasta_manifest.tsv"),
        )

    def test_benchmark_fasta_manifest_references_existing_versioned_fastas_only(self) -> None:
        for row in read_tsv(BENCHMARK_FASTA_MANIFEST):
            fasta_path = Path(row["fasta_path"])
            self.assertTrue(fasta_path.exists(), f"Missing benchmark FASTA reference {fasta_path}")
            self.assertEqual(fasta_path.parent, FASTA_DIR)
            self.assertEqual(fasta_path.name, f"{row['record_id']}.fasta")

    def test_milestone2_remote_env_uses_benchmark_paths(self) -> None:
        text = BENCHMARK_REMOTE_ENV.read_text(encoding="utf-8")
        self.assertIn("data/processed/benchmarks/fasta/fasta_manifest.tsv", text)
        self.assertIn("data/processed/benchmarks/alphapulldown_inputs", text)
        self.assertIn("results/milestone2_benchmark/features", text)
        self.assertIn("results/milestone2_benchmark/alphapulldown", text)
        self.assertIn("results/milestone2_benchmark/logs", text)
        self.assertIn("results/milestone2_benchmark/tmp", text)
        self.assertIn("results/provenance/milestone2_benchmark", text)
        self.assertNotIn("data/processed/fasta/fasta_manifest.tsv", text)

    def test_remote_runner_selects_milestone2_accessions_from_benchmark_inputs(self) -> None:
        accessions = accessions_for_screen("milestone2", BENCHMARK_AP_INPUTS)
        self.assertEqual(set(accessions), EXPECTED_BENCHMARK_ACCESSIONS)

    def test_remote_feature_config_uses_benchmark_fasta_manifest_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = benchmark_remote_config(Path(tmp))
            path, feature_inputs = write_resolved_feature_config(config, run_id="feature-m2")
            feature_lines = feature_inputs.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(feature_lines), len(EXPECTED_BENCHMARK_RECORDS))
            self.assertTrue(all("/data/processed/fasta/HUMAN_" in line for line in feature_lines))
            text = path.read_text(encoding="utf-8")
            self.assertIn("feature_inputs.txt", text)
            self.assertNotIn("data/processed/fasta/fasta_manifest.tsv", text)

    def test_remote_prediction_config_writes_eight_milestone2_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = benchmark_remote_config(Path(tmp))
            path, inputs = write_resolved_prediction_config(
                config, screen="milestone2", run_id="prediction-m2"
            )
            self.assertEqual(len(inputs), 1)
            lines = inputs[0].read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 8)
            self.assertIn("HUMAN_DNAAF18.fasta+/", lines[0] + "/")
            self.assertNotIn("chlamy", inputs[0].read_text(encoding="utf-8").lower())
            self.assertIn("prediction.milestone2.config.yaml", str(path))

    def test_milestone2_prediction_command_is_selectable_and_full_remains_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = benchmark_remote_config(Path(tmp))
            command = prediction_command(config, screen="milestone2", dry_run=True)
            self.assertIn("--dry-run", command)
            with self.assertRaises(ValidationError):
                prediction_command(config, screen="full", dry_run=True)

    def test_milestone2_feature_coverage_uses_only_benchmark_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = benchmark_remote_config(tmp_path)
            missing = missing_features(config, "milestone2")
            self.assertEqual(len(missing), len(EXPECTED_BENCHMARK_RECORDS))
            (tmp_path / "features").mkdir()
            for record_id in EXPECTED_BENCHMARK_RECORDS:
                (tmp_path / "features" / f"{record_id}.pkl.xz").write_text("feature")
            self.assertEqual(missing_features(config, "milestone2"), [])

    def test_chlamydomonas_scenario_is_blocked_if_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_dir = copy_benchmark_inputs(Path(tmp))
            with (input_dir / "milestone2_sample_sheet.tsv").open("a", encoding="utf-8") as handle:
                handle.write("chlamy_dnaaf18_ift46_positive\t\t\n")
            with self.assertRaisesRegex(
                ValidationError, "versioned sequence records are absent"
            ):
                accessions_for_screen("milestone2", input_dir)

    def test_excluded_milestone2_scenario_is_rejected_if_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_dir = copy_benchmark_inputs(Path(tmp))
            with (input_dir / "milestone2_sample_sheet.tsv").open("a", encoding="utf-8") as handle:
                handle.write("human_dnaaf9_ift74\tHUMAN_DNAAF9+HUMAN_IFT74\tQ5TEA3+Q96LB3\n")
            with self.assertRaisesRegex(ValidationError, "explicitly excluded"):
                accessions_for_screen("milestone2", input_dir)


def read_tsv(path: Path) -> list[dict[str, str]]:
    import csv

    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def benchmark_remote_config(tmp_path: Path):
    env = tmp_path / "paths.env"
    root = Path.cwd()
    env.write_text(
        "\n".join(
            [
                f"REMOTE_PROJECT_ROOT={root}",
                "REMOTE_EXECUTION_STAGE=cpu",
                f"AP_WORKFLOW_DIR={tmp_path / 'workflow'}",
                "CONDA_ENV_NAME=snake",
                "AP_SNAKEMAKE_VERSION=2.5.0",
                f"FEATURE_CONFIG={root / 'config/remote/feature_generation.example.yaml'}",
                f"PREDICTION_CONFIG={root / 'config/remote/prediction.example.yaml'}",
                f"FASTA_MANIFEST={root / BENCHMARK_FASTA_MANIFEST}",
                f"ALPHAPULLDOWN_INPUT_DIR={root / BENCHMARK_AP_INPUTS}",
                f"FASTA_DIR={root / FASTA_DIR}",
                f"FEATURE_DIR={tmp_path / 'features'}",
                f"OUTPUT_DIR={tmp_path / 'output'}",
                f"LOG_DIR={tmp_path / 'logs'}",
                f"TMP_DIR={tmp_path / 'tmp'}",
                f"PROVENANCE_DIR={tmp_path / 'provenance'}",
                "DATABASES_DIR=",
                "BACKEND_WEIGHTS_DIR=",
                "FEATURE_MODE=mmseqs2",
                "FEATURE_FILE_PATTERN={record_id}.pkl.xz",
                "SNAKEMAKE_CORES=9",
                "SNAKEMAKE_JOBS=1",
                "SNAKEMAKE_PROFILE=",
                "SLURM_PROFILE=",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return load_remote_config(env)


def copy_benchmark_inputs(tmp_path: Path) -> Path:
    root = tmp_path / "benchmarks"
    input_dir = root / "alphapulldown_inputs"
    input_dir.mkdir(parents=True)
    shutil.copy2(SCENARIO_MANIFEST, root / "milestone2_scenarios.json")
    shutil.copy2(BENCHMARK_SAMPLE_SHEET, input_dir / "milestone2_sample_sheet.tsv")
    return input_dir


if __name__ == "__main__":
    unittest.main()
