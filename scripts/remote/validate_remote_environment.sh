#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

usage() {
  cat <<'USAGE'
Usage: validate_remote_environment.sh [--env-file PATH]

Reports OS, Conda/Mamba, Python, Snakemake, AlphaPulldown, CUDA/GPU, database,
and path readiness. Returns non-zero on blocking failures.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      REMOTE_ENV_FILE="$2"
      shift 2
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

FAILURES=0
report() { printf '%-32s %s\n' "$1" "$2"; }
fail() { report "$1" "FAIL: $2"; FAILURES=$((FAILURES + 1)); }
ok() { report "$1" "OK: $2"; }

report "OS" "$(uname -srm)"
report "Architecture" "$(uname -m)"

if command -v mamba >/dev/null 2>&1; then ok "Mamba" "$(mamba --version | head -1)"
else fail "Mamba" "not found"; fi

if command -v conda >/dev/null 2>&1; then ok "Conda" "$(conda --version)"
else fail "Conda" "not found"; fi

if command -v python3 >/dev/null 2>&1; then ok "Python" "$(python3 --version)"
else fail "Python" "python3 not found"; fi

if command -v snakemake >/dev/null 2>&1; then ok "Snakemake" "$(snakemake --version)"
else fail "Snakemake" "not found"; fi

if python3 -c 'import alphapulldown; print(getattr(alphapulldown, "__version__", "unknown"))' >/tmp/ap_version.$$ 2>/tmp/ap_err.$$; then
  ok "AlphaPulldown" "$(cat /tmp/ap_version.$$)"
else
  fail "AlphaPulldown" "$(cat /tmp/ap_err.$$ 2>/dev/null || echo not importable)"
fi
rm -f /tmp/ap_version.$$ /tmp/ap_err.$$

if command -v nvidia-smi >/dev/null 2>&1; then
  ok "nvidia-smi" "$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | paste -sd ';' -)"
  report "CUDA" "$(nvidia-smi | sed -n 's/.*CUDA Version: \([^ ]*\).*/\1/p' | head -1)"
else
  fail "nvidia-smi" "not found"
fi

if [[ "${FEATURE_MODE:-localdb}" == "localdb" ]]; then
  if [[ -d "${DATABASES_DIR:-}" ]]; then ok "Databases directory" "${DATABASES_DIR}"
  else fail "Databases directory" "missing or not a directory: ${DATABASES_DIR:-unset}"; fi
fi

for path_var in REMOTE_PROJECT_ROOT FASTA_DIR ALPHAPULLDOWN_INPUT_DIR FEATURE_DIR OUTPUT_DIR LOG_DIR TMP_DIR PROVENANCE_DIR; do
  value="${!path_var:-}"
  if [[ -z "${value}" ]]; then
    fail "${path_var}" "unset"
  else
    mkdir -p "${value}" 2>/dev/null || true
    if [[ -e "${value}" && -w "${value}" ]]; then ok "${path_var}" "${value}"
    else fail "${path_var}" "not writable or missing: ${value}"; fi
  fi
done

if [[ -f "${FASTA_MANIFEST:-}" ]]; then ok "FASTA manifest" "${FASTA_MANIFEST}"
else fail "FASTA manifest" "missing: ${FASTA_MANIFEST:-unset}"; fi

if [[ "${FAILURES}" -gt 0 ]]; then
  echo "Blocking remote environment failures: ${FAILURES}" >&2
  exit 2
fi

echo "Remote environment validation passed."

