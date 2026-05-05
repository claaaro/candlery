#!/usr/bin/env bash
set -euo pipefail

EXPECTED_NAME="${EXPECTED_NAME:-claaaro}"
EXPECTED_EMAIL="${EXPECTED_EMAIL:-274381829+claaaro@users.noreply.github.com}"
FORBIDDEN_RE='co-authored-by:|cursoragent|cursor <|@cursor\.com'

range="${1:-}"
if [[ -z "${range}" ]]; then
  if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    git fetch --quiet origin "${GITHUB_BASE_REF}" || true
    range="origin/${GITHUB_BASE_REF}..HEAD"
  else
    base="$(git rev-list --max-count=1 --skip=50 HEAD 2>/dev/null || true)"
    if [[ -n "${base}" ]]; then
      range="${base}..HEAD"
    else
      range="HEAD"
    fi
  fi
fi

bad=0
while IFS= read -r commit; do
  [[ -z "${commit}" ]] && continue
  a_name="$(git show -s --format=%an "${commit}")"
  a_email="$(git show -s --format=%ae "${commit}")"
  c_name="$(git show -s --format=%cn "${commit}")"
  c_email="$(git show -s --format=%ce "${commit}")"
  msg="$(git show -s --format=%B "${commit}")"

  if [[ "${a_name}" != "${EXPECTED_NAME}" || "${a_email}" != "${EXPECTED_EMAIL}" ]]; then
    echo "ERROR: ${commit} author is ${a_name} <${a_email}> (expected ${EXPECTED_NAME} <${EXPECTED_EMAIL}>)"
    bad=1
  fi
  if [[ "${c_name}" != "${EXPECTED_NAME}" || "${c_email}" != "${EXPECTED_EMAIL}" ]]; then
    echo "ERROR: ${commit} committer is ${c_name} <${c_email}> (expected ${EXPECTED_NAME} <${EXPECTED_EMAIL}>)"
    bad=1
  fi
  if printf "%s" "${msg}" | grep -Eiq "${FORBIDDEN_RE}"; then
    echo "ERROR: ${commit} message contains forbidden attribution text"
    bad=1
  fi
done < <(git rev-list "${range}")

if [[ "${bad}" -ne 0 ]]; then
  echo
  echo "Commit identity check failed."
  exit 1
fi

echo "Commit identity check passed for range: ${range}"
