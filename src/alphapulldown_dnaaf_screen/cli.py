"""Command-line interface for CPU-side AlphaPulldown input preparation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .fasta import write_fastas
from .provenance import Provenance
from .samplesheets import write_alphapulldown_inputs, write_heavy_chain_review_table
from .screens import heavy_chain_review_rows, write_screen_definitions
from .targets import load_targets, write_validated_manifest
from .validation import ValidationError

DEFAULT_VERIFIED_JSON = Path("data/processed/uniprot/targets_uniprot_verified.json")
DEFAULT_RAW_DIR = Path("data/raw/uniprot")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional config file to checksum.",
    )
    parser.add_argument("--verified-json", type=Path, default=DEFAULT_VERIFIED_JSON)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--provenance-dir", type=Path, default=Path("data/processed/provenance"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-targets", help="Validate verified UniProt targets.")
    validate.add_argument("--output-dir", type=Path, default=Path("data/processed/targets"))

    fastas = subparsers.add_parser(
        "write-fastas",
        help="Write deterministic canonical FASTA files.",
    )
    fastas.add_argument("--output-dir", type=Path, default=Path("data/processed/fasta"))

    screens = subparsers.add_parser(
        "build-screens",
        help="Write machine-readable screen definitions.",
    )
    screens.add_argument("--output-dir", type=Path, default=Path("data/processed/screens"))

    ap = subparsers.add_parser("prepare-alphapulldown", help="Write AlphaPulldown input files.")
    ap.add_argument("--output-dir", type=Path, default=Path("data/processed/alphapulldown"))
    return parser


def _provenance(args: argparse.Namespace) -> Provenance:
    inputs = [args.verified_json]
    if args.raw_dir.exists():
        inputs.extend(sorted(path for path in args.raw_dir.glob("*.json")))
    return Provenance(
        command=args.command,
        cwd=Path.cwd(),
        input_paths=inputs,
        config_path=args.config,
    )


def validate_targets_command(args: argparse.Namespace) -> int:
    targets = load_targets(args.verified_json, raw_dir=args.raw_dir, require_sequences=True)
    artifacts = write_validated_manifest(targets, args.output_dir)
    provenance = _provenance(args)
    for artifact in artifacts:
        provenance.add_artifact(artifact)
    provenance.write(args.provenance_dir / "validate_targets.json")
    groups: dict[str, int] = {}
    for target in targets:
        groups[target.protein_group] = groups.get(target.protein_group, 0) + 1
    print(json.dumps({"target_count": len(targets), "groups": groups}, sort_keys=True))
    return 0


def write_fastas_command(args: argparse.Namespace) -> int:
    targets = load_targets(args.verified_json, raw_dir=args.raw_dir, require_sequences=True)
    artifacts = write_fastas(targets, args.output_dir)
    provenance = _provenance(args)
    for artifact in artifacts:
        provenance.add_artifact(artifact)
    provenance.write(args.provenance_dir / "write_fastas.json")
    print(f"wrote {len(artifacts)} FASTA artifacts to {args.output_dir}")
    return 0


def build_screens_command(args: argparse.Namespace) -> int:
    targets = load_targets(args.verified_json, raw_dir=args.raw_dir, require_sequences=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    screen_path = args.output_dir / "screen_definitions.json"
    write_screen_definitions(screen_path, targets)
    review_path = args.output_dir / "heavy_chain_review.tsv"
    write_heavy_chain_review_table(review_path, heavy_chain_review_rows(targets))
    provenance = _provenance(args)
    for artifact in [screen_path, review_path]:
        provenance.add_artifact(artifact)
    provenance.write(args.provenance_dir / "build_screens.json")
    print(f"wrote screen definitions to {args.output_dir}")
    return 0


def prepare_alphapulldown_command(args: argparse.Namespace) -> int:
    targets = load_targets(args.verified_json, raw_dir=args.raw_dir, require_sequences=True)
    artifacts = write_alphapulldown_inputs(args.output_dir, targets)
    provenance = _provenance(args)
    for artifact in artifacts:
        provenance.add_artifact(artifact)
    provenance.write(args.provenance_dir / "prepare_alphapulldown.json")
    print(f"wrote {len(artifacts)} AlphaPulldown input artifacts to {args.output_dir}")
    return 0


COMMANDS = {
    "validate-targets": validate_targets_command,
    "write-fastas": write_fastas_command,
    "build-screens": build_screens_command,
    "prepare-alphapulldown": prepare_alphapulldown_command,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except ValidationError as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
