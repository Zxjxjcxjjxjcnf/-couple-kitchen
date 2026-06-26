#!/bin/bash
# Railway 启动脚本 — 如果 Dockerfile 不生效，这个会被 Procfile 调用
set -e
PORT="${PORT:-8000}"
echo "[启动] 端口: $PORT"
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" --proxy-headers --forwarded-allow-ips='*'
