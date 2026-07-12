#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

usage() {
  cat <<'USAGE'
Usage: collect_results.sh [--env-file PATH] [--dry-run]

Collects lightweight outputs for transfer back to macOS: score tables, PAE files,
ranked structures, logs, provenance, and selected result pickles if configured.
USAGE
}

DRY_RUN=0
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

COLLECT_DIR="${COLLECT_DIR:-${REMOTE_PROJECT_ROOT}/results/collected/$(date -u +%Y%m%dT%H%M%SZ)}"
ensure_dir "${COLLECT_DIR}"

echo "Collecting selected outputs from ${OUTPUT_DIR} to ${COLLECT_DIR}"
PATTERNS=(
  "*.csv"
  "*.tsv"
  "*.json"
  "ranked_*.pdb"
  "ranked_*.cif"
  "ranked_*.mmcif"
  "pae*.png"
  "pae*.json"
  "ranking_debug.json"
  "*.log"
)

for pattern in "${PATTERNS[@]}"; do
  if [[ "${DRY_RUN}" == "1" ]]; then
    echo "DRY RUN: find ${OUTPUT_DIR} -name ${pattern}"
  else
    find "${OUTPUT_DIR}" -name "${pattern}" -type f -exec cp --parents {} "${COLLECT_DIR}" \;
  fi
done

if [[ -d "${LOG_DIR}" && "${DRY_RUN}" != "1" ]]; then
  mkdir -p "${COLLECT_DIR}/logs"
  cp -R "${LOG_DIR}/." "${COLLECT_DIR}/logs/"
fi

if [[ -d "${PROVENANCE_DIR}" && "${DRY_RUN}" != "1" ]]; then
  mkdir -p "${COLLECT_DIR}/provenance"
  cp -R "${PROVENANCE_DIR}/." "${COLLECT_DIR}/provenance/"
fi

echo "Collection directory: ${COLLECT_DIR}"

