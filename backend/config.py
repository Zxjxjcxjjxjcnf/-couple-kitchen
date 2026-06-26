import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ---- 数据库连接 URL 优先级 ----
# 1. Railway 注入的 MYSQL_URL（也可能是 DATABASE_URL）
# 2. Railway 注入的 MYSQL_PUBLIC_URL
# 3. 自定义环境变量 COUPLE_DATABASE_URL
# 4. 本地 MySQL 配置（兜底）

_raw_url = (
    os.getenv("MYSQL_URL")
    or os.getenv("DATABASE_URL")
    or os.getenv("MYSQL_PUBLIC_URL")
    or ""
)

if _raw_url:
    # Railway 给的 URL 是 mysql://...，aiomysql 需要 mysql+aiomysql://
    if _raw_url.startswith("mysql://"):
        _raw_url = _raw_url.replace("mysql://", "mysql+aiomysql://", 1)
        print(f"[配置] 从环境变量读取到 MYSQL_URL（已转换格式）")
    elif _raw_url.startswith("mysql+aiomysql://"):
        print(f"[配置] 从环境变量读取到 DATABASE_URL")
    else:
        print(f"[配置] 从环境变量读取到其他数据库 URL")
    DATABASE_URL = _raw_url
else:
    # 本地开发用默认配置
    DATABASE_URL = "mysql+aiomysql://root:82512314dw@127.0.0.1:3306/couple_kitchen"
    print("[配置] 未找到环境变量，使用本地 MySQL")

# 允许通过自定义变量覆盖
DATABASE_URL = os.getenv("COUPLE_DATABASE_URL", DATABASE_URL)
