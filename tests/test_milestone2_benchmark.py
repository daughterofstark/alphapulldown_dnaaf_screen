from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


SCENARIO_MANIFEST = Path("data/processed/benchmarks/milestone2_scenarios.json")
BENCHMARK_CONFIG = Path("config/benchmarks/milestone2_benchmark.example.yaml")
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


if __name__ == "__main__":
    unittest.main()
