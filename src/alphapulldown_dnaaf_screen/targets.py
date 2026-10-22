"""Typed loading and validation of verified UniProt target records."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .validation import ValidationError, require, validate_accession, validate_sequence

REQUIRED_FIELDS = {
    "record_id",
    "display_name",
    "protein_group",
    "uniprot_accession",
    "organism",
    "length",
    "sequence_sha256",
    "reviewed",
    "role",
}

HEAVY_CHAIN_RECORD_IDS = frozenset(
    {"HUMAN_DNAH5", "HUMAN_DNAH8", "HUMAN_DNAH9", "HUMAN_DNAH11", "HUMAN_DNAH17"}
)


@dataclass(frozen=True)
class Target:
    record_id: str
    display_name: str
    protein_group: str
    accession: str
    organism: str
    length: int
    sequence_sha256: str
    reviewed: bool
    role: str
    genes: tuple[str, ...]
    aliases: tuple[str, ...]
    sequence: str

    @property
    def requires_construct_review(self) -> bool:
        return self.record_id in HEAVY_CHAIN_RECORD_IDS

    @property
    def alphapulldown_token(self) -> str:
        return self.accession

    def fasta_header(self) -> str:
        return f">{self.record_id}|{self.accession}|{self.display_name}"


def _split_semicolon(value: str) -> tuple[str, ...]:
    return tuple(part for part in value.split(";") if part)


def _load_raw_sequence(raw_dir: Path, record_id: str) -> str:
    path = raw_dir / f"{record_id}.json"
    if not path.exists():
        raise ValidationError(
            f"{record_id}: missing raw UniProt JSON sequence source at {path}. "
            "Regenerate raw records before writing FASTA files."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    entry = payload.get("entry", payload)
    sequence = entry.get("sequence", {}).get("value", "")
    validate_sequence(sequence, record_id=record_id)
    return sequence


def _parse_reviewed(value: Any, *, record_id: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    raise ValidationError(f"{record_id}: reviewed must be boolean-like")


def _target_from_row(
    row: dict[str, Any],
    *,
    raw_dir: Path | None,
    require_sequence: bool,
) -> Target:
    missing = sorted(field for field in REQUIRED_FIELDS if not row.get(field))
    record_id = str(row.get("record_id", "<unknown>"))
    require(not missing, f"{record_id}: missing required fields: {', '.join(missing)}")

    accession = str(row["uniprot_accession"])
    validate_accession(accession)
    require(row["organism"] == "Homo sapiens", f"{record_id}: non-human organism {row['organism']}")

    try:
        length = int(row["length"])
    except ValueError as exc:
        raise ValidationError(f"{record_id}: invalid sequence length {row['length']}") from exc
    require(length > 0, f"{record_id}: sequence length must be positive")

    reviewed = _parse_reviewed(row["reviewed"], record_id=record_id)
    require(reviewed, f"{record_id}: record is not reviewed Swiss-Prot")

    sequence = ""
    if raw_dir is not None:
        sequence = _load_raw_sequence(raw_dir, record_id)
        digest = hashlib.sha256(sequence.encode("utf-8")).hexdigest()
        require(
            digest == row["sequence_sha256"],
            f"{record_id}: checksum mismatch; expected {row['sequence_sha256']} got {digest}",
        )
        require(
            len(sequence) == length,
            f"{record_id}: length mismatch; metadata {length}, sequence {len(sequence)}",
        )
    elif require_sequence:
        raise ValidationError(f"{record_id}: raw_dir is required when sequences are required")

    genes = _split_semicolon(str(row.get("genes_from_uniprot", "")))
    aliases = tuple(gene for gene in genes if gene != row["display_name"])

    return Target(
        record_id=record_id,
        display_name=str(row["display_name"]),
        protein_group=str(row["protein_group"]),
        accession=accession,
        organism=str(row["organism"]),
        length=length,
        sequence_sha256=str(row["sequence_sha256"]),
        reviewed=reviewed,
        role=str(row["role"]),
        genes=genes,
        aliases=aliases,
        sequence=sequence,
    )


def load_targets(
    verified_json: Path,
    *,
    raw_dir: Path | None = None,
    require_sequences: bool = False,
) -> list[Target]:
    rows = json.loads(verified_json.read_text(encoding="utf-8"))
    require(isinstance(rows, list), f"{verified_json}: expected a list of target records")

    targets = [
        _target_from_row(row, raw_dir=raw_dir, require_sequence=require_sequences) for row in rows
    ]
    _validate_unique_targets(targets)
    return targets


def _validate_unique_targets(targets: list[Target]) -> None:
    seen_ids: set[str] = set()
    seen_accessions: set[str] = set()
    for target in targets:
        require(
            target.record_id not in seen_ids,
            f"Duplicate target record ID: {target.record_id}",
        )
        require(
            target.accession not in seen_accessions,
            f"Duplicate UniProt accession mapping: {target.accession}",
        )
        seen_ids.add(target.record_id)
        seen_accessions.add(target.accession)


def targets_by_id(targets: list[Target]) -> dict[str, Target]:
    return {target.record_id: target for target in targets}


def filter_group(targets: list[Target], group: str) -> list[Target]:
    return [target for target in targets if target.protein_group == group]


def target_manifest_rows(targets: list[Target]) -> list[dict[str, str]]:
    rows = []
    for target in sorted(targets, key=lambda item: item.record_id):
        rows.append(
            {
                "record_id": target.record_id,
                "display_name": target.display_name,
                "protein_group": target.protein_group,
                "uniprot_accession": target.accession,
                "organism": target.organism,
                "length": str(target.length),
                "sequence_sha256": target.sequence_sha256,
                "reviewed": str(target.reviewed),
                "requires_construct_review": str(target.requires_construct_review),
                "genes": ";".join(target.genes),
                "aliases": ";".join(target.aliases),
                "role": target.role,
            }
        )
    return rows


def write_validated_manifest(targets: list[Target], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = target_manifest_rows(targets)
    json_path = output_dir / "validated_targets.json"
    tsv_path = output_dir / "validated_targets.tsv"
    json_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with tsv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    return [json_path, tsv_path]
