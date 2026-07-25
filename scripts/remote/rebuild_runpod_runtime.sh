#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: rebuild_runpod_runtime.sh [--dry-run]

Rebuilds the disposable RunPod runtime under /workspace after host migration or
environment corruption. It never touches project data, results, logs, or target
manifests. It does not run AlphaPulldown feature generation or inference.
USAGE
}

DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
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

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This recovery script is for RunPod/Linux only." >&2
  exit 2
fi

if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "Unsupported RunPod architecture: $(uname -m)" >&2
  exit 2
fi

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspace}"
MINIFORGE_DIR="${MINIFORGE_DIR:-${WORKSPACE_ROOT}/miniforge3}"
RUNTIME_DIR="${RUNTIME_DIR:-${WORKSPACE_ROOT}/alphapulldown_runtime}"
RUNPOD_LOG_DIR="${RUNPOD_LOG_DIR:-${WORKSPACE_ROOT}/runpod_logs}"
PROJECT_ROOT="${PROJECT_ROOT:-${WORKSPACE_ROOT}/alphapulldown}"
AP_WORKFLOW_DIR="${AP_WORKFLOW_DIR:-${WORKSPACE_ROOT}/workflows/AlphaPulldownSnakemake}"
AP_SNAKEMAKE_VERSION="${AP_SNAKEMAKE_VERSION:-2.5.0}"
SNAKE_ENV_NAME="${SNAKE_ENV_NAME:-snake}"
TOOLS_ENV_NAME="${TOOLS_ENV_NAME:-snakedeploy-tools}"
MINIFORGE_INSTALLER_URL="${MINIFORGE_INSTALLER_URL:-https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh}"
AP_ENV_YAML="${AP_ENV_YAML:-${RUNTIME_DIR}/alphapulldown_snakemake_${AP_SNAKEMAKE_VERSION}.yaml}"
AP_ENV_YAML_URL="${AP_ENV_YAML_URL:-https://raw.githubusercontent.com/KosinskiLab/AlphaPulldownSnakemake/${AP_SNAKEMAKE_VERSION}/workflow/envs/alphapulldown.yaml}"
MINIFORGE_INSTALLER="${RUNTIME_DIR}/Miniforge3-Linux-x86_64.sh"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_FILE="${RUNPOD_LOG_DIR}/rebuild_runpod_runtime_${TIMESTAMP}.log"

case "${WORKSPACE_ROOT}" in
  /workspace|/workspace/*) ;;
  *)
    echo "WORKSPACE_ROOT must be under /workspace, got: ${WORKSPACE_ROOT}" >&2
    exit 2
    ;;
esac

for path in "${MINIFORGE_DIR}" "${RUNTIME_DIR}" "${RUNPOD_LOG_DIR}" "${PROJECT_ROOT}" "${AP_WORKFLOW_DIR}"; do
  case "${path}" in
    /workspace|/workspace/*) ;;
    *)
      echo "Refusing non-/workspace path: ${path}" >&2
      exit 2
      ;;
  esac
done

mkdir -p "${RUNPOD_LOG_DIR}" "${RUNTIME_DIR}"
exec > >(tee -a "${LOG_FILE}") 2>&1

run_or_echo() {
  if [[ "${DRY_RUN}" == "1" ]]; then
    printf 'DRY RUN:'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

fetch_url() {
  local url="$1"
  local output="$2"
  if command -v curl >/dev/null 2>&1; then
    run_or_echo curl -fsSL -o "${output}" "${url}"
  elif command -v wget >/dev/null 2>&1; then
    run_or_echo wget -q -O "${output}" "${url}"
  else
    echo "Either curl or wget is required to rebuild the RunPod runtime." >&2
    exit 2
  fi
}

miniforge_is_healthy() {
  [[ -x "${MINIFORGE_DIR}/bin/conda" ]] || return 1
  [[ -x "${MINIFORGE_DIR}/bin/python" ]] || return 1
  "${MINIFORGE_DIR}/bin/python" -c 'import encodings, ssl, sys; print(sys.version)' >/dev/null 2>&1 || return 1
  "${MINIFORGE_DIR}/bin/conda" --version >/dev/null 2>&1 || return 1
  if [[ -x "${MINIFORGE_DIR}/bin/mamba" ]]; then
    "${MINIFORGE_DIR}/bin/mamba" --version >/dev/null 2>&1 || return 1
  fi
}

env_is_healthy() {
  local env_name="$1"
  local python_check="$2"
  local python_bin="${MINIFORGE_DIR}/envs/${env_name}/bin/python"
  [[ -x "${python_bin}" ]] || return 1
  "${python_bin}" -c 'import encodings, ssl, sys; print(sys.version)' >/dev/null 2>&1 || return 1
  "${python_bin}" -c "${python_check}" >/dev/null 2>&1 || return 1
}

conda_runner() {
  if [[ -x "${MINIFORGE_DIR}/bin/mamba" ]]; then
    echo "${MINIFORGE_DIR}/bin/mamba"
  else
    echo "${MINIFORGE_DIR}/bin/conda"
  fi
}

echo "RunPod runtime rebuild log: ${LOG_FILE}"
echo "Timestamp UTC: ${TIMESTAMP}"
echo "Workspace root: ${WORKSPACE_ROOT}"
echo "Project root: ${PROJECT_ROOT}"
echo "Miniforge dir: ${MINIFORGE_DIR}"
echo "Runtime dir: ${RUNTIME_DIR}"
echo "Workflow dir: ${AP_WORKFLOW_DIR}"
echo "Dry run: ${DRY_RUN}"

if miniforge_is_healthy; then
  echo "Miniforge execution checks passed."
else
  echo "Miniforge is missing or failed execution checks."
  if [[ -e "${MINIFORGE_DIR}" ]]; then
    BROKEN_DIR="${MINIFORGE_DIR}.broken.${TIMESTAMP}"
    run_or_echo mv "${MINIFORGE_DIR}" "${BROKEN_DIR}"
    echo "Moved broken Miniforge aside: ${BROKEN_DIR}"
  fi
  fetch_url "${MINIFORGE_INSTALLER_URL}" "${MINIFORGE_INSTALLER}"
  run_or_echo bash "${MINIFORGE_INSTALLER}" -b -p "${MINIFORGE_DIR}"
fi

if [[ "${DRY_RUN}" == "1" ]]; then
  CONDA_BIN="${MINIFORGE_DIR}/bin/conda"
  ENV_MANAGER="${MINIFORGE_DIR}/bin/mamba"
else
  if ! miniforge_is_healthy; then
    echo "Miniforge installation did not pass execution checks after rebuild." >&2
    exit 2
  fi
  CONDA_BIN="${MINIFORGE_DIR}/bin/conda"
  ENV_MANAGER="$(conda_runner)"
fi

echo "Conda executable: ${CONDA_BIN}"
echo "Environment manager: ${ENV_MANAGER}"

if env_is_healthy "${TOOLS_ENV_NAME}" 'import snakemake; print("snakemake ok")'; then
  echo "Tooling environment is healthy: ${TOOLS_ENV_NAME}"
else
  echo "Tooling environment is missing or broken: ${TOOLS_ENV_NAME}"
  if [[ -d "${MINIFORGE_DIR}/envs/${TOOLS_ENV_NAME}" ]]; then
    run_or_echo "${CONDA_BIN}" env remove -n "${TOOLS_ENV_NAME}" -y
  fi
  run_or_echo "${ENV_MANAGER}" create -n "${TOOLS_ENV_NAME}" -c conda-forge -y snakedeploy snakemake
fi

if [[ ! -f "${AP_ENV_YAML}" ]]; then
  echo "Fetching pinned AlphaPulldownSnakemake environment YAML: ${AP_ENV_YAML_URL}"
  fetch_url "${AP_ENV_YAML_URL}" "${AP_ENV_YAML}"
else
  echo "Pinned environment YAML already exists: ${AP_ENV_YAML}"
fi

if env_is_healthy "${SNAKE_ENV_NAME}" 'import snakemake, alphapulldown_input_parser; print("snake ok")'; then
  echo "AlphaPulldownSnakemake orchestration environment is healthy: ${SNAKE_ENV_NAME}"
else
  echo "AlphaPulldownSnakemake orchestration environment is missing or broken: ${SNAKE_ENV_NAME}"
  if [[ -d "${MINIFORGE_DIR}/envs/${SNAKE_ENV_NAME}" ]]; then
    run_or_echo "${CONDA_BIN}" env remove -n "${SNAKE_ENV_NAME}" -y
  fi
  run_or_echo "${ENV_MANAGER}" env create -n "${SNAKE_ENV_NAME}" -f "${AP_ENV_YAML}"
fi

if [[ "${DRY_RUN}" != "1" ]]; then
  "${MINIFORGE_DIR}/envs/${TOOLS_ENV_NAME}/bin/snakedeploy" --help >/dev/null
  "${MINIFORGE_DIR}/envs/${SNAKE_ENV_NAME}/bin/snakemake" --version >/dev/null
  "${MINIFORGE_DIR}/envs/${SNAKE_ENV_NAME}/bin/python" -c 'import alphapulldown_input_parser; print("alphapulldown-input-parser ok")'
  if "${MINIFORGE_DIR}/envs/${SNAKE_ENV_NAME}/bin/python" -c 'import alphapulldown' >/dev/null 2>&1; then
    echo "alphapulldown importable in orchestration env."
  else
    echo "alphapulldown not importable in orchestration env; expected for containerized workflow runtime."
  fi
fi

if [[ ! -f "${AP_WORKFLOW_DIR}/workflow/Snakefile" ]]; then
  echo "Deploying pinned AlphaPulldownSnakemake workflow."
  run_or_echo "${MINIFORGE_DIR}/envs/${TOOLS_ENV_NAME}/bin/snakedeploy" deploy-workflow \
    https://github.com/KosinskiLab/AlphaPulldownSnakemake \
    "${AP_WORKFLOW_DIR}" \
    --tag "${AP_SNAKEMAKE_VERSION}"
else
  echo "Pinned workflow already deployed: ${AP_WORKFLOW_DIR}/workflow/Snakefile"
fi

if [[ "${DRY_RUN}" != "1" && ! -f "${AP_WORKFLOW_DIR}/workflow/Snakefile" ]]; then
  echo "Workflow deployment did not produce ${AP_WORKFLOW_DIR}/workflow/Snakefile" >&2
  exit 2
fi

echo "RunPod runtime rebuild completed without starting feature generation or inference."
