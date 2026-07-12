#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

usage() {
  cat <<'USAGE'
Usage: run_prediction.sh --screen controls|transport [--executor desktop|slurm] [--env-file PATH] [--dry-run]

Runs or dry-runs GPU prediction after precomputed feature files exist.
The full screen is intentionally deferred and rejected by default.
USAGE
}

SCREEN=""
EXECUTOR="desktop"
DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --screen)
      SCREEN="$2"
      shift 2
      ;;
    --executor)
      EXECUTOR="$2"
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

if [[ -z "${SCREEN}" ]]; then
  echo "--screen is required" >&2
  usage >&2
  exit 2
fi

load_remote_env "${REMOTE_ENV_FILE}"
require_linux
ensure_dir "${OUTPUT_DIR:?OUTPUT_DIR must be set}"
ensure_dir "${LOG_DIR:?LOG_DIR must be set}"
ensure_dir "${PROVENANCE_DIR:?PROVENANCE_DIR must be set}"

RUN_ID="${RUN_ID:-$(date -u +prediction-${SCREEN}-%Y%m%dT%H%M%SZ)}"
COMMAND_FILE="${PROVENANCE_DIR}/${RUN_ID}/prediction_command.txt"
mkdir -p "$(dirname "${COMMAND_FILE}")"

ARGS=(--config "${REMOTE_ENV_FILE}" prediction-command --screen "${SCREEN}" --executor "${EXECUTOR}")
if [[ "${DRY_RUN}" == "1" ]]; then ARGS+=(--dry-run); fi
remote_python -m alphapulldown_dnaaf_screen.remote_cli "${ARGS[@]}" | tee "${COMMAND_FILE}"

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "Prediction dry run complete. No jobs submitted."
  exit 0
fi

SNAKEMAKE_COMMAND="$(cat "${COMMAND_FILE}")"
bash -lc "${SNAKEMAKE_COMMAND}" 2>&1 | tee "${LOG_DIR}/${RUN_ID}.prediction.log"
