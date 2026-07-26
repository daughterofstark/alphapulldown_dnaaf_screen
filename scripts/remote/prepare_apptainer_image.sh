#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

usage() {
  cat <<'USAGE'
Usage: prepare_apptainer_image.sh [--env-file PATH] [--dry-run] [--force]

Safely prepares the pinned AlphaFold2 Apptainer SIF before feature generation.
It separates persistent cache/output on /workspace from temporary SIF
construction on an explicit local build directory. It does not run Snakemake,
feature generation, or inference.
USAGE
}

DRY_RUN=0
FORCE=0
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
    --force)
      FORCE=1
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
require_command apptainer

APPTAINER_IMAGE_DIR="${APPTAINER_IMAGE_DIR:-${REMOTE_PROJECT_ROOT}/results/containers}"
APPTAINER_PERSISTENT_CACHE_DIR="${APPTAINER_PERSISTENT_CACHE_DIR:-${REMOTE_PROJECT_ROOT}/results/apptainer_cache}"
APPTAINER_LOCAL_BUILD_DIR="${APPTAINER_LOCAL_BUILD_DIR:-}"
APPTAINER_MIN_LOCAL_FREE_GB="${APPTAINER_MIN_LOCAL_FREE_GB:-28}"
APPTAINER_PREDICTION_IMAGE="${APPTAINER_PREDICTION_IMAGE:-docker://kosinskilab/alphafold2:2.5.0}"
APPTAINER_PREDICTION_SIF="${APPTAINER_PREDICTION_SIF:-${APPTAINER_IMAGE_DIR}/kosinskilab_alphafold2_2.5.0.sif}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"

fs_type() {
  local path="$1"
  mkdir -p "${path}"
  findmnt -T "${path}" -no FSTYPE 2>/dev/null | head -1 || df -T "${path}" | awk 'NR==2 {print $2}'
}

fs_available_kb() {
  local path="$1"
  df -Pk "${path}" | awk 'NR==2 {print $4}'
}

is_network_fs() {
  case "$1" in
    fuse*|nfs|nfs4|cifs|smb3|sshfs|lustre|gpfs|beegfs|ceph|ceph-fuse|glusterfs)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

run_or_echo_with_env() {
  if [[ "${DRY_RUN}" == "1" ]]; then
    printf 'DRY RUN:'
    printf ' %q=%q' APPTAINER_CACHEDIR "${APPTAINER_PERSISTENT_CACHE_DIR}"
    printf ' %q=%q' APPTAINER_TMPDIR "${LOCAL_TMPDIR}"
    printf ' %q' "$@"
    printf '\n'
  else
    APPTAINER_CACHEDIR="${APPTAINER_PERSISTENT_CACHE_DIR}" \
      APPTAINER_TMPDIR="${LOCAL_TMPDIR}" \
      "$@"
  fi
}

validate_sif() {
  local sif="$1"
  [[ -s "${sif}" ]] || return 1
  apptainer inspect "${sif}" >/dev/null 2>&1 || return 1
}

if [[ -z "${APPTAINER_LOCAL_BUILD_DIR}" ]]; then
  echo "APPTAINER_LOCAL_BUILD_DIR must be set to an explicit local disk path." >&2
  echo "Do not default to /tmp on RunPod; check available local capacity first." >&2
  exit 2
fi

for path in "${APPTAINER_IMAGE_DIR}" "${APPTAINER_PERSISTENT_CACHE_DIR}" "${APPTAINER_LOCAL_BUILD_DIR}" "${APPTAINER_PREDICTION_SIF}"; do
  case "${path}" in
    /*) ;;
    *)
      echo "Apptainer paths must be absolute for portable CPU/GPU handoff: ${path}" >&2
      exit 2
      ;;
  esac
done

mkdir -p "${APPTAINER_IMAGE_DIR}" "${APPTAINER_PERSISTENT_CACHE_DIR}" "${APPTAINER_LOCAL_BUILD_DIR}"

CACHE_FS="$(fs_type "${APPTAINER_PERSISTENT_CACHE_DIR}")"
BUILD_FS="$(fs_type "${APPTAINER_LOCAL_BUILD_DIR}")"
CACHE_FREE_KB="$(fs_available_kb "${APPTAINER_PERSISTENT_CACHE_DIR}")"
BUILD_FREE_KB="$(fs_available_kb "${APPTAINER_LOCAL_BUILD_DIR}")"
MIN_FREE_KB=$((APPTAINER_MIN_LOCAL_FREE_GB * 1024 * 1024))
LOCAL_TMPDIR="${APPTAINER_LOCAL_BUILD_DIR}/apptainer-tmp-${TIMESTAMP}"
LOCAL_SIF_TMP="${APPTAINER_LOCAL_BUILD_DIR}/$(basename "${APPTAINER_PREDICTION_SIF}").building.${TIMESTAMP}"
SIF_SHA256="${APPTAINER_PREDICTION_SIF}.sha256"
SIF_INSPECT="${APPTAINER_PREDICTION_SIF}.inspect.txt"

echo "Apptainer version: $(apptainer --version)"
echo "Container source: ${APPTAINER_PREDICTION_IMAGE}"
echo "Completed SIF: ${APPTAINER_PREDICTION_SIF}"
echo "Persistent cache: ${APPTAINER_PERSISTENT_CACHE_DIR} (${CACHE_FS}, ${CACHE_FREE_KB} KiB free)"
echo "Local build dir: ${APPTAINER_LOCAL_BUILD_DIR} (${BUILD_FS}, ${BUILD_FREE_KB} KiB free)"
echo "Minimum local free space: ${APPTAINER_MIN_LOCAL_FREE_GB} GiB"

if [[ "${FORCE}" != "1" ]] && validate_sif "${APPTAINER_PREDICTION_SIF}"; then
  echo "Valid existing SIF found; refusing to rebuild: ${APPTAINER_PREDICTION_SIF}"
  if [[ "${DRY_RUN}" == "1" ]]; then
    echo "DRY RUN: sha256sum ${APPTAINER_PREDICTION_SIF} > ${SIF_SHA256}"
    echo "DRY RUN: apptainer inspect ${APPTAINER_PREDICTION_SIF} > ${SIF_INSPECT}"
  else
    sha256sum "${APPTAINER_PREDICTION_SIF}" > "${SIF_SHA256}"
    apptainer inspect "${APPTAINER_PREDICTION_SIF}" > "${SIF_INSPECT}"
  fi
  exit 0
fi

if [[ -e "${APPTAINER_PREDICTION_SIF}" ]] && ! validate_sif "${APPTAINER_PREDICTION_SIF}"; then
  PARTIAL="${APPTAINER_PREDICTION_SIF}.partial.${TIMESTAMP}"
  if [[ "${DRY_RUN}" == "1" ]]; then
    echo "DRY RUN: mv ${APPTAINER_PREDICTION_SIF} ${PARTIAL}"
  else
    mv "${APPTAINER_PREDICTION_SIF}" "${PARTIAL}"
  fi
  echo "Moved invalid/interrupted SIF aside: ${PARTIAL}"
elif [[ "${FORCE}" == "1" && -e "${APPTAINER_PREDICTION_SIF}" ]]; then
  PREVIOUS="${APPTAINER_PREDICTION_SIF}.previous.${TIMESTAMP}"
  if [[ "${DRY_RUN}" == "1" ]]; then
    echo "DRY RUN: mv ${APPTAINER_PREDICTION_SIF} ${PREVIOUS}"
  else
    mv "${APPTAINER_PREDICTION_SIF}" "${PREVIOUS}"
  fi
  echo "Moved existing SIF aside before forced rebuild: ${PREVIOUS}"
fi

if is_network_fs "${BUILD_FS}"; then
  echo "Refusing to build SIF on network/FUSE filesystem: ${APPTAINER_LOCAL_BUILD_DIR} (${BUILD_FS})" >&2
  exit 2
fi

if is_network_fs "${CACHE_FS}"; then
  echo "Warning: persistent Apptainer cache is on ${CACHE_FS}; this is acceptable for cached artifacts but not for SIF construction."
fi

if (( BUILD_FREE_KB < MIN_FREE_KB )); then
  echo "Insufficient local build space in ${APPTAINER_LOCAL_BUILD_DIR}: ${BUILD_FREE_KB} KiB free, need at least ${MIN_FREE_KB} KiB." >&2
  exit 2
fi

if [[ -e "${LOCAL_SIF_TMP}" ]]; then
  if [[ "${DRY_RUN}" == "1" ]]; then
    echo "DRY RUN: rm stale local partial ${LOCAL_SIF_TMP}"
  else
    rm -f "${LOCAL_SIF_TMP}"
  fi
fi

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "DRY RUN: mkdir -p ${LOCAL_TMPDIR}"
else
  mkdir -p "${LOCAL_TMPDIR}"
fi

run_or_echo_with_env apptainer pull --force "${LOCAL_SIF_TMP}" "${APPTAINER_PREDICTION_IMAGE}"

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "DRY RUN: apptainer inspect ${LOCAL_SIF_TMP}"
  echo "DRY RUN: mv ${LOCAL_SIF_TMP} ${APPTAINER_PREDICTION_SIF}"
  echo "DRY RUN: sha256sum ${APPTAINER_PREDICTION_SIF} > ${SIF_SHA256}"
  echo "DRY RUN: apptainer inspect ${APPTAINER_PREDICTION_SIF} > ${SIF_INSPECT}"
  echo "DRY RUN: rm -rf ${LOCAL_TMPDIR}"
  echo "Apptainer image preparation dry run completed."
  exit 0
fi

if ! validate_sif "${LOCAL_SIF_TMP}"; then
  echo "Apptainer build did not produce a valid SIF: ${LOCAL_SIF_TMP}" >&2
  exit 2
fi

mv "${LOCAL_SIF_TMP}" "${APPTAINER_PREDICTION_SIF}"
sha256sum "${APPTAINER_PREDICTION_SIF}" > "${SIF_SHA256}"
apptainer inspect "${APPTAINER_PREDICTION_SIF}" > "${SIF_INSPECT}"
rm -rf "${LOCAL_TMPDIR}"
validate_sif "${APPTAINER_PREDICTION_SIF}"
echo "Prepared Apptainer SIF: ${APPTAINER_PREDICTION_SIF}"
echo "SIF SHA-256: ${SIF_SHA256}"
echo "SIF inspect metadata: ${SIF_INSPECT}"
