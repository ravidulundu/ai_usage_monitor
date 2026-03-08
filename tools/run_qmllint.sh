#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGETS_FILE="${ROOT_DIR}/tools/qmllint_targets.txt"

if [[ ! -f "${TARGETS_FILE}" ]]; then
  echo "qmllint targets file is missing: ${TARGETS_FILE}" >&2
  exit 1
fi

QMLLINT_BIN="$(command -v qmllint || command -v qmllint6 || true)"
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
