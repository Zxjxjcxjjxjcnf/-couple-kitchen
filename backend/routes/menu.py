import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..database import get_session
from ..models import MenuItem
from ..schemas import MenuItemOut, MenuItemCreate

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/api/menu", tags=["菜单"])


@router.get("", response_model=List[MenuItemOut])
async def get_menu(session: AsyncSession = Depends(get_session)):
    """获取所有菜单项"""
    result = await session.execute(select(MenuItem).order_by(MenuItem.category, MenuItem.id))
    items = result.scalars().all()
    return items


@router.post("", response_model=MenuItemOut)
async def create_menu_item(item: MenuItemCreate, session: AsyncSession = Depends(get_session)):
    """新增菜单项"""
    db_item = MenuItem(**item.model_dump())
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item


@router.post("/{item_id}/image")
async def upload_menu_image(item_id: int, file: UploadFile = File(...)):
    """上传菜品图片"""
    # 校验文件类型
    ext = os.path.splitext(file.filename or "image.jpg")[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/gif/webp 格式")

    # 生成唯一文件名
    filename = f"dish_{item_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # 保存文件
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # 更新数据库中的 image_url
    from sqlalchemy import update
    from ..database import async_session

    image_url = f"/uploads/{filename}"
    async with async_session() as session:
        await session.execute(
            update(MenuItem).where(MenuItem.id == item_id).values(image_url=image_url)
        )
        await session.commit()

    return {"image_url": image_url, "filename": filename}
