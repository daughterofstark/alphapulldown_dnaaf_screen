"""CLI helpers used by remote shell scripts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .remote import (
    create_run_provenance,
    feature_generation_command,
    load_remote_config,
    missing_features,
    prediction_command,
    shell_join,
    stable_run_id,
    validate_accession_files,
)
from .validation import ValidationError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Remote paths.env file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    feature = subparsers.add_parser("feature-command")
    feature.add_argument("--dry-run", action="store_true")

    prediction = subparsers.add_parser("prediction-command")
    prediction.add_argument("--screen", choices=["controls", "transport", "full"], required=True)
    prediction.add_argument("--executor", choices=["desktop", "slurm"], default="desktop")
    prediction.add_argument("--dry-run", action="store_true")

    coverage = subparsers.add_parser("check-feature-coverage")
    coverage.add_argument("--screen", choices=["controls", "transport", "full"], required=True)
    coverage.add_argument("--json", action="store_true")
    return parser


def feature_command(args: argparse.Namespace) -> int:
    config = load_remote_config(args.config)
    validate_accession_files(config)
    command = feature_generation_command(config, dry_run=args.dry_run)
    run_id = stable_run_id("feature")
    create_run_provenance(
        config=config,
        run_id=run_id,
        command=command,
        input_paths=[config.fasta_manifest, config.feature_config],
    )
    print(shell_join(command))
    return 0


def prediction_command_action(args: argparse.Namespace) -> int:
    config = load_remote_config(args.config)
    missing = missing_features(config, args.screen)
    if missing:
        missing_preview = "\n".join(str(path) for path in missing[:20])
        raise ValidationError(
            f"Missing {len(missing)} required feature files for screen {args.screen}:\n"
            f"{missing_preview}"
        )
    command = prediction_command(
        config,
        screen=args.screen,
        dry_run=args.dry_run,
        executor=args.executor,
    )
    run_id = stable_run_id("prediction", screen=args.screen)
    create_run_provenance(
        config=config,
        run_id=run_id,
        command=command,
        input_paths=[config.prediction_config, config.fasta_manifest],
    )
    print(shell_join(command))
    return 0


def check_feature_coverage(args: argparse.Namespace) -> int:
    config = load_remote_config(args.config)
    missing = missing_features(config, args.screen)
    payload = {
        "screen": args.screen,
        "missing_count": len(missing),
        "missing": [str(path) for path in missing],
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"screen={args.screen}")
        print(f"missing_count={len(missing)}")
        for path in missing:
            print(path)
    return 1 if missing else 0


COMMANDS = {
    "feature-command": feature_command,
    "prediction-command": prediction_command_action,
    "check-feature-coverage": check_feature_coverage,
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
