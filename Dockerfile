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

# main.py 内部读取 $PORT 环境变量，不需要 shell 展开
CMD python -m backend.main
