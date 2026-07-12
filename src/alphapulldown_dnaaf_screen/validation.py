"""Validation helpers shared by the CPU-side preparation pipeline."""

from __future__ import annotations

import re


class ValidationError(ValueError):
    """Raised when project metadata or generated artifacts fail validation."""


ACCESSION_RE = re.compile(
    r"^(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9][A-Z][A-Z0-9]{2}[0-9])$"
)
AMINO_ACID_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWYBXZUOJ]+$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_accession(accession: str) -> None:
    require(bool(accession), "UniProt accession is required")
    require(bool(ACCESSION_RE.match(accession)), f"Malformed UniProt accession: {accession}")


def validate_sequence(sequence: str, *, record_id: str) -> None:
    require(bool(sequence), f"{record_id}: missing canonical sequence")
    require(
        bool(AMINO_ACID_RE.match(sequence)),
        f"{record_id}: sequence contains non-amino-acid characters",
    )
