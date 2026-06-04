#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$(pwd)}"

echo "== Install A-share review collector =="
echo "Project directory: $PROJECT_DIR"
echo

cd "$PROJECT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is missing. Install it first."
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git is missing. Install it first."
  exit 1
fi

python3 -m venv .venv
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

