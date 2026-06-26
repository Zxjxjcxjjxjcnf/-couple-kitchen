from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .database import init_db, async_session
from .models import MenuItem
from .seed import SEED_MENU
from .routes.menu import router as menu_router
from .routes.orders import router as orders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭生命周期"""
    print("❤️ 情侣私厨 后端启动中...")
    await init_db()
    await seed_menu_data()
    print("❤️ 情侣私厨 后端就绪 (http://localhost:8000)")
    yield
    print("❤️ 情侣私厨 后端关闭")


app = FastAPI(
    title="情侣私厨 API",
    description="❤️ 为爱下厨 — 情侣专属点餐系统",
    version="1.0.0",
    lifespan=lifespan,
)

# ---- CORS（允许前端跨域访问） ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 注册路由 ----
app.include_router(menu_router)
app.include_router(orders_router)

# ---- 静态文件（提供前端页面访问） ----
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)))
if os.path.exists(os.path.join(STATIC_DIR, "index.html")):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


# ---- 启动时写入预置菜单 ----
async def seed_menu_data():
    """如果数据库中没有菜单数据，写入预置数据"""
    from sqlalchemy import select, func

    async with async_session() as session:
        result = await session.execute(select(func.count(MenuItem.id)))
        count = result.scalar()

        if count == 0:
            for item_data in SEED_MENU:
                session.add(MenuItem(**item_data))
            await session.commit()
            print(f"[Seed] 已写入 {len(SEED_MENU)} 道预置菜品")
        else:
            print(f"[Seed] 菜单已存在 ({count} 道菜)，跳过初始化")
