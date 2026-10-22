from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

PANEL_TSV = Path("data/processed/screens/first_pass_interaction_panel.tsv")
PANEL_JSON = Path("data/processed/screens/first_pass_interaction_panel.json")
TARGETS_JSON = Path("data/processed/targets/validated_targets.json")

ALLOWED_EVIDENCE_LEVELS = {
    "direct_structural",
    "direct_biochemical",
    "physical_association",
    "functional_association",
    "inference",
    "negative_evidence",
    "no_reported_interaction",
}

ALLOWED_DIRECTNESS = {
    "direct",
    "association_not_binary",
    "functional_only",
    "not_detected",
    "none_reported",
    "unknown",
}

ALLOWED_ROLES = {
    "positive_control",
    "candidate",
    "species_divergence_test",
    "exploratory",
    "negative_control",
    "defer_construct_review",
}

ALLOWED_CONSTRUCT_POLICIES = {
    "full_length_ok",
    "domain_or_fragment_preferred",
    "heterodimer_context_preferred",
    "construct_review_required",
    "not_in_target_universe",
}


def load_tsv() -> list[dict[str, str]]:
    with PANEL_TSV.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_json() -> list[dict[str, object]]:
    return json.loads(PANEL_JSON.read_text(encoding="utf-8"))


def target_accessions() -> set[str]:
    rows = json.loads(TARGETS_JSON.read_text(encoding="utf-8"))
    return {row["uniprot_accession"] for row in rows}


class FirstPassPanelTests(unittest.TestCase):
    def test_json_and_tsv_contain_same_pair_ids(self) -> None:
        tsv_ids = [row["pair_id"] for row in load_tsv()]
        json_ids = [str(row["pair_id"]) for row in load_json()]
        self.assertEqual(tsv_ids, json_ids)
        self.assertEqual(len(tsv_ids), len(set(tsv_ids)))

    def test_allowed_schema_values(self) -> None:
        for row in load_tsv():
            self.assertIn(row["evidence_level"], ALLOWED_EVIDENCE_LEVELS)
            self.assertIn(row["directness"], ALLOWED_DIRECTNESS)
            self.assertIn(row["alphapulldown_role"], ALLOWED_ROLES)
            self.assertIn(row["construct_policy"], ALLOWED_CONSTRUCT_POLICIES)
            self.assertIn(row["include_in_first_run"], {"true", "false"})

    def test_every_included_human_protein_exists_in_verified_targets(self) -> None:
        accessions = target_accessions()
        for row in load_tsv():
            for side in ["a", "b"]:
                species = row[f"species_{side}"]
                uniprot_value = row[f"protein_{side}_uniprot"]
                if species != "Homo sapiens":
                    continue
                for accession in uniprot_value.split("+"):
                    self.assertIn(accession, accessions, row["pair_id"])

    def test_ccdc103_negative_controls_are_not_candidate_positives(self) -> None:
        rows = [row for row in load_tsv() if row["protein_a_symbol"] == "CCDC103/DNAAF19"]
        self.assertEqual(len(rows), 4)
        for row in rows:
            self.assertEqual(row["alphapulldown_role"], "negative_control")
            self.assertEqual(row["evidence_level"], "no_reported_interaction")
            self.assertEqual(row["directness"], "none_reported")

    def test_dnaaf9_ift74_ift81_are_not_labelled_direct(self) -> None:
        rows = [
            row
            for row in load_tsv()
            if row["pair_id"]
            in {
                "HUMAN_DNAAF9__HUMAN_IFT74",
                "HUMAN_DNAAF9__HUMAN_IFT81",
                "HUMAN_DNAAF9__HUMAN_IFT74_IFT81",
            }
        ]
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row["evidence_level"], "physical_association")
            self.assertEqual(row["directness"], "association_not_binary")

    def test_human_oda16_ift46_is_species_divergence_not_positive(self) -> None:
        row = next(row for row in load_tsv() if row["pair_id"] == "HUMAN_DNAAF18__HUMAN_IFT46")
        self.assertEqual(row["alphapulldown_role"], "species_divergence_test")
        self.assertEqual(row["evidence_level"], "negative_evidence")
        self.assertEqual(row["directness"], "not_detected")

    def test_chlamydomonas_oda16_ift46_is_external_benchmark(self) -> None:
        row = next(row for row in load_tsv() if row["pair_id"] == "EXT_CR_ODA16__CR_IFT46")
        self.assertEqual(row["alphapulldown_role"], "positive_control")
        self.assertEqual(row["construct_policy"], "not_in_target_universe")
        self.assertEqual(row["include_in_first_run"], "false")
        self.assertEqual(row["protein_a_uniprot"], "")
        self.assertIn("External benchmark", row["notes"])

    def test_heavy_chain_full_length_pairs_are_deferred(self) -> None:
        rows = [
            row
            for row in load_tsv()
            if row["protein_a_symbol"] in {"DNAH5 full-length", "DNAH9 full-length"}
        ]
        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertEqual(row["alphapulldown_role"], "defer_construct_review")
            self.assertEqual(row["construct_policy"], "construct_review_required")
            self.assertEqual(row["include_in_first_run"], "false")

    def test_first_pass_panel_is_deterministic(self) -> None:
        rows = load_tsv()
        ranks = [int(row["priority_rank"]) for row in rows]
        self.assertEqual(ranks, sorted(ranks))
        self.assertEqual(ranks, list(range(1, len(rows) + 1)))
        expected_json = json.dumps(load_json(), indent=2, sort_keys=True) + "\n"
        self.assertEqual(PANEL_JSON.read_text(encoding="utf-8"), expected_json)


if __name__ == "__main__":
    unittest.main()
