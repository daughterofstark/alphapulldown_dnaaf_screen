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

HAS_ENV_MANAGER=0
if command -v mamba >/dev/null 2>&1; then
  ok "Mamba" "$(mamba --version | head -1)"
  HAS_ENV_MANAGER=1
else
  report "Mamba" "not found"
fi

if command -v conda >/dev/null 2>&1; then
  ok "Conda" "$(conda --version)"
  HAS_ENV_MANAGER=1
else
  report "Conda" "not found"
fi

if [[ "${HAS_ENV_MANAGER}" == "0" ]]; then
  fail "Conda/Mamba" "neither conda nor mamba found"
fi

if command -v python3 >/dev/null 2>&1; then ok "Python" "$(python3 --version)"
else fail "Python" "python3 not found"; fi

if command -v snakemake >/dev/null 2>&1; then ok "Snakemake" "$(snakemake --version)"
else fail "Snakemake" "not found"; fi

if python3 -c 'import alphapulldown_input_parser; print("alphapulldown-input-parser importable")' >/tmp/ap_parser.$$ 2>/tmp/ap_parser_err.$$; then
  ok "Input parser" "$(cat /tmp/ap_parser.$$)"
else
  fail "Input parser" "$(cat /tmp/ap_parser_err.$$ 2>/dev/null || echo not importable)"
fi

if python3 -c 'import alphapulldown' >/tmp/ap_version.$$ 2>/tmp/ap_err.$$; then
  ok "AlphaPulldown Python package" "importable in orchestration environment"
else
  report "AlphaPulldown Python package" "not importable in orchestration environment; expected for containerized AlphaPulldownSnakemake runtime"
fi
rm -f /tmp/ap_parser.$$ /tmp/ap_parser_err.$$ /tmp/ap_version.$$ /tmp/ap_err.$$

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

if [[ -f "${AP_WORKFLOW_DIR:-}/workflow/Snakefile" ]]; then ok "Workflow Snakefile" "${AP_WORKFLOW_DIR}/workflow/Snakefile"
else fail "Workflow Snakefile" "missing: ${AP_WORKFLOW_DIR:-unset}/workflow/Snakefile"; fi

if [[ -n "${SNAKEMAKE_PROFILE:-}" ]]; then
  if [[ -d "${SNAKEMAKE_PROFILE}" ]]; then ok "Desktop profile" "${SNAKEMAKE_PROFILE}"
  else fail "Desktop profile" "configured but missing: ${SNAKEMAKE_PROFILE}"; fi
else
  report "Desktop profile" "not configured; local single-node execution will use --cores"
fi

if [[ -n "${SLURM_PROFILE:-}" ]]; then
  if [[ -d "${SLURM_PROFILE}" ]]; then ok "SLURM profile" "${SLURM_PROFILE}"
  else fail "SLURM profile" "configured but missing: ${SLURM_PROFILE}"; fi
else
  report "SLURM profile" "not configured"
fi

if [[ -f "${FASTA_MANIFEST:-}" ]]; then ok "FASTA manifest" "${FASTA_MANIFEST}"
else fail "FASTA manifest" "missing: ${FASTA_MANIFEST:-unset}"; fi

if [[ "${FAILURES}" -gt 0 ]]; then
  echo "Blocking remote environment failures: ${FAILURES}" >&2
  exit 2
fi

echo "Remote environment validation passed."
