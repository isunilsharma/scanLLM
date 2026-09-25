#!/usr/bin/env bash
# ScanLLM end-to-end install test kit.
#
# Builds a throwaway virtualenv, installs scanllm exactly the way a new user
# would, scans pinned open-source repos, and asserts on the results.
#
#   ./run.sh                      # test the current PyPI release
#   ./run.sh --source pypi==2.3.2 # test a specific published version
#   ./run.sh --source local       # test this working tree before releasing
#   ./run.sh --source wheel:dist/scanllm-2.3.3-py3-none-any.whl
#   ./run.sh --extras all         # also install server/reports/watch extras
#   ./run.sh --keep               # reuse the existing venv (faster reruns)
#
# Exit code 0 = all checks passed, 1 = at least one check failed.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
WORK="${SCANLLM_E2E_WORK:-$HERE/.work}"
VENV="$WORK/venv"
REPOS="$WORK/repos"
RESULTS="$WORK/results"

SOURCE="pypi"
EXTRAS=""
KEEP=0
PYTHON_BIN="${SCANLLM_E2E_PYTHON:-python3}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source) SOURCE="$2"; shift 2 ;;
    --extras) EXTRAS="$2"; shift 2 ;;
    --python) PYTHON_BIN="$2"; shift 2 ;;
    --keep)   KEEP=1; shift ;;
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

bold()  { printf '\033[1m%s\033[0m\n' "$*"; }
info()  { printf '  %s\n' "$*"; }
fail()  { printf '\033[31m  FAIL %s\033[0m\n' "$*"; }

bold "ScanLLM e2e install test"
info "source      : $SOURCE"
info "extras      : ${EXTRAS:-<none>}"
info "work dir    : $WORK"
info "python      : $($PYTHON_BIN -V 2>&1)"
echo

# ---------------------------------------------------------------- 1. venv ---
mkdir -p "$WORK" "$REPOS" "$RESULTS"
if [[ $KEEP -eq 0 || ! -x "$VENV/bin/python" ]]; then
  bold "[1/4] Creating clean virtualenv"
  rm -rf "$VENV"
  "$PYTHON_BIN" -m venv "$VENV" || exit 1
  "$VENV/bin/python" -m pip install -q --upgrade pip
else
  bold "[1/4] Reusing existing virtualenv (--keep)"
fi

PIP="$VENV/bin/pip"
SCANLLM="$VENV/bin/scanllm"

# ------------------------------------------------------------- 2. install ---
bold "[2/4] Installing scanllm"
suffix=""; [[ -n "$EXTRAS" ]] && suffix="[$EXTRAS]"
case "$SOURCE" in
  local)    target="$REPO_ROOT$suffix" ;;
  wheel:*)  target="${SOURCE#wheel:}$suffix" ;;
  pypi)     target="scanllm$suffix" ;;
  pypi==*)  target="scanllm$suffix==${SOURCE#pypi==}" ;;
  *)        echo "bad --source: $SOURCE" >&2; exit 2 ;;
esac
info "pip install --no-cache-dir '$target'"
if ! "$PIP" install -q --no-cache-dir "$target"; then
  fail "installation failed"; exit 1
fi
INSTALLED_VERSION="$("$SCANLLM" --version 2>/dev/null | awk '{print $NF}')"
info "installed   : scanllm $INSTALLED_VERSION"
echo

# ------------------------------------------------------------ 3. fixtures ---
bold "[3/4] Fetching pinned fixture repos"
while IFS=$'\t' read -r name url sha; do
  [[ -z "${name:-}" || "$name" == \#* ]] && continue
  dest="$REPOS/$name"
  if [[ -d "$dest/.git" ]] && [[ "$(git -C "$dest" rev-parse HEAD 2>/dev/null)" == "$sha" ]]; then
    info "$name: cached at ${sha:0:8}"
    continue
  fi
  rm -rf "$dest"; mkdir -p "$dest"
  git -C "$dest" init -q
  git -C "$dest" remote add origin "$url"
  if git -C "$dest" fetch --depth 1 -q origin "$sha" 2>/dev/null; then
    git -C "$dest" checkout -q FETCH_HEAD
  else
    rm -rf "$dest"
    git clone -q "$url" "$dest" && git -C "$dest" checkout -q "$sha"
  fi
  info "$name: fetched ${sha:0:8}"
done < "$HERE/fixtures.txt"
echo

# --------------------------------------------------------------- 4. scans ---
bold "[4/4] Scanning fixtures and running checks"
for d in "$REPOS"/*/; do
  name="$(basename "$d")"
  COLUMNS=200 "$SCANLLM" scan "$d" -o json --no-banner > "$RESULTS/$name.json" 2>"$RESULTS/$name.err"
  code=$?
  echo "$code" > "$RESULTS/$name.exit"
  COLUMNS=200 "$SCANLLM" scan "$d" --no-banner > "$RESULTS/$name.table.txt" 2>&1
  COLUMNS=200 "$SCANLLM" scan "$d" -o sarif     --no-banner > "$RESULTS/$name.sarif.json" 2>/dev/null
  COLUMNS=200 "$SCANLLM" scan "$d" -o cyclonedx --no-banner > "$RESULTS/$name.cdx.json"   2>/dev/null
  COLUMNS=200 "$SCANLLM" scan "$d" -o json -s high --no-banner > "$RESULTS/$name.high.json" 2>/dev/null
  if [[ ! -s "$RESULTS/$name.json" ]]; then
    fail "$name produced no JSON output"; cat "$RESULTS/$name.err"
  fi
done
COLUMNS=200 "$SCANLLM" doctor > "$RESULTS/doctor.txt" 2>&1
echo

"$VENV/bin/python" "$HERE/checks.py" \
  --results "$RESULTS" --version "$INSTALLED_VERSION" --source "$SOURCE"
rc=$?
echo
info "artifacts: $RESULTS"
exit $rc
