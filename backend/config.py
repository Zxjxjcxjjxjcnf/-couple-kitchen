import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Railway 会自动注入 DATABASE_URL（格式：mysql://user:pass@host:port/db）
# 本地开发则使用本地的 MySQL
_raw_url = os.getenv("DATABASE_URL", "")

if _raw_url:
    # Railway 给的 URL 是 mysql://...，但 aiomysql 需要 mysql+aiomysql://
    if _raw_url.startswith("mysql://"):
        _raw_url = _raw_url.replace("mysql://", "mysql+aiomysql://", 1)
    elif _raw_url.startswith("mysql+aiomysql://"):
        pass  # 格式正确
    else:
        # 其他数据库，保持原样
        pass
    DATABASE_URL = _raw_url
else:
    # 本地开发：用硬编码的 MySQL 配置
    DATABASE_URL = "mysql+aiomysql://root:82512314dw@127.0.0.1:3306/couple_kitchen"

# 阿里云 / 自定义 MySQL 可以通过这个环境变量覆盖
DATABASE_URL = os.getenv("COUPLE_DATABASE_URL", DATABASE_URL)
