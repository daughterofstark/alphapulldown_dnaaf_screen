"""No-data GPU contract test for the candidate AlphaPulldown image."""

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
    import alphapulldown.scripts.run_structure_prediction  # noqa: F401
    import jax

    if importlib.metadata.version("alphapulldown") != "2.5.0":
        raise RuntimeError("AlphaPulldown version does not match the candidate image contract")
    if jax.__version__ != "0.5.3":
        raise RuntimeError(f"Expected JAX 0.5.3, found {jax.__version__}")
    devices = jax.local_devices(backend="gpu")
    if not devices:
        raise RuntimeError("JAX could not see an NVIDIA GPU")
    verify_help_command(
        ["run_structure_prediction.py", "--help"],
        "--output_directory",
    )
    print(f"GPU image smoke test passed: devices={devices}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
