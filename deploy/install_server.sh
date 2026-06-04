#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-}"

echo "== Install A-share review collector =="
echo "Project directory: $PROJECT_DIR"
echo

cd "$PROJECT_DIR"

if [ -z "$PYTHON_BIN" ]; then
  for candidate in python3.12 python3.11 python3.10 python3.9 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi

if [ -z "$PYTHON_BIN" ] || ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3.9+ is missing. Install a newer Python first."
  exit 1
fi

if ! "$PYTHON_BIN" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
then
  echo "Python is too old: $("$PYTHON_BIN" --version)"
  echo "AkShare and pandas need a newer Python. Please install Python 3.9+."
  echo "On Alibaba Cloud Linux, try: dnf install -y python3.11 python3.11-pip python3.11-devel"
  echo "Then rerun: PYTHON_BIN=python3.11 bash deploy/install_server.sh"
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git is missing. Install it first."
  exit 1
fi

if [ -x ".venv/bin/python" ]; then
  if ! .venv/bin/python - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
  then
    echo "Existing virtualenv uses an old Python: $(.venv/bin/python --version)"
    echo "Recreating .venv with $("$PYTHON_BIN" --version)."
    rm -rf .venv
  fi
fi

"$PYTHON_BIN" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

mkdir -p logs data/raw data/processed data/reports

echo
echo "== Run tests =="
PYTHONPATH=tools python -m unittest discover -s tools/tests

echo
echo "== Install complete =="
echo "Try:"
echo "./scripts/run_daily.sh 2026-06-02"
