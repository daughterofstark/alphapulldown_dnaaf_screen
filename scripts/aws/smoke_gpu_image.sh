#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <candidate-image-reference>" >&2
  exit 2
fi

IMAGE_REFERENCE="$1"
command -v docker >/dev/null || {
  echo "Docker is required for the GPU image smoke test." >&2
  exit 1
}
command -v nvidia-smi >/dev/null || {
  echo "nvidia-smi is required. Run this only on an AWS NVIDIA GPU instance." >&2
  exit 1
}

nvidia-smi
docker run --rm --gpus all "${IMAGE_REFERENCE}" \
  python /opt/alphapulldown-runtime/smoke_gpu.py

echo "Candidate image passed the GPU smoke test. No biological data was used."
