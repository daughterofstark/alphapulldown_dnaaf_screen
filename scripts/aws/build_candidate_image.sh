#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <candidate-image-reference>" >&2
  exit 2
fi

IMAGE_REFERENCE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

command -v docker >/dev/null || {
  echo "Docker is required to build the AWS candidate image." >&2
  exit 1
}

cd "${PROJECT_ROOT}"
docker buildx build \
  --platform linux/amd64 \
  --file deployment/aws/Dockerfile \
  --tag "${IMAGE_REFERENCE}" \
  --load \
  .

docker run --rm --platform linux/amd64 "${IMAGE_REFERENCE}" \
  python /opt/alphapulldown-runtime/smoke_cpu.py

RECORDS_DIR="${PROJECT_ROOT}/results/runtime/candidate-image"
mkdir -p "${RECORDS_DIR}"
CONTAINER_ID="$(docker create "${IMAGE_REFERENCE}")"
cleanup() {
  docker rm -f "${CONTAINER_ID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT
docker cp "${CONTAINER_ID}:/opt/alphapulldown-runtime/conda-explicit.txt" \
  "${RECORDS_DIR}/conda-explicit.txt"
docker cp "${CONTAINER_ID}:/opt/alphapulldown-runtime/pip-freeze.txt" \
  "${RECORDS_DIR}/pip-freeze.txt"
docker image inspect "${IMAGE_REFERENCE}" \
  --format '{{.Id}} {{.Architecture}}' > "${RECORDS_DIR}/image-id.txt"

echo "Candidate image passed the CPU smoke test: ${IMAGE_REFERENCE}"
echo "Resolved dependency records: ${RECORDS_DIR}"
echo "Do not push or use it for biological work until the GPU smoke test passes."
