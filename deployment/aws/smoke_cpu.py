"""No-data CPU contract test for the candidate AlphaPulldown image."""

from __future__ import annotations

import importlib.metadata
import subprocess
import sys


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

    subprocess.run(["create_individual_features.py", "--help"], check=True)
    print(f"CPU image smoke test passed: alphapulldown={installed_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
