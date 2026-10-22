"""Offline summarization of completed Milestone 2 AlphaPulldown outputs."""

from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path


class ResultValidationError(ValueError):
    """Raised when a prediction directory is incomplete or internally inconsistent."""


@dataclass(frozen=True)
class PredictionSummary:
    """Metrics derived from the top-ranked AlphaPulldown model for one scenario."""

    scenario_id: str
    best_model: str
    iptm: float
    ranking_confidence: float
    mean_plddt: float
    chain_lengths: tuple[int, ...]
    mean_interchain_pae: float
    low_pae_interchain_fraction: float

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["chain_lengths"] = list(self.chain_lengths)
        return data


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ResultValidationError(f"Missing required output: {path}") from error
    except json.JSONDecodeError as error:
        raise ResultValidationError(f"Invalid JSON output: {path}") from error


def _chain_lengths_from_pdb(path: Path) -> tuple[int, ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as error:
        raise ResultValidationError(f"Missing top-ranked structure: {path}") from error

    residues: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for line in lines:
        if not line.startswith("ATOM") or line[12:16].strip() != "CA":
            continue
        residue = (line[21], line[22:26].strip(), line[26])
        if residue not in seen:
            seen.add(residue)
            residues.append(residue)

    if not residues:
        raise ResultValidationError(f"No CA residues found in top-ranked structure: {path}")

    lengths: list[int] = []
    previous_chain: str | None = None
    for chain, _, _ in residues:
        if chain != previous_chain:
            lengths.append(0)
            previous_chain = chain
        lengths[-1] += 1
    return tuple(lengths)


def _interchain_pae_metrics(
    pae_matrix: list[list[float]], chain_lengths: tuple[int, ...]
) -> tuple[float, float]:
    expected_size = sum(chain_lengths)
    if len(pae_matrix) != expected_size or any(len(row) != expected_size for row in pae_matrix):
        raise ResultValidationError(
            "PAE matrix dimensions do not match the residue count in ranked_0.pdb"
        )

    chain_for_residue: list[int] = []
    for chain_index, length in enumerate(chain_lengths):
        chain_for_residue.extend([chain_index] * length)

    interchain = [
        value
        for row_index, row in enumerate(pae_matrix)
        for column_index, value in enumerate(row)
        if chain_for_residue[row_index] != chain_for_residue[column_index]
    ]
    if not interchain:
        raise ResultValidationError("At least two chains are required for interchain PAE analysis")
    return statistics.mean(interchain), sum(value <= 10.0 for value in interchain) / len(interchain)


def summarize_prediction(scenario_id: str, prediction_dir: Path) -> PredictionSummary:
    """Validate and summarize one completed AlphaPulldown prediction directory."""

    ranking = _load_json(prediction_dir / "ranking_debug.json")
    if not isinstance(ranking, dict):
        raise ResultValidationError("ranking_debug.json must contain an object")
    order = ranking.get("order")
    iptm_by_model = ranking.get("iptm")
    confidence_by_model = ranking.get("iptm+ptm")
    if not isinstance(order, list) or not order or not isinstance(iptm_by_model, dict):
        raise ResultValidationError(
            "ranking_debug.json lacks a valid ranked model order and ipTM values"
        )
    if not isinstance(confidence_by_model, dict):
        raise ResultValidationError("ranking_debug.json lacks ranking-confidence values")

    best_model = order[0]
    if best_model not in iptm_by_model or best_model not in confidence_by_model:
        raise ResultValidationError("Top-ranked model is missing a score in ranking_debug.json")

    confidence = _load_json(prediction_dir / f"confidence_{best_model}.json")
    if not isinstance(confidence, dict) or not isinstance(confidence.get("confidenceScore"), list):
        raise ResultValidationError(f"Missing confidence scores for {best_model}")
    confidence_scores = confidence["confidenceScore"]
    if not confidence_scores:
        raise ResultValidationError(f"No confidence scores found for {best_model}")

    pae = _load_json(prediction_dir / f"pae_{best_model}.json")
    if not isinstance(pae, list) or not pae or not isinstance(pae[0], dict):
        raise ResultValidationError(f"Invalid PAE output for {best_model}")
    pae_matrix = pae[0].get("predicted_aligned_error")
    if not isinstance(pae_matrix, list):
        raise ResultValidationError(f"PAE matrix is missing for {best_model}")

    chain_lengths = _chain_lengths_from_pdb(prediction_dir / "ranked_0.pdb")
    mean_pae, low_pae_fraction = _interchain_pae_metrics(pae_matrix, chain_lengths)
    return PredictionSummary(
        scenario_id=scenario_id,
        best_model=str(best_model),
        iptm=float(iptm_by_model[best_model]),
        ranking_confidence=float(confidence_by_model[best_model]),
        mean_plddt=statistics.mean(float(value) for value in confidence_scores),
        chain_lengths=chain_lengths,
        mean_interchain_pae=mean_pae,
        low_pae_interchain_fraction=low_pae_fraction,
    )


def summarize_results_root(results_root: Path) -> list[PredictionSummary]:
    """Summarize every complete prediction directory immediately below ``results_root``."""

    if not results_root.is_dir():
        raise ResultValidationError(f"Prediction root does not exist: {results_root}")
    return [
        summarize_prediction(prediction_dir.name, prediction_dir)
        for prediction_dir in sorted(path for path in results_root.iterdir() if path.is_dir())
    ]
