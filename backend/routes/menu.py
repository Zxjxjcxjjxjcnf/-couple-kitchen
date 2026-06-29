import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List

from ..database import get_session, engine
from ..models import MenuItem
from ..schemas import MenuItemOut, MenuItemCreate
from ..seed import SEED_MENU

router = APIRouter(prefix="/api/menu", tags=["菜单"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

_memory_menu = []
_db_menu_cache = []  # 最后一次从数据库读到的菜单

def _get_fallback_menu():
    """数据库不可用时的降级菜单"""
    if _memory_menu:
        return _memory_menu
    return [dict(item, id=idx+1) for idx, item in enumerate(SEED_MENU)]


async def _check_db():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@router.get("", response_model=List[MenuItemOut])
async def get_menu(session: AsyncSession = Depends(get_session)):
    """获取所有菜单项"""
    try:
        if await _check_db():
            result = await session.execute(select(MenuItem).order_by(MenuItem.category, MenuItem.id))
            items = result.scalars().all()
            _memory_menu.clear()
            for item in items:
                _memory_menu.append({
                    "id": item.id, "category": item.category, "name": item.name,
                    "price": float(item.price), "emoji": item.emoji or "",
                    "description": item.description or "", "sold": item.sold or 0,
                    "bg": item.bg or "", "image_url": item.image_url or "",
                })
            return items
    except Exception:
        pass

    return _get_fallback_menu()


@router.post("", response_model=MenuItemOut)
async def create_menu_item(item: MenuItemCreate, session: AsyncSession = Depends(get_session)):
    """新增菜单项"""
    try:
        if await _check_db():
            db_item = MenuItem(**item.model_dump())
            session.add(db_item)
            await session.commit()
            await session.refresh(db_item)
            return db_item
    except Exception:
        pass

    # 内存降级
    new_id = max((i["id"] for i in _get_fallback_menu()), default=0) + 1
    entry = {"id": new_id, **item.model_dump(), "image_url": ""}
    _memory_menu.append(entry)
    return entry


@router.post("/{item_id}/image")
async def upload_menu_image(item_id: int, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "image.jpg")[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/gif/webp 格式")

    import uuid
    filename = f"dish_{item_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    image_url = f"/uploads/{filename}"

    try:
        if await _check_db():
            from ..database import async_session
            await session.execute(update(MenuItem).where(MenuItem.id == item_id).values(image_url=image_url))
            await session.commit()
    except Exception:
        for item in _memory_menu:
            if item["id"] == item_id:
                item["image_url"] = image_url

    return {"image_url": image_url, "filename": filename}
