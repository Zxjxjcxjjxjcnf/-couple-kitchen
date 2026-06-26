import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ---- 调试：打印所有环境变量，找 MySQL 相关的 ----
print("[调试] 当前所有环境变量（仅 MySQL 相关）:")
for k, v in sorted(os.environ.items()):
    if "mysql" in k.lower() or "database" in k.lower() or "url" in k.lower():
        # 隐藏密码
        display = v
        if "@" in v:
            display = v.split("@")[0].split(":")[0] + ":***@" + v.split("@")[1]
        print(f"  {k} = {display[:120]}")

# ---- 数据库连接 URL 优先级 ----
# Railway MySQL 给的环境变量名可能有细微差异，全部查一遍
CANDIDATE_KEYS = [
    "MYSQL_URL",
    "MYSQL_PUBLIC_URL",
    "DATABASE_URL",
    "MYSQL_PRIVATE_URL",
    "MYSQL_HOST",
    "MYSQL_PORT",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "MYSQL_DATABASE",
]

_raw_url = ""
for key in CANDIDATE_KEYS:
    val = os.getenv(key, "")
    if val:
        print(f"[配置] 找到 {key} = {val[:80]}...")
        if key in ("MYSQL_HOST",):
            # 单独的 host/port/user/password/database，需要拼成 URL
            host = os.getenv("MYSQL_HOST", "localhost")
            port = os.getenv("MYSQL_PORT", "3306")
            user = os.getenv("MYSQL_USER", "root")
            pwd = os.getenv("MYSQL_PASSWORD", "")
            db = os.getenv("MYSQL_DATABASE", "couple_kitchen")
            _raw_url = f"mysql+aiomysql://{user}:{pwd}@{host}:{port}/{db}"
            print(f"[配置] 已拼接 URL: {_raw_url[:80]}...")
            break
        else:
            _raw_url = val
            break

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
