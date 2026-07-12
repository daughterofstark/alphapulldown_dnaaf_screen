#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

usage() {
  cat <<'USAGE'
Usage: run_feature_generation.sh [--env-file PATH] [--dry-run] [--skip-existing]

Runs or dry-runs the remote feature generation stage. This stage prepares
per-protein MSAs/templates/features and does not run structure prediction.
USAGE
}

DRY_RUN=0
SKIP_EXISTING="${SKIP_EXISTING:-1}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      REMOTE_ENV_FILE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --skip-existing)
      SKIP_EXISTING=1
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

load_remote_env "${REMOTE_ENV_FILE}"
require_linux
ensure_dir "${FEATURE_DIR:?FEATURE_DIR must be set}"
ensure_dir "${LOG_DIR:?LOG_DIR must be set}"
ensure_dir "${TMP_DIR:?TMP_DIR must be set}"
ensure_dir "${PROVENANCE_DIR:?PROVENANCE_DIR must be set}"

if [[ "${FEATURE_MODE:-localdb}" == "localdb" && ! -d "${DATABASES_DIR:-}" ]]; then
  echo "FEATURE_MODE=localdb requires DATABASES_DIR to exist." >&2
  exit 2
fi

RUN_ID="${RUN_ID:-$(date -u +feature-%Y%m%dT%H%M%SZ)}"
COMMAND_FILE="${PROVENANCE_DIR}/${RUN_ID}/feature_generation_command.txt"
mkdir -p "$(dirname "${COMMAND_FILE}")"

ARGS=(--config "${REMOTE_ENV_FILE}" feature-command)
if [[ "${DRY_RUN}" == "1" ]]; then ARGS+=(--dry-run); fi
remote_python -m alphapulldown_dnaaf_screen.remote_cli "${ARGS[@]}" | tee "${COMMAND_FILE}"

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "Feature-generation dry run complete. No jobs submitted."
  exit 0
fi

if [[ "${SKIP_EXISTING}" == "1" ]]; then
  echo "SKIP_EXISTING=1: remote workflow should reuse existing MSAs/features where configured."
fi

SNAKEMAKE_COMMAND="$(cat "${COMMAND_FILE}")"
bash -lc "${SNAKEMAKE_COMMAND}" 2>&1 | tee "${LOG_DIR}/${RUN_ID}.feature_generation.log"
