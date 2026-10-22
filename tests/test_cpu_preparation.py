from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from alphapulldown_dnaaf_screen.fasta import write_fastas
from alphapulldown_dnaaf_screen.samplesheets import (
    validate_alphapulldown_spec,
    write_alphapulldown_inputs,
)
from alphapulldown_dnaaf_screen.screens import control_pairs, full_screen_pairs
from alphapulldown_dnaaf_screen.targets import load_targets
from alphapulldown_dnaaf_screen.validation import ValidationError


def _sha(sequence: str) -> str:
    return hashlib.sha256(sequence.encode("utf-8")).hexdigest()


def _row(record_id: str, display: str, accession: str, group: str, sequence: str) -> dict[str, str]:
    return {
        "record_id": record_id,
        "display_name": display,
        "protein_group": group,
        "uniprot_accession": accession,
        "uniprot_entry": f"{display}_HUMAN",
        "protein_name": display,
        "genes_from_uniprot": display,
        "organism": "Homo sapiens",
        "length": str(len(sequence)),
        "sequence_sha256": _sha(sequence),
        "hgnc_ids": "HGNC:1",
        "gene_ids": "1",
        "pdb_ids": "",
        "pubmed_ids": "",
        "query_symbol_used": display,
        "reviewed": "True",
        "role": f"{display} role",
        "uniprot_url": f"https://www.uniprot.org/uniprotkb/{accession}/entry",
    }


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.verified = root / "targets.json"
        self.raw_dir = root / "raw"
        self.raw_dir.mkdir()
        self.sequences = {
            "HUMAN_DNAAF9": "MAAAAA",
            "HUMAN_DNAAF18": "MBBBBB",
            "HUMAN_DNAAF2": "MCCCCC",
            "HUMAN_DNAAF4": "MDDDDD",
            "HUMAN_DNAI1": "MEEEEE",
            "HUMAN_DNAI2": "MFFFFF",
            "HUMAN_DNAH5": "MGGGGG",
            "HUMAN_IFT74": "MHHHHH",
            "HUMAN_IFT81": "MIIIII",
            "HUMAN_IFT46": "MKKKKK",
            "HUMAN_IFT70A": "MLLLLL",
            "HUMAN_IFT70B": "MMMMMM",
            "HUMAN_IFT43": "MNNNNN",
            "HUMAN_ODAD1": "MPPPPP",
        }
        self.rows = [
            _row("HUMAN_DNAAF9", "DNAAF9", "Q5TEA3", "DNAAF", self.sequences["HUMAN_DNAAF9"]),
            _row("HUMAN_DNAAF18", "DNAAF18", "Q8N136", "DNAAF", self.sequences["HUMAN_DNAAF18"]),
            _row("HUMAN_DNAAF2", "DNAAF2", "Q9NVR5", "DNAAF", self.sequences["HUMAN_DNAAF2"]),
            _row("HUMAN_DNAAF4", "DNAAF4", "Q8WXU2", "DNAAF", self.sequences["HUMAN_DNAAF4"]),
            _row("HUMAN_DNAI1", "DNAI1", "Q9UI46", "ODA", self.sequences["HUMAN_DNAI1"]),
            _row("HUMAN_DNAI2", "DNAI2", "Q9GZS0", "ODA", self.sequences["HUMAN_DNAI2"]),
            _row("HUMAN_DNAH5", "DNAH5", "Q8TE73", "ODA", self.sequences["HUMAN_DNAH5"]),
            _row("HUMAN_IFT74", "IFT74", "Q96LB3", "IFT_B", self.sequences["HUMAN_IFT74"]),
            _row("HUMAN_IFT81", "IFT81", "Q8WYA0", "IFT_B", self.sequences["HUMAN_IFT81"]),
            _row("HUMAN_IFT46", "IFT46", "Q9NQC8", "IFT_B", self.sequences["HUMAN_IFT46"]),
            _row("HUMAN_IFT70A", "IFT70A", "Q86WT1", "IFT_B", self.sequences["HUMAN_IFT70A"]),
            _row("HUMAN_IFT70B", "IFT70B", "Q8N4P2", "IFT_B", self.sequences["HUMAN_IFT70B"]),
            _row("HUMAN_IFT43", "IFT43", "Q96FT9", "IFT_A", self.sequences["HUMAN_IFT43"]),
            _row("HUMAN_ODAD1", "ODAD1", "Q96M63", "ODAD", self.sequences["HUMAN_ODAD1"]),
        ]
        self.write()

    def write(self) -> None:
        self.verified.write_text(json.dumps(self.rows), encoding="utf-8")
        for row in self.rows:
            sequence = self.sequences[row["record_id"]]
            payload = {"entry": {"sequence": {"value": sequence, "length": len(sequence)}}}
            (self.raw_dir / f"{row['record_id']}.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )


class CpuPreparationTests(unittest.TestCase):
    def test_valid_target_loading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            targets = load_targets(
                fixture.verified,
                raw_dir=fixture.raw_dir,
                require_sequences=True,
            )
            self.assertEqual(len(targets), len(fixture.rows))

    def test_duplicate_record_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            rows = fixture.rows + [fixture.rows[0]]
            fixture.verified.write_text(json.dumps(rows), encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_targets(fixture.verified, raw_dir=fixture.raw_dir, require_sequences=True)

    def test_malformed_accession_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.rows[0]["uniprot_accession"] = "BAD_ACCESSION"
            fixture.verified.write_text(json.dumps(fixture.rows), encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_targets(fixture.verified, raw_dir=fixture.raw_dir, require_sequences=True)

    def test_checksum_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.rows[0]["sequence_sha256"] = "0" * 64
            fixture.verified.write_text(json.dumps(fixture.rows), encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_targets(fixture.verified, raw_dir=fixture.raw_dir, require_sequences=True)

    def test_deterministic_fasta_output_and_idempotent_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            targets = load_targets(
                fixture.verified,
                raw_dir=fixture.raw_dir,
                require_sequences=True,
            )
            output = Path(tmp) / "fasta"
            first = write_fastas(targets, output)
            first_text = (output / "HUMAN_DNAAF9.fasta").read_text(encoding="utf-8")
            second = write_fastas(targets, output)
            second_text = (output / "HUMAN_DNAAF9.fasta").read_text(encoding="utf-8")
            self.assertEqual([path.name for path in first], [path.name for path in second])
            self.assertEqual(first_text, second_text)
            self.assertTrue(first_text.startswith(">HUMAN_DNAAF9|Q5TEA3|DNAAF9\n"))

    def test_control_presence_and_no_duplicate_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            targets = load_targets(
                fixture.verified,
                raw_dir=fixture.raw_dir,
                require_sequences=True,
            )
            pairs = control_pairs(targets)
            pair_ids = [pair.pair_id for pair in pairs]
            self.assertEqual(len(pair_ids), len(set(pair_ids)))
            self.assertIn("HUMAN_DNAAF9__HUMAN_IFT74", pair_ids)
            self.assertIn("HUMAN_DNAAF18__HUMAN_IFT46", pair_ids)

    def test_ift70_paralogs_retained_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            targets = load_targets(
                fixture.verified,
                raw_dir=fixture.raw_dir,
                require_sequences=True,
            )
            output = Path(tmp) / "ap"
            write_alphapulldown_inputs(output, targets)
            preys = (output / "ift_b_preys.txt").read_text(encoding="utf-8")
            self.assertIn("Q86WT1", preys)
            self.assertIn("Q8N4P2", preys)

    def test_heavy_chains_marked_not_executable_in_full_screen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            targets = load_targets(
                fixture.verified,
                raw_dir=fixture.raw_dir,
                require_sequences=True,
            )
            pairs = full_screen_pairs(targets)
            heavy = [pair for pair in pairs if pair.prey_id == "HUMAN_DNAH5"]
            self.assertTrue(heavy)
            self.assertTrue(all(pair.requires_construct_review for pair in heavy))
            self.assertTrue(all(not pair.executable for pair in heavy))

    def test_alphapulldown_syntax_correctness(self) -> None:
        validate_alphapulldown_spec("Q5TEA3+Q96LB3")
        with self.assertRaises(ValidationError):
            validate_alphapulldown_spec("HUMAN_DNAAF9+Q96LB3")

    def test_cli_smoke_write_fastas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = Fixture(root)
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path.cwd() / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "alphapulldown_dnaaf_screen.cli",
                    "--verified-json",
                    str(fixture.verified),
                    "--raw-dir",
                    str(fixture.raw_dir),
                    "--provenance-dir",
                    str(root / "provenance"),
                    "write-fastas",
                    "--output-dir",
                    str(root / "fasta"),
                ],
                cwd=Path.cwd(),
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "fasta" / "HUMAN_DNAAF9.fasta").exists())


if __name__ == "__main__":
    unittest.main()
