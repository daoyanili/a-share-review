#!/usr/bin/env bash
set -u

echo "== A-share review server check =="
echo

echo "== OS =="
if [ -f /etc/os-release ]; then
  cat /etc/os-release
else
  uname -a
fi
echo

echo "== Time =="
date
command -v timedatectl >/dev/null 2>&1 && timedatectl | sed -n '1,12p'
echo

echo "== User and path =="
whoami
pwd
echo "HOME=$HOME"
echo

echo "== Commands =="
for cmd in python3 pip3 git curl wget zsh bash systemctl crontab dnf yum apt; do
  if command -v "$cmd" >/dev/null 2>&1; then
    printf "%-10s %s\n" "$cmd" "$(command -v "$cmd")"
  else
    printf "%-10s %s\n" "$cmd" "missing"
  fi
done
echo

echo "== Python =="
python3 --version 2>&1 || true
python3 -m venv --help >/dev/null 2>&1 && echo "venv: ok" || echo "venv: missing"
echo

echo "== Disk and memory =="
df -h .
free -h 2>/dev/null || true
echo

echo "== Network probes =="
probe() {
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -I -L --connect-timeout 8 --max-time 15 "$url" 2>/dev/null | sed -n '1,4p'
  elif command -v wget >/dev/null 2>&1; then
    wget --spider --timeout=15 "$url" 2>&1 | sed -n '1,6p'
  else
    echo "curl/wget missing, skip $url"
  fi
  echo
}

probe "https://pypi.org/simple/akshare/"
probe "https://api.zizizaizai.com/v3/api/review/uplimit/reason?date1=2026-06-02&page=1&page_size=1"
probe "https://stock.ziruxing.com/open/tradedays"
probe "https://hq.sinajs.cn/list=sh000001"
probe "https://push2.eastmoney.com"

echo "== systemd =="
if command -v systemctl >/dev/null 2>&1; then
  systemctl --version | sed -n '1,2p'
  systemctl is-system-running 2>/dev/null || true
else
  echo "systemctl missing"
fi
echo

echo "== Done =="

