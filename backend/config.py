import os
from dotenv import load_dotenv

# 加载 .env 文件（本地开发用，Railway 上不存在也不影响）
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# 优先级：
# 1. Railway 注入的 DATABASE_URL
# 2. 自定义环境变量 COUPLE_DATABASE_URL
# 3. 本地 MySQL 配置（兜底）
_raw_url = os.getenv("DATABASE_URL", "")

if _raw_url:
    # Railway 给的 URL 是 mysql://...，aiomysql 需要 mysql+aiomysql://
    if _raw_url.startswith("mysql://"):
        _raw_url = _raw_url.replace("mysql://", "mysql+aiomysql://", 1)
    elif _raw_url.startswith("mysql+aiomysql://"):
        pass  # 格式已正确
    else:
        pass  # 非 MySQL 数据库，保持原样
    DATABASE_URL = _raw_url
else:
    # 本地开发用默认配置
    DATABASE_URL = "mysql+aiomysql://root:82512314dw@127.0.0.1:3306/couple_kitchen"

# 允许通过环境变量覆盖
DATABASE_URL = os.getenv("COUPLE_DATABASE_URL", DATABASE_URL)

print(f"[配置] DATABASE_URL 已设置（{'来自环境变量' if _raw_url else '本地默认'}）")
