#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

usage() {
  cat <<'USAGE'
Usage: bootstrap_remote_environment.sh [--env-file PATH] [--dry-run]

Deploys the official AlphaPulldownSnakemake workflow and records environment versions.
Does not vendor AlphaPulldown source into this repository.
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

case "$(uname -m)" in
  x86_64|aarch64) ;;
  *)
    echo "Unsupported CPU architecture: $(uname -m)" >&2
    exit 2
    ;;
esac

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi is required for the GPU inference host." >&2
  exit 2
fi

if ! command -v apptainer >/dev/null 2>&1; then
  echo "Apptainer is required for the pinned AlphaPulldownSnakemake container runtime." >&2
  exit 2
fi

if command -v mamba >/dev/null 2>&1; then
  ENV_MANAGER="mamba"
elif command -v conda >/dev/null 2>&1; then
  ENV_MANAGER="conda"
else
  echo "Either mamba or conda must be available on the remote host." >&2
  exit 2
fi

AP_SNAKEMAKE_VERSION="${AP_SNAKEMAKE_VERSION:-2.5.0}"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-snake}"
AP_WORKFLOW_DIR="${AP_WORKFLOW_DIR:?AP_WORKFLOW_DIR must be set}"
PROVENANCE_DIR="${PROVENANCE_DIR:?PROVENANCE_DIR must be set}"
SNAKEDEPLOY_BIN="${SNAKEDEPLOY_BIN:-snakedeploy}"
RUN_ID="bootstrap-$(date -u +%Y%m%dT%H%M%SZ)"
BOOTSTRAP_PROVENANCE="${PROVENANCE_DIR}/${RUN_ID}"
ensure_dir "${BOOTSTRAP_PROVENANCE}"

echo "Remote host: $(hostname)"
echo "Linux: $(uname -a)"
echo "Architecture: $(uname -m)"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || true

ENV_URL="https://raw.githubusercontent.com/KosinskiLab/AlphaPulldownSnakemake/${AP_SNAKEMAKE_VERSION}/workflow/envs/alphapulldown.yaml"
ENV_SOURCE="${ENV_URL}"
if [[ -n "${AP_ENV_YAML:-}" ]]; then
  if [[ ! -f "${AP_ENV_YAML}" ]]; then
    echo "AP_ENV_YAML is set but does not exist: ${AP_ENV_YAML}" >&2
    exit 2
  fi
  ENV_SOURCE="${AP_ENV_YAML}"
fi
if ! "${ENV_MANAGER}" env list | awk '{print $1}' | grep -qx "${CONDA_ENV_NAME}"; then
  run_or_echo "${DRY_RUN}" "${ENV_MANAGER}" env create -n "${CONDA_ENV_NAME}" -f "${ENV_SOURCE}"
else
  echo "Conda environment already exists: ${CONDA_ENV_NAME}"
fi

if [[ ! -d "${AP_WORKFLOW_DIR}/workflow" ]]; then
  require_command "${SNAKEDEPLOY_BIN}"
  run_or_echo "${DRY_RUN}" "${SNAKEDEPLOY_BIN}" deploy-workflow \
    https://github.com/KosinskiLab/AlphaPulldownSnakemake \
    "${AP_WORKFLOW_DIR}" \
    --tag "${AP_SNAKEMAKE_VERSION}"
else
  echo "AlphaPulldownSnakemake workflow already deployed: ${AP_WORKFLOW_DIR}"
fi

{
  echo "run_id=${RUN_ID}"
  echo "timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "env_manager=${ENV_MANAGER}"
  echo "conda_env_name=${CONDA_ENV_NAME}"
  echo "alphapulldown_snakemake_version=${AP_SNAKEMAKE_VERSION}"
  echo "workflow_dir=${AP_WORKFLOW_DIR}"
  echo "python=$({ command -v python3 && python3 --version; } 2>&1 | tr '\n' ' ')"
  echo "snakemake=$({ command -v snakemake && snakemake --version; } 2>&1 | tr '\n' ' ')"
  echo "gpu=$({ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; } 2>&1 | tr '\n' ';')"
} > "${BOOTSTRAP_PROVENANCE}/bootstrap_versions.txt"

echo "Bootstrap provenance: ${BOOTSTRAP_PROVENANCE}"
