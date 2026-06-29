import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ---- 调试：打印所有环境变量，找 MySQL 相关的 ----
print("[调试] 当前所有环境变量（仅 MySQL 相关）:")
for k, v in sorted(os.environ.items()):
    if "mysql" in k.lower() or "database" in k.lower() or "url" in k.lower():
        display = v
        if "@" in v:
            display = v.split("@")[0].split(":")[0] + ":***@" + v.split("@")[1]
        print(f"  {k} = {display[:120]}")

# ---- 数据库连接 URL 优先级 ----
# 1. MYSQL_PUBLIC_URL（公网地址，不依赖内部 DNS）
# 2. MYSQL_URL / DATABASE_URL（内部地址，需要服务间联网）
# 3. 拼接 MYSQL_HOST + MYSQL_PORT + ...（分拆变量）
# 4. COUPLE_DATABASE_URL（自定义覆盖）
# 5. 本地 MySQL（兜底）

_raw_url = os.getenv("MYSQL_PUBLIC_URL", "")
if _raw_url:
    print("[配置] 使用 MYSQL_PUBLIC_URL（公网地址）")
else:
    _raw_url = os.getenv("MYSQL_URL", "") or os.getenv("DATABASE_URL", "") or ""
    if _raw_url:
        print("[配置] 使用 MYSQL_URL（内部地址）")
    else:
        # 尝试拼接
        host = os.getenv("MYSQL_HOST", "")
        if host:
            port = os.getenv("MYSQL_PORT", "3306")
            user = os.getenv("MYSQL_USER", "root")
            pwd = os.getenv("MYSQL_PASSWORD", "")
            db = os.getenv("MYSQL_DATABASE", "couple_kitchen")
            _raw_url = f"mysql://{user}:{pwd}@{host}:{port}/{db}"
            print("[配置] 通过 MYSQL_HOST/MYSQL_PORT 等拼接 URL")

if _raw_url:
    if _raw_url.startswith("mysql://"):
        _raw_url = _raw_url.replace("mysql://", "mysql+aiomysql://", 1)
    DATABASE_URL = _raw_url
    print(f"[配置] DATABASE_URL 已设置")
else:
    DATABASE_URL = "mysql+aiomysql://root:82512314dw@127.0.0.1:3306/couple_kitchen"
    print("[配置] 未找到环境变量，使用本地 MySQL")

DATABASE_URL = os.getenv("COUPLE_DATABASE_URL", DATABASE_URL)
