from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ============ 菜单 ============
class MenuItemCreate(BaseModel):
    category: str
    name: str
    price: float
    emoji: str = "🍽️"
    description: str = ""
    sold: int = 0
    bg: str = ""


class MenuItemOut(BaseModel):
    id: int
    category: str
    name: str
    price: float
    emoji: str
    description: str
    sold: int
    bg: str = ""
    image_url: str = ""

    class Config:
        from_attributes = True


# ============ 订单项 ============
class OrderItemCreate(BaseModel):
    id: int
    name: str
    price: float
    qty: int = 1
    emoji: str = ""
    note: str = ""


class OrderItemOut(BaseModel):
    id: int
    order_id: str
    menu_item_id: Optional[int] = None
    name: str
    price: float
    qty: int
    emoji: str
    note: str

    class Config:
        from_attributes = True


# ============ 订单 ============
class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    note: str = ""


class OrderStatusUpdate(BaseModel):
    status: str  # accepted | cooking | completed | cancelled


class OrderOut(BaseModel):
    id: str
    status: str
    note: str = ""
    total: float
    guest_note: str = ""
    chef_note: str = ""
    created_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    items: List[OrderItemOut] = []

    class Config:
        from_attributes = True


# ============ WebSocket ============
class WSMessage(BaseModel):
    type: str  # "order_new" | "order_update" | "subscribe"
    role: Optional[str] = None  # "guest" | "chef"
    data: Optional[dict] = None
    order_id: Optional[str] = None
