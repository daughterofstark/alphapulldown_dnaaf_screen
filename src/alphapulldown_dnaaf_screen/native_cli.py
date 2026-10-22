"""Direct Docker-native AlphaPulldown runner for the Milestone 2 benchmark."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .native_runtime import (
    execute_commands,
    load_native_config,
    plan_native_run,
    runtime_identity,
    shell_join,
    validate_host_runtime,
    validate_runtime_identity,
    write_native_provenance,
)
from .validation import ValidationError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("features", "predict"):
        stage = subparsers.add_parser(name)
        stage.add_argument("--dry-run", action="store_true")
        if name == "predict":
            stage.add_argument(
                "--scenario",
                help="Run one permitted Milestone 2 scenario instead of all eight.",
            )
    subparsers.add_parser("validate")
    subparsers.add_parser("preflight")
    return parser


def run(args: argparse.Namespace) -> int:
    config = load_native_config(args.config)
    if args.command == "validate":
        print(
            "Docker-native Milestone 2 configuration valid: "
            f"stage={config.execution_stage}, feature_mode={config.feature_mode}"
        )
        return 0
    if args.command == "preflight":
        stage_command = "features" if config.execution_stage == "cpu" else "predict"
        validate_host_runtime(config, command=stage_command, dry_run=False)
        identity = runtime_identity(config)
        validate_runtime_identity(config, identity)
        plan_native_run(config, command=stage_command)
        print(
            "Docker-native runtime preflight passed: "
            f"stage={config.execution_stage}, command={stage_command}"
        )
        return 0

    dry_run = bool(args.dry_run)
    validate_host_runtime(config, command=args.command, dry_run=dry_run)
    run_id, commands = plan_native_run(
        config, command=args.command, scenario_id=getattr(args, "scenario", None)
    )
    identity = runtime_identity(config)
    validate_runtime_identity(config, identity, allow_uninstalled=dry_run)
    write_native_provenance(
        config,
        run_id=run_id,
        stage_command=args.command,
        commands=commands,
        dry_run=dry_run,
        status="dry-run" if dry_run else "started",
        identity=identity,
    )
    for command in commands:
        print(shell_join(command))
    if not dry_run:
        try:
            execute_commands(commands)
        except subprocess.CalledProcessError as exc:
            write_native_provenance(
                config,
                run_id=run_id,
                stage_command=args.command,
                commands=commands,
                dry_run=False,
                status=f"failed-exit-{exc.returncode}",
                identity=identity,
            )
            raise ValidationError(
                f"AlphaPulldown command failed with exit code {exc.returncode}: "
                f"{shell_join([str(item) for item in exc.cmd])}"
            ) from exc
        else:
            write_native_provenance(
                config,
                run_id=run_id,
                stage_command=args.command,
                commands=commands,
                dry_run=False,
                status="completed",
                identity=identity,
            )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except ValidationError as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
