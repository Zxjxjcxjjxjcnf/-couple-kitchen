from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..database import get_session
from ..models import MenuItem
from ..schemas import MenuItemOut, MenuItemCreate

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
