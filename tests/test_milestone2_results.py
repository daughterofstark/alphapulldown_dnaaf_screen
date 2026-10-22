from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from alphapulldown_dnaaf_screen.milestone2_results import (
    ResultValidationError,
    summarize_prediction,
)


class Milestone2ResultsTests(unittest.TestCase):
    def _write_complete_prediction(self, directory: Path) -> None:
        best = "model_1_multimer_v3_pred_0"
        (directory / "ranking_debug.json").write_text(
            json.dumps({"order": [best], "iptm": {best: 0.5}, "iptm+ptm": {best: 0.6}}),
            encoding="utf-8",
        )
        (directory / f"confidence_{best}.json").write_text(
            json.dumps({"confidenceScore": [80.0, 70.0, 60.0, 50.0]}), encoding="utf-8"
        )
        (directory / f"pae_{best}.json").write_text(
            json.dumps(
                [
                    {
                        "predicted_aligned_error": [
                            [1.0, 2.0, 8.0, 12.0],
                            [2.0, 1.0, 9.0, 13.0],
                            [8.0, 9.0, 1.0, 2.0],
                            [12.0, 13.0, 2.0, 1.0],
                        ]
                    }
                ]
            ),
            encoding="utf-8",
        )
        (directory / "ranked_0.pdb").write_text(
            "ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00 80.00           C\n"
            "ATOM      2  CA  ALA A   2       0.000   0.000   0.000  1.00 70.00           C\n"
            "ATOM      3  CA  ALA B   1       0.000   0.000   0.000  1.00 60.00           C\n"
            "ATOM      4  CA  ALA B   2       0.000   0.000   0.000  1.00 50.00           C\n",
            encoding="utf-8",
        )

    def test_summarizes_complete_prediction(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            prediction_dir = Path(temporary_directory)
            self._write_complete_prediction(prediction_dir)

            summary = summarize_prediction("synthetic", prediction_dir)

        self.assertEqual(summary.scenario_id, "synthetic")
        self.assertEqual(summary.chain_lengths, (2, 2))
        self.assertAlmostEqual(summary.iptm, 0.5)
        self.assertAlmostEqual(summary.ranking_confidence, 0.6)
        self.assertAlmostEqual(summary.mean_plddt, 65.0)
        self.assertAlmostEqual(summary.mean_interchain_pae, 10.5)
        self.assertAlmostEqual(summary.low_pae_interchain_fraction, 0.5)

    def test_rejects_incomplete_prediction(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary_directory,
            self.assertRaisesRegex(ResultValidationError, "ranking_debug"),
        ):
            summarize_prediction("synthetic", Path(temporary_directory))
