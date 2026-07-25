#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DEFAULT_ENV_FILE="${REPO_ROOT}/config/remote/paths.env"

REMOTE_ENV_FILE="${REMOTE_ENV_FILE:-${DEFAULT_ENV_FILE}}"

load_remote_env() {
  local env_file="${1:-${REMOTE_ENV_FILE}}"
  if [[ ! -f "${env_file}" ]]; then
    echo "Missing remote environment file: ${env_file}" >&2
    echo "Copy config/remote/paths.example.env to config/remote/paths.env and edit it." >&2
    exit 2
  fi
  set -a
  # shellcheck disable=SC1090
  source "${env_file}"
  set +a
  REMOTE_ENV_FILE="${env_file}"
}

require_linux() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This script is for remote Linux execution, not local macOS." >&2
    exit 2
  fi
}

require_command() {
  local name="$1"
  if ! command -v "${name}" >/dev/null 2>&1; then
    echo "Missing required command: ${name}" >&2
    exit 2
  fi
}

ensure_dir() {
  local path="$1"
  mkdir -p "${path}"
  if [[ ! -w "${path}" ]]; then
    echo "Path is not writable: ${path}" >&2
    exit 2
  fi
}

remote_python() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}" "${PYTHON_BIN}" "$@"
  else
    PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}" python3 "$@"
  fi
}

run_or_echo() {
  local dry_run="$1"
  shift
  if [[ "${dry_run}" == "1" ]]; then
    printf 'DRY RUN:'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}
