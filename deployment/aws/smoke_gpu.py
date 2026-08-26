"""No-data GPU contract test for the candidate AlphaPulldown image."""

from __future__ import annotations

import importlib.metadata
import subprocess
import sys


def main() -> int:
    import jax
    import alphapulldown.scripts.run_structure_prediction  # noqa: F401

    if importlib.metadata.version("alphapulldown") != "2.5.0":
        raise RuntimeError("AlphaPulldown version does not match the candidate image contract")
    if jax.__version__ != "0.5.3":
        raise RuntimeError(f"Expected JAX 0.5.3, found {jax.__version__}")
    devices = jax.local_devices(backend="gpu")
    if not devices:
        raise RuntimeError("JAX could not see an NVIDIA GPU")
    subprocess.run(["run_structure_prediction.py", "--help"], check=True)
    print(f"GPU image smoke test passed: devices={devices}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
