"""Provenance records for generated CPU-side preparation artifacts."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from alphapulldown_dnaaf_screen import __version__


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_metadata(cwd: Path) -> dict[str, str | bool]:
    def run_git(args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "unknown"

    status = run_git(["status", "--short"])
    return {
        "commit": run_git(["rev-parse", "HEAD"]),
        "branch": run_git(["branch", "--show-current"]),
        "dirty": bool(status),
    }


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    sha256: str


@dataclass
class Provenance:
    command: str
    cwd: Path
    input_paths: list[Path]
    config_path: Path | None = None
    artifacts: list[ArtifactRecord] = field(default_factory=list)

    def add_artifact(self, path: Path) -> None:
        self.artifacts.append(ArtifactRecord(path=str(path), sha256=sha256_file(path)))

    def write(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        inputs = [{"path": str(path), "sha256": sha256_file(path)} for path in self.input_paths]
        config: dict[str, Any] | None = None
        if self.config_path:
            config = {"path": str(self.config_path), "sha256": sha256_file(self.config_path)}
        payload = {
            "utc_timestamp": dt.datetime.now(dt.UTC).isoformat(),
            "command": self.command,
            "package_version": __version__,
            "git": git_metadata(self.cwd),
            "inputs": inputs,
            "config": config,
            "artifacts": [record.__dict__ for record in self.artifacts],
        }
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
