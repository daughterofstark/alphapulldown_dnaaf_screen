"""No-data CPU contract test for the candidate AlphaPulldown image."""

from __future__ import annotations

import importlib.metadata
import subprocess
import sys


def verify_help_command(command: list[str], expected_flag: str) -> None:
    """Accept AlphaPulldown's observed non-zero help exit only with real help text."""
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    print(result.stdout, end="")
    if result.returncode not in (0, 1) or expected_flag not in result.stdout:
        raise RuntimeError(
            f"CLI help contract failed for {' '.join(command)}: exit={result.returncode}"
        )


def main() -> int:
    expected_version = "2.5.0"
    installed_version = importlib.metadata.version("alphapulldown")
    if installed_version != expected_version:
        raise RuntimeError(
            f"Expected AlphaPulldown {expected_version}, found {installed_version}"
        )

    import alphafold  # noqa: F401
    import alphapulldown  # noqa: F401
    import colabfold  # noqa: F401
    import jax  # noqa: F401
    import openmm  # noqa: F401
    import alphapulldown.scripts.create_individual_features  # noqa: F401

    verify_help_command(
        ["create_individual_features.py", "--help"],
        "--use_mmseqs2",
    )
    print(f"CPU image smoke test passed: alphapulldown={installed_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
