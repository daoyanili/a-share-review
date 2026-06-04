#!/usr/bin/env bash
set -u

echo "== Host =="
hostname
date
whoami
echo

echo "== OS =="
if [ -f /etc/os-release ]; then
  cat /etc/os-release
else
  uname -a
fi
echo

echo "== CPU =="
nproc 2>/dev/null || true
lscpu 2>/dev/null | sed -n '1,16p' || true
echo

echo "== Memory =="
free -h 2>/dev/null || true
echo

echo "== Disk =="
df -h
echo

echo "== Largest directories under /root and /opt =="
du -h -d 1 /root 2>/dev/null | sort -h | tail -n 20 || true
du -h -d 1 /opt 2>/dev/null | sort -h | tail -n 20 || true
echo

echo "== Top memory processes =="
ps -eo pid,user,%mem,%cpu,rss,cmd --sort=-%mem | head -n 25
echo

echo "== Top CPU processes =="
ps -eo pid,user,%mem,%cpu,rss,cmd --sort=-%cpu | head -n 25
echo

echo "== Running services =="
if command -v systemctl >/dev/null 2>&1; then
  systemctl list-units --type=service --state=running --no-pager | sed -n '1,120p'
else
  echo "systemctl not found"
fi
echo

echo "== Enabled timers =="
if command -v systemctl >/dev/null 2>&1; then
  systemctl list-timers --all --no-pager | sed -n '1,120p'
else
  echo "systemctl not found"
fi
echo

echo "== Docker =="
if command -v docker >/dev/null 2>&1; then
  docker ps -a
  echo
  docker system df
else
  echo "docker not found"
fi
echo

echo "== Python and git =="
python3 --version 2>&1 || true
pip3 --version 2>&1 || true
git --version 2>&1 || true
echo

echo "== Network probes =="
for url in \
  "https://pypi.org/simple/akshare/" \
  "https://stock.ziruxing.com/open/tradedays" \
  "https://api.zizizaizai.com/v3/api/review/uplimit/reason?date1=2026-06-02&page=1&page_size=1" \
  "https://hq.sinajs.cn/list=sh000001"; do
  echo "-- $url"
  if command -v curl >/dev/null 2>&1; then
    curl -I -L --connect-timeout 8 --max-time 15 "$url" 2>/dev/null | sed -n '1,8p'
  else
    echo "curl not found"
  fi
  echo
done

echo "== Recommendation hints =="
echo "- If free memory is under 500M, add swap or stop unused services before installing pandas/akshare."
echo "- If disk free space is under 3G, clean old logs/images before deployment."
echo "- Do not remove unknown system services. Check service names first."

