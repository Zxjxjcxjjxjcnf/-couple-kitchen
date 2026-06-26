# 情侣私厨 — 生产环境 Docker 镜像
# Railway 会自动检测此文件并使用 Docker 构建
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制全部代码
COPY . .

# 创建上传目录
RUN mkdir -p backend/uploads

# 确保 start.sh 可执行
RUN chmod +x start.sh

# 直接用 python -m uvicorn 启动（$PORT 由 Railway 注入）
CMD python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'
