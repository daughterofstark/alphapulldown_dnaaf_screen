"""Deterministic canonical FASTA generation."""

from __future__ import annotations

import csv
from pathlib import Path

from .provenance import sha256_file
from .targets import Target
from .validation import require


def wrap_sequence(sequence: str, width: int = 80) -> str:
    return "\n".join(sequence[index : index + width] for index in range(0, len(sequence), width))


def fasta_text(target: Target) -> str:
    require(bool(target.sequence), f"{target.record_id}: cannot write FASTA without sequence")
    return f"{target.fasta_header()}\n{wrap_sequence(target.sequence)}\n"


def write_fastas(targets: list[Target], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for target in sorted(targets, key=lambda item: item.record_id):
        path = output_dir / f"{target.record_id}.fasta"
        text = fasta_text(target)
        if path.exists() and path.read_text(encoding="utf-8") != text:
            raise ValueError(f"Refusing to overwrite mismatched FASTA: {path}")
        path.write_text(text, encoding="utf-8")
        paths.append(path)
    write_fasta_manifest(targets, output_dir / "fasta_manifest.tsv", output_dir)
    paths.append(output_dir / "fasta_manifest.tsv")
    return paths


def write_fasta_manifest(targets: list[Target], path: Path, fasta_dir: Path) -> None:
    rows = []
    for target in sorted(targets, key=lambda item: item.record_id):
        fasta_path = fasta_dir / f"{target.record_id}.fasta"
        rows.append(
            {
                "record_id": target.record_id,
                "display_name": target.display_name,
                "accession": target.accession,
                "group": target.protein_group,
                "sequence_length": target.length,
                "sha256": target.sequence_sha256,
                "fasta_path": str(fasta_path),
                "fasta_sha256": sha256_file(fasta_path) if fasta_path.exists() else "",
            }
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
