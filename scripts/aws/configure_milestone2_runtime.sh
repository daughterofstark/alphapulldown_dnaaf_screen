#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: configure_milestone2_runtime.sh [--force]

Writes config/remote/paths.env for the validated AWS Docker-native Milestone 2
runtime. It does not invoke Docker, contact MMseqs2, generate features, or run
predictions.
USAGE
}

FORCE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd -P)"
TEMPLATE="${PROJECT_ROOT}/config/benchmarks/milestone2_aws.example.env"
DESTINATION="${PROJECT_ROOT}/config/remote/paths.env"

[[ -f "${TEMPLATE}" ]] || { echo "Missing template: ${TEMPLATE}" >&2; exit 2; }
if [[ -e "${DESTINATION}" && "${FORCE}" != "1" ]]; then
  echo "Refusing to overwrite existing configuration: ${DESTINATION}" >&2
  echo "Review it, remove it, or rerun with --force." >&2
  exit 2
fi

TMP_FILE="$(mktemp "${DESTINATION}.tmp.XXXXXX")"
trap 'rm -f "${TMP_FILE}"' EXIT
sed "s|__PROJECT_ROOT__|${PROJECT_ROOT}|g" "${TEMPLATE}" > "${TMP_FILE}"
mv "${TMP_FILE}" "${DESTINATION}"
trap - EXIT

echo "Wrote benchmark-only AWS runtime configuration: ${DESTINATION}"
echo "Next safe command: bash scripts/aws/run_milestone2_stage.sh --stage features --dry-run"
