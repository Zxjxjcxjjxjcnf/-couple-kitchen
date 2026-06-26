# 情侣私厨 — 生产环境 Docker 镜像
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（aiomysql 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 缓存
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制全部项目代码
COPY . .

# 创建上传目录
RUN mkdir -p backend/uploads

# 启动
CMD python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'
