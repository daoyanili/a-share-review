#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$(pwd)}"
RUN_USER="${2:-${SUDO_USER:-$(id -un)}}"
SERVICE_FILE="/etc/systemd/system/a-share-review.service"
TIMER_FILE="/etc/systemd/system/a-share-review.timer"

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root, for example:"
  echo "sudo bash deploy/setup_systemd.sh $(pwd) $(id -un)"
  exit 1
fi

if [ ! -f "$PROJECT_DIR/scripts/run_daily.sh" ]; then
  echo "Project directory is not valid: $PROJECT_DIR"
  echo "Expected file: $PROJECT_DIR/scripts/run_daily.sh"
  exit 1
fi

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl is missing. This script is intended for systemd servers."
  exit 1
fi

mkdir -p "$PROJECT_DIR/logs" "$PROJECT_DIR/data/raw" "$PROJECT_DIR/data/processed" "$PROJECT_DIR/data/reports"
chmod +x "$PROJECT_DIR/scripts/run_daily.sh"

cat >"$SERVICE_FILE" <<EOF
[Unit]
Description=A-share review daily data collector
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
User=$RUN_USER
WorkingDirectory=$PROJECT_DIR
Environment=TZ=Asia/Shanghai
Environment=PATH=$PROJECT_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/bin/bash $PROJECT_DIR/scripts/run_daily.sh
EOF

cat >"$TIMER_FILE" <<'EOF'
[Unit]
Description=Run A-share review data collector on trading days

[Timer]
OnCalendar=Mon..Fri *-*-* 15:20:00
Persistent=true
Unit=a-share-review.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now a-share-review.timer

echo "systemd timer installed."
echo
systemctl list-timers a-share-review.timer --no-pager
echo
echo "Manual run:"
echo "sudo systemctl start a-share-review.service"
echo
echo "Logs:"
echo "journalctl -u a-share-review.service -n 100 --no-pager"
