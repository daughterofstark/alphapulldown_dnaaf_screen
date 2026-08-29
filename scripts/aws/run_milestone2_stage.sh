#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: run_milestone2_stage.sh --stage features|predict [--scenario ID] [--dry-run] [--config PATH]

Runs one isolated Milestone 2 stage inside the validated local Docker image.
The host Docker daemon launches the image once; the container never invokes
Docker, Apptainer, Singularity, or Snakemake. --dry-run is required for the
first invocation on any host.
USAGE
}

STAGE=""
DRY_RUN=0
CONFIG_PATH=""
SCENARIO=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --stage) STAGE="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --scenario) SCENARIO="${2:-}"; shift 2 ;;
    --config) CONFIG_PATH="${2:-}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "${STAGE}" in
  features|predict) ;;
  *) echo "--stage must be features or predict" >&2; exit 2 ;;
esac
if [[ -n "${SCENARIO}" && "${STAGE}" != "predict" ]]; then
  echo "--scenario is supported only with --stage predict" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd -P)"
CONFIG_PATH="${CONFIG_PATH:-${PROJECT_ROOT}/config/remote/paths.env}"
[[ -f "${CONFIG_PATH}" ]] || {
  echo "Missing runtime configuration: ${CONFIG_PATH}" >&2
  echo "Run bash scripts/aws/configure_milestone2_runtime.sh first." >&2
  exit 2
}
CONFIG_PATH="$(cd "$(dirname "${CONFIG_PATH}")" && pwd -P)/$(basename "${CONFIG_PATH}")"

set -a
# shellcheck disable=SC1090
source "${CONFIG_PATH}"
set +a

[[ "${CONTAINER_RUNTIME:-}" == "docker-native" ]] || {
  echo "CONTAINER_RUNTIME must be docker-native." >&2; exit 2;
}
[[ "${REMOTE_PROJECT_ROOT:-}" == "${PROJECT_ROOT}" ]] || {
  echo "REMOTE_PROJECT_ROOT must match this checkout: ${PROJECT_ROOT}" >&2; exit 2;
}
[[ "${NATIVE_IMAGE_REFERENCE:-}" ]] || {
  echo "NATIVE_IMAGE_REFERENCE must name the validated local Docker image." >&2; exit 2;
}
command -v docker >/dev/null || { echo "Docker is required." >&2; exit 2; }
if [[ "${STAGE}" == "predict" ]]; then
  command -v nvidia-smi >/dev/null || { echo "Prediction requires nvidia-smi." >&2; exit 2; }
  [[ -n "${BACKEND_WEIGHTS_DIR:-}" ]] || {
    echo "Prediction requires BACKEND_WEIGHTS_DIR to name the AlphaFold2 model-weights directory." >&2
    exit 2
  }
  [[ -d "${BACKEND_WEIGHTS_DIR}" ]] || {
    echo "Prediction model-weights directory does not exist on the host: ${BACKEND_WEIGHTS_DIR}" >&2
    exit 2
  }
  BACKEND_WEIGHTS_DIR="$(cd "${BACKEND_WEIGHTS_DIR}" && pwd -P)"
fi

IMAGE_ID="$(docker image inspect --format '{{.Id}}' "${NATIVE_IMAGE_REFERENCE}" 2>/dev/null)" || {
  echo "Validated Docker image is unavailable: ${NATIVE_IMAGE_REFERENCE}" >&2; exit 2;
}
[[ "${IMAGE_ID}" == "${ALPHAPULLDOWN_DERIVED_IMAGE_DIGEST:-}" ]] || {
  echo "Docker image ID does not match ALPHAPULLDOWN_DERIVED_IMAGE_DIGEST." >&2
  echo "Expected: ${ALPHAPULLDOWN_DERIVED_IMAGE_DIGEST:-unset}" >&2
  echo "Found:    ${IMAGE_ID}" >&2
  exit 2
}

mkdir -p "${TMP_DIR}/docker-home"
DOCKER_COMMAND=(
  docker run --rm --init --platform linux/amd64
  --workdir "${PROJECT_ROOT}"
  --user "$(id -u):$(id -g)"
  --env "HOME=${TMP_DIR}/docker-home"
  --env "XDG_CACHE_HOME=${TMP_DIR}/docker-home/.cache"
  --env "PYTHONPATH=${PROJECT_ROOT}/src"
  --env "ALPHAPULLDOWN_SOURCE_REVISION=${ALPHAPULLDOWN_EXPECTED_REVISION}"
  --volume "${PROJECT_ROOT}:${PROJECT_ROOT}"
)
if [[ "${STAGE}" == "predict" ]]; then
  DOCKER_COMMAND+=(
    --gpus all
    --volume "${BACKEND_WEIGHTS_DIR}:${BACKEND_WEIGHTS_DIR}:ro"
  )
fi
DOCKER_COMMAND+=(
  "${NATIVE_IMAGE_REFERENCE}"
  python -m alphapulldown_dnaaf_screen.native_cli
  --config "${CONFIG_PATH}" "${STAGE}"
)
if [[ -n "${SCENARIO}" ]]; then
  DOCKER_COMMAND+=(--scenario "${SCENARIO}")
fi
if [[ "${DRY_RUN}" == "1" ]]; then
  DOCKER_COMMAND+=(--dry-run)
fi

printf 'Executing:'
printf ' %q' "${DOCKER_COMMAND[@]}"
printf '\n'
"${DOCKER_COMMAND[@]}"
