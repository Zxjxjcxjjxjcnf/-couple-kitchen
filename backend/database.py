from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import os

from .config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """初始化数据库：建库（本地）→ 建表 → 迁移旧表"""
    import aiomysql

    # 判断是否在 Railway（有 DATABASE_URL 环境变量说明是部署环境）
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
            print("[DB] 数据库已就绪")
        except Exception as e:
            print(f"[DB] 建库跳过（可能已在 Railway）: {e}")

    # 创建所有表（如果不存在则创建，已存在则跳过）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[DB] 表结构已同步")

    # 迁移：给已存在的表添加 image_url 列（如果尚不存在）
    async with engine.begin() as conn:
        try:
            await conn.execute(
                text("ALTER TABLE menu_items ADD COLUMN image_url VARCHAR(500) DEFAULT ''")
            )
            print("[DB] 已添加 image_url 列")
        except Exception:
            pass  # 列已存在

    print("[DB] 数据库初始化完成")


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
