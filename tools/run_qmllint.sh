#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGETS_FILE="${ROOT_DIR}/tools/qmllint_targets.txt"

resolve_qmllint() {
  local candidate=""
  candidate="$(command -v qmllint || true)"
  if [[ -n "${candidate}" ]]; then
    echo "${candidate}"
    return 0
  fi

  candidate="$(command -v qmllint6 || true)"
  if [[ -n "${candidate}" ]]; then
    echo "${candidate}"
    return 0
  fi

  if command -v qtpaths6 >/dev/null 2>&1; then
    local host_bins
    host_bins="$(qtpaths6 --query QT_HOST_BINS 2>/dev/null || true)"
    if [[ -n "${host_bins}" ]]; then
      for candidate in "${host_bins}/qmllint" "${host_bins}/qmllint6"; do
        if [[ -x "${candidate}" ]]; then
          echo "${candidate}"
          return 0
        fi
      done
    fi
  fi

  for candidate in /usr/lib/qt6/bin/qmllint /usr/lib/qt6/bin/qmllint6 /usr/lib/qt/bin/qmllint /usr/lib/qt/bin/qmllint6; do
    if [[ -x "${candidate}" ]]; then
      echo "${candidate}"
      return 0
    fi
  done

  return 1
}

if [[ ! -f "${TARGETS_FILE}" ]]; then
  echo "qmllint targets file is missing: ${TARGETS_FILE}" >&2
  exit 1
fi

QMLLINT_BIN="$(resolve_qmllint || true)"
if [[ -z "${QMLLINT_BIN}" ]]; then
  echo "qmllint (or qmllint6) is not installed." >&2
  exit 1
fi

declare -a qml_files=()
while IFS= read -r target || [[ -n "${target}" ]]; do
  target="${target#"${target%%[![:space:]]*}"}"
  target="${target%"${target##*[![:space:]]}"}"
  [[ -z "${target}" || "${target}" == \#* ]] && continue

  abs_target="${ROOT_DIR}/${target}"
  if [[ -d "${abs_target}" ]]; then
    while IFS= read -r -d '' file; do
      qml_files+=("${file}")
    done < <(find "${abs_target}" -maxdepth 1 -type f -name '*.qml' -print0 | sort -z)
  elif [[ -f "${abs_target}" ]]; then
    qml_files+=("${abs_target}")
  fi
done < "${TARGETS_FILE}"

if [[ "${#qml_files[@]}" -eq 0 ]]; then
  echo "No QML files were found for qmllint." >&2
  exit 1
fi

declare -a rel_files=()
for file in "${qml_files[@]}"; do
  rel_files+=("${file#${ROOT_DIR}/}")
done

exec "${QMLLINT_BIN}" "${rel_files[@]}"
