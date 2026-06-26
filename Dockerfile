# 情侣私厨 — 生产环境 Docker 镜像
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY . .

RUN mkdir -p backend/uploads

# 用 python 启动，从环境变量读取 PORT
CMD python -c "import os, uvicorn; port = int(os.getenv('PORT', '8000')); uvicorn.run('backend.main:app', host='0.0.0.0', port=port, proxy_headers=True, forwarded_allow_ips='*')"
