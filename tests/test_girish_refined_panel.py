from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

PANEL_TSV = Path("data/processed/screens/girish_refined_first_run_panel.tsv")
PANEL_JSON = Path("data/processed/screens/girish_refined_first_run_panel.json")
RUNPOD_TSV = Path("data/processed/alphapulldown/girish_refined_runpod_first_run.tsv")

PRIMARY_GROUPS = {"exact_executable_now", "multichain_primary_if_supported"}


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_json(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


class GirishRefinedPanelTests(unittest.TestCase):
    def test_refined_panel_exists_and_is_deterministic(self) -> None:
        rows = load_tsv(PANEL_TSV)
        self.assertEqual(len(rows), 11)
        ranks = [int(row["priority_rank"]) for row in rows]
        self.assertEqual(ranks, list(range(1, len(rows) + 1)))
        expected_json = json.dumps(load_json(PANEL_JSON), indent=2, sort_keys=True) + "\n"
        self.assertEqual(PANEL_JSON.read_text(encoding="utf-8"), expected_json)

    def test_json_and_tsv_agree_on_set_ids(self) -> None:
        tsv_ids = [row["set_id"] for row in load_tsv(PANEL_TSV)]
        json_ids = [str(row["set_id"]) for row in load_json(PANEL_JSON)]
        self.assertEqual(tsv_ids, json_ids)
        self.assertEqual(len(tsv_ids), len(set(tsv_ids)))

    def test_isolated_dnaaf9_ift74_and_ift81_are_not_primary_jobs(self) -> None:
        forbidden_primary_specs = {"Q5TEA3+Q96LB3", "Q5TEA3+Q8WYA0"}
        for row in load_tsv(RUNPOD_TSV):
            if row["alphapulldown_spec"] in forbidden_primary_specs:
                self.assertEqual(row["job_group"], "fallback_only", row)
                self.assertEqual(row["include_by_default"], "false", row)

    def test_ift74_ift81_alone_is_not_first_run_job(self) -> None:
        specs = {row["alphapulldown_spec"] for row in load_tsv(RUNPOD_TSV)}
        self.assertNotIn("Q96LB3+Q8WYA0", specs)
        self.assertNotIn("Q8WYA0+Q96LB3", specs)

    def test_dnaaf19_ift_jobs_are_not_first_run_jobs(self) -> None:
        for row in load_tsv(RUNPOD_TSV):
            self.assertNotIn("DNAAF19", row["components"])
            self.assertNotIn("Q8IW40", row["alphapulldown_spec"])

    def test_human_dnaaf18_ift46_negative_control_present(self) -> None:
        panel_row = next(row for row in load_tsv(PANEL_TSV) if row["set_id"] == "GR_SET_002")
        self.assertEqual(panel_row["category"], "negative_control")
        self.assertEqual(panel_row["directness"], "not_detected")
        self.assertEqual(panel_row["include_in_runpod_first_run"], "true")
        runpod_row = next(row for row in load_tsv(RUNPOD_TSV) if row["set_id"] == "GR_SET_002")
        self.assertEqual(runpod_row["alphapulldown_spec"], "Q8N136+Q9NQC8")
        self.assertEqual(runpod_row["job_group"], "exact_executable_now")

    def test_chlamydomonas_positive_is_external_benchmark(self) -> None:
        panel_row = next(row for row in load_tsv(PANEL_TSV) if row["set_id"] == "GR_SET_001")
        self.assertEqual(panel_row["category"], "positive_control")
        self.assertEqual(panel_row["alphapulldown_input_type"], "external_benchmark")
        self.assertEqual(panel_row["requires_external_sequence"], "true")
        self.assertEqual(panel_row["include_in_runpod_first_run"], "false")
        runpod_row = next(row for row in load_tsv(RUNPOD_TSV) if row["set_id"] == "GR_SET_001")
        self.assertEqual(runpod_row["job_group"], "external_benchmark_requires_sequences")
        self.assertEqual(runpod_row["alphapulldown_spec"], "")

    def test_dnah5_and_dnah9_are_deferred_construct_review_only(self) -> None:
        deferred = [
            row for row in load_tsv(PANEL_TSV) if row["set_id"] in {"GR_SET_010", "GR_SET_011"}
        ]
        self.assertEqual(len(deferred), 2)
        for row in deferred:
            self.assertEqual(row["category"], "future_construct_review")
            self.assertEqual(row["alphapulldown_input_type"], "deferred_construct")
            self.assertEqual(row["construct_policy"], "construct_review_required")
            self.assertEqual(row["include_in_runpod_first_run"], "false")
        runpod_text = RUNPOD_TSV.read_text(encoding="utf-8")
        self.assertNotIn("Q8TE73", runpod_text)
        self.assertNotIn("Q9NYC9", runpod_text)

    def test_multichain_jobs_are_labelled_honestly(self) -> None:
        for row in load_tsv(RUNPOD_TSV):
            chain_count = (
                row["alphapulldown_spec"].count("+") + 1 if row["alphapulldown_spec"] else 0
            )
            if row["job_group"] == "multichain_primary_if_supported":
                self.assertEqual(row["requires_multichain_support"], "true", row)
                self.assertGreaterEqual(chain_count, 3, row)
                self.assertNotEqual(row["input_type"], "binary", row)
            if row["job_group"] == "fallback_only":
                self.assertEqual(row["include_by_default"], "false", row)
                self.assertTrue(row["fallback_for_set_id"], row)

    def test_primary_runpod_job_count(self) -> None:
        primary = [
            row
            for row in load_tsv(RUNPOD_TSV)
            if row["job_group"] in PRIMARY_GROUPS and row["include_by_default"] == "true"
        ]
        self.assertEqual(len(primary), 8)


if __name__ == "__main__":
    unittest.main()
