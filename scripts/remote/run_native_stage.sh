#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

usage() {
  cat <<'USAGE'
Usage: run_native_stage.sh --stage features|predict [--env-file PATH] [--dry-run]

Runs one AlphaPulldown stage directly inside the Docker-native runtime image.
It never launches Snakemake, Apptainer, Singularity, Docker, or another container.
USAGE
}

STAGE=""
DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --stage)
      STAGE="$2"
      shift 2
      ;;
    --env-file)
      REMOTE_ENV_FILE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "${STAGE}" in
  features|predict) ;;
  *)
    echo "--stage must be features or predict" >&2
    exit 2
    ;;
esac

load_remote_env "${REMOTE_ENV_FILE}"
require_linux
if [[ "${CONTAINER_RUNTIME:-}" != "docker-native" ]]; then
  echo "run_native_stage.sh requires CONTAINER_RUNTIME=docker-native." >&2
  exit 2
fi

ensure_dir "${FEATURE_DIR:?FEATURE_DIR must be set}"
ensure_dir "${OUTPUT_DIR:?OUTPUT_DIR must be set}"
ensure_dir "${LOG_DIR:?LOG_DIR must be set}"
ensure_dir "${TMP_DIR:?TMP_DIR must be set}"
ensure_dir "${PROVENANCE_DIR:?PROVENANCE_DIR must be set}"

ARGS=(--config "${REMOTE_ENV_FILE}" "${STAGE}")
if [[ "${DRY_RUN}" == "1" ]]; then
  ARGS+=(--dry-run)
fi

RUN_LABEL="$(date -u +native-${STAGE}-%Y%m%dT%H%M%SZ)"
remote_python -m alphapulldown_dnaaf_screen.native_cli "${ARGS[@]}" \
  2>&1 | tee "${LOG_DIR}/${RUN_LABEL}.log"
