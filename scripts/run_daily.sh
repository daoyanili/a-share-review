#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TRADE_DATE="${1:-$(TZ=Asia/Shanghai date +%Y-%m-%d)}"
if [ "$#" -gt 0 ]; then
  shift
fi

mkdir -p "$ROOT_DIR/logs"

cd "$ROOT_DIR"
PYTHONPATH=tools python3 tools/collect_daily_data.py "$TRADE_DATE" --out-dir . --allow-insecure "$@"
