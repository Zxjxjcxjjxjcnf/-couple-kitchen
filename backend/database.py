from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import os

from .config import DATABASE_URL

# 创建异步引擎
# 连接池调小一点，Railway 免费版连接数有限
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # 连接前检查是否有效
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """初始化数据库：建表 + 迁移"""
    import aiomysql

    is_railway = bool(os.getenv("DATABASE_URL"))

    if not is_railway:
        # 本地开发：先确保数据库存在
        try:
            conn = await aiomysql.connect(
                host="127.0.0.1",
                port=3306,
                user="root",
                password="82512314dw",
                autocommit=True,
            )
            cur = await conn.cursor()
            await cur.execute(
                "CREATE DATABASE IF NOT EXISTS couple_kitchen "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            await cur.close()
            conn.close()
            print("[DB] 本地数据库已就绪")
        except Exception as e:
            print(f"[DB] 本地建库跳过: {e}")

    # 创建所有表
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[DB] 表结构已同步")
    except Exception as e:
        print(f"[DB] 建表失败: {e}")
        print("[DB] 请检查 DATABASE_URL 是否正确，以及数据库是否可访问")
        raise  # 让应用启动失败，Railway 会显示错误日志

    # 迁移：添加 image_url 列（如果尚不存在）
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("ALTER TABLE menu_items ADD COLUMN image_url VARCHAR(500) DEFAULT ''")
            )
        print("[DB] 已添加 image_url 列")
    except Exception:
        pass  # 列已存在，忽略

    print("[DB] 数据库初始化完成")


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
