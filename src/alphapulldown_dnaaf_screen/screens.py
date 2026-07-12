"""Screen definitions and pair construction for AlphaPulldown preparation."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from .targets import Target, filter_group, targets_by_id
from .validation import require


@dataclass(frozen=True)
class Pair:
    pair_id: str
    bait_id: str
    prey_id: str
    screen: str
    control_type: str
    rationale: str
    executable: bool = True
    requires_construct_review: bool = False

    def alphapulldown_spec(self, by_id: dict[str, Target]) -> str:
        bait_token = by_id[self.bait_id].alphapulldown_token
        prey_token = by_id[self.prey_id].alphapulldown_token
        return f"{bait_token}+{prey_token}"


CONTROL_SPECS = [
    (
        "HUMAN_DNAAF9",
        "HUMAN_IFT74",
        "positive",
        "Known DNAAF9/Shulin interaction with IFT-B transport machinery.",
    ),
    (
        "HUMAN_DNAAF9",
        "HUMAN_IFT81",
        "positive",
        "Known DNAAF9/Shulin interaction with IFT-B transport machinery.",
    ),
    (
        "HUMAN_DNAAF2",
        "HUMAN_DNAAF4",
        "positive",
        "R2TP-like dynein assembly factor interaction.",
    ),
    (
        "HUMAN_DNAI1",
        "HUMAN_DNAI2",
        "positive",
        "ODA intermediate-chain dimer benchmark.",
    ),
    (
        "HUMAN_DNAAF18",
        "HUMAN_IFT46",
        "human_nonconserved_candidate",
        "Human benchmark candidate; algal ODA16-IFT46 biology should not be assumed conserved.",
    ),
]


def pair_id(bait_id: str, prey_id: str) -> str:
    return f"{bait_id}__{prey_id}"


def validate_pair_set(pairs: list[Pair]) -> None:
    seen: set[str] = set()
    for pair in pairs:
        require(pair.pair_id not in seen, f"Duplicate pair ID: {pair.pair_id}")
        seen.add(pair.pair_id)


def control_pairs(targets: list[Target]) -> list[Pair]:
    by_id = targets_by_id(targets)
    pairs = []
    for bait_id, prey_id, control_type, rationale in CONTROL_SPECS:
        require(bait_id in by_id, f"Missing control bait: {bait_id}")
        require(prey_id in by_id, f"Missing control prey: {prey_id}")
        pairs.append(
            Pair(
                pair_id=pair_id(bait_id, prey_id),
                bait_id=bait_id,
                prey_id=prey_id,
                screen="control_benchmark",
                control_type=control_type,
                rationale=rationale,
            )
        )
    validate_pair_set(pairs)
    return pairs


def targeted_transport_pairs(targets: list[Target]) -> list[Pair]:
    by_id = targets_by_id(targets)
    baits = ["HUMAN_DNAAF9", "HUMAN_DNAAF18"]
    preys = sorted(filter_group(targets, "IFT_B"), key=lambda target: target.record_id)
    pairs = []
    for bait_id in baits:
        require(bait_id in by_id, f"Missing targeted transport bait: {bait_id}")
        for prey in preys:
            pairs.append(
                Pair(
                    pair_id=pair_id(bait_id, prey.record_id),
                    bait_id=bait_id,
                    prey_id=prey.record_id,
                    screen="targeted_transport",
                    control_type="discovery",
                    rationale="Targeted transport-linked DNAAF versus verified IFT-B prey.",
                )
            )
    validate_pair_set(pairs)
    return pairs


def full_screen_pairs(targets: list[Target]) -> list[Pair]:
    baits = sorted(filter_group(targets, "DNAAF"), key=lambda target: target.record_id)
    prey_groups = {"ODA", "ODAD", "IFT_A", "IFT_B"}
    preys = sorted(
        [target for target in targets if target.protein_group in prey_groups],
        key=lambda target: (target.protein_group, target.record_id),
    )
    pairs = []
    for bait in baits:
        for prey in preys:
            requires_review = prey.requires_construct_review
            pairs.append(
                Pair(
                    pair_id=pair_id(bait.record_id, prey.record_id),
                    bait_id=bait.record_id,
                    prey_id=prey.record_id,
                    screen=f"future_full_{prey.protein_group.lower()}",
                    control_type="future_discovery",
                    rationale="Future full biological screen; not executable until scope review.",
                    executable=False,
                    requires_construct_review=requires_review,
                )
            )
    validate_pair_set(pairs)
    return pairs


def write_pair_tsv(path: Path, pairs: list[Pair], targets: list[Target]) -> None:
    by_id = targets_by_id(targets)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for pair in sorted(pairs, key=lambda item: item.pair_id):
        bait = by_id[pair.bait_id]
        prey = by_id[pair.prey_id]
        rows.append(
            {
                "pair_id": pair.pair_id,
                "screen": pair.screen,
                "bait_id": pair.bait_id,
                "bait_accession": bait.accession,
                "bait_name": bait.display_name,
                "prey_id": pair.prey_id,
                "prey_accession": prey.accession,
                "prey_name": prey.display_name,
                "prey_group": prey.protein_group,
                "control_type": pair.control_type,
                "executable": str(pair.executable),
                "requires_construct_review": str(pair.requires_construct_review),
                "alphapulldown_spec": pair.alphapulldown_spec(by_id),
                "rationale": pair.rationale,
            }
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_screen_definitions(path: Path, targets: list[Target]) -> None:
    payload = {
        "control_benchmark": {
            "description": "Small benchmark for AlphaPulldown validation.",
            "pairs": [pair.__dict__ for pair in control_pairs(targets)],
            "future_curated_negative_controls": [],
        },
        "targeted_transport": {
            "description": "DNAAF9 and DNAAF18 against verified IFT-B proteins.",
            "baits": ["HUMAN_DNAAF9", "HUMAN_DNAAF18"],
            "prey_group": "IFT_B",
            "pairs": [pair.__dict__ for pair in targeted_transport_pairs(targets)],
        },
        "future_full_screen": {
            "description": "Defined but not executed DNAAF x ODA/ODAD/IFT-A/IFT-B screen.",
            "pairs": [pair.__dict__ for pair in full_screen_pairs(targets)],
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def heavy_chain_review_rows(targets: list[Target]) -> list[dict[str, str]]:
    rows = []
    for target in sorted(targets, key=lambda item: item.record_id):
        if target.requires_construct_review:
            rows.append(
                {
                    "record_id": target.record_id,
                    "display_name": target.display_name,
                    "accession": target.accession,
                    "length": str(target.length),
                    "status": "deferred_requires_construct_review",
                    "reason": "Full-length axonemal dynein heavy chain; no arbitrary truncation.",
                }
            )
    return rows
