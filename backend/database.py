from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """创建数据库（如果不存在）并初始化表结构"""
    import aiomysql

    # 先连接 MySQL（不指定数据库）创建数据库
    conn = await aiomysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="82512314dw",
        autocommit=True,
    )
    cur = await conn.cursor()
    await cur.execute("CREATE DATABASE IF NOT EXISTS couple_kitchen CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    await cur.close()
    conn.close()

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("[DB] 数据库初始化完成")


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
