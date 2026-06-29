import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..database import get_session, engine
from ..models import Order, OrderItem, MenuItem
from ..schemas import OrderOut, OrderCreate, OrderStatusUpdate
from ..websocket_manager import manager

router = APIRouter(prefix="/api/orders", tags=["订单"])

# ---- 内存降级存储（数据库不可用时自动使用） ----
_memory_orders: list = []
_db_available = True

async def _check_db():
    """检查数据库是否可用"""
    global _db_available
    try:
        async with engine.connect() as conn:
            await conn.execute(select(1))
        _db_available = True
    except Exception:
        _db_available = False
    return _db_available


@router.get("", response_model=List[OrderOut])
async def get_orders(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """获取订单列表"""
    global _memory_orders

    try:
        if await _check_db():
            query = select(Order).order_by(desc(Order.created_at))
            if status:
                query = query.where(Order.status == status)
            result = await session.execute(query)
            orders = result.scalars().all()
            for o in orders:
                await session.refresh(o, ["items"])
            return orders
    except Exception as e:
        print(f"[Orders] 数据库查询失败，使用内存存储: {e}")

    # 内存降级
    filtered = [o for o in _memory_orders if status is None or o["status"] == status]
    return sorted(filtered, key=lambda x: x.get("created_at", ""), reverse=True)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: str, session: AsyncSession = Depends(get_session)):
    global _memory_orders
    try:
        if await _check_db():
            result = await session.execute(select(Order).where(Order.id == order_id))
            order = result.scalar_one_or_none()
            if not order:
                raise HTTPException(status_code=404, detail="订单不存在")
            await session.refresh(order, ["items"])
            return order
    except HTTPException:
        raise
    except Exception:
        pass

    for o in _memory_orders:
        if o["id"] == order_id:
            return o
    raise HTTPException(status_code=404, detail="订单不存在")


@router.post("", response_model=OrderOut)
async def create_order(data: OrderCreate, session: AsyncSession = Depends(get_session)):
    """创建新订单"""
    global _memory_orders
    order_id = uuid.uuid4().hex[:8].upper()

    try:
        if await _check_db():
            total = Decimal("0")
            order_items = []
            for item_data in data.items:
                price = Decimal(str(item_data.price))
                qty = item_data.qty
                subtotal = price * qty
                total += subtotal
                order_items.append(OrderItem(
                    menu_item_id=item_data.id,
                    name=item_data.name,
                    price=price, qty=qty,
                    emoji=item_data.emoji, note=item_data.note,
                ))
                # 更新销量
                r = await session.execute(select(MenuItem).where(MenuItem.id == item_data.id))
                mi = r.scalar_one_or_none()
                if mi:
                    mi.sold = (mi.sold or 0) + qty

            order = Order(id=order_id, note=data.note, total=total, created_at=datetime.now(), items=order_items)
            session.add(order)
            await session.commit()
            await session.refresh(order, ["items"])
            order_data = _order_to_dict(order)
            await _broadcast_new(order_data)
            return order
    except Exception as e:
        print(f"[Orders] 数据库写入失败，使用内存存储: {e}")

    # 内存降级
    total = sum(item.price * item.qty for item in data.items)
    order_data = {
        "id": order_id,
        "status": "pending",
        "note": data.note or "",
        "total": total,
        "guest_note": "",
        "chef_note": "",
        "created_at": datetime.now().isoformat(),
        "accepted_at": None,
        "completed_at": None,
        "items": [
            {"id": 0, "order_id": order_id, "menu_item_id": item.id,
             "name": item.name, "price": item.price, "qty": item.qty,
             "emoji": item.emoji or "", "note": item.note or ""}
            for item in data.items
        ],
    }
    _memory_orders.append(order_data)
    await _broadcast_new(order_data)
    return order_data


@router.put("/{order_id}/status", response_model=OrderOut)
async def update_order_status(order_id: str, update: OrderStatusUpdate, session: AsyncSession = Depends(get_session)):
    global _memory_orders
    try:
        if await _check_db():
            result = await session.execute(select(Order).where(Order.id == order_id))
            order = result.scalar_one_or_none()
            if not order:
                raise HTTPException(status_code=404, detail="订单不存在")
            now = datetime.now()
            order.status = update.status
            if update.status == "accepted":
                order.accepted_at = now
            elif update.status == "completed":
                order.completed_at = now
            elif update.status == "cancelled":
                order.completed_at = now
            await session.commit()
            await session.refresh(order, ["items"])
            order_data = _order_to_dict(order)
            await _broadcast_update(order_data)
            return order
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Orders] 数据库更新失败，使用内存存储: {e}")

    for o in _memory_orders:
        if o["id"] == order_id:
            o["status"] = update.status
            now = datetime.now().isoformat()
            if update.status == "accepted":
                o["accepted_at"] = now
            elif update.status == "completed":
                o["completed_at"] = now
            elif update.status == "cancelled":
                o["completed_at"] = now
            await _broadcast_update(o)
            return o
    raise HTTPException(status_code=404, detail="订单不存在")


# ============ WebSocket ============

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    role = "guest"
    try:
        await ws.accept()
        raw = await ws.receive_text()
        msg = json.loads(raw)
        if msg.get("type") == "subscribe" and msg.get("role") in ("guest", "chef"):
            role = msg["role"]
        manager.connections[role].add(ws)
        print(f"[WS] {role} 已订阅 (共 {len(manager.connections[role])} 个)")
        while True:
            try:
                data = await ws.receive_text()
                if data == "ping":
                    await ws.send_text("pong")
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS] 连接异常: {e}")
    finally:
        manager.connections[role].discard(ws)


async def _broadcast_new(order_data: dict):
    await manager.broadcast_to_role("chef", {"type": "order_new", "data": order_data})
    await manager.broadcast_to_role("guest", {"type": "order_new", "data": order_data})


async def _broadcast_update(order_data: dict):
    await manager.broadcast_to_role("chef", {"type": "order_update", "data": order_data})
    await manager.broadcast_to_role("guest", {"type": "order_update", "data": order_data})


def _order_to_dict(order) -> dict:
    return {
        "id": order.id,
        "status": order.status,
        "note": order.note or "",
        "total": float(order.total or 0),
        "guest_note": order.guest_note or "",
        "chef_note": order.chef_note or "",
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "accepted_at": order.accepted_at.isoformat() if order.accepted_at else None,
        "completed_at": order.completed_at.isoformat() if order.completed_at else None,
        "items": [
            {"id": item.id, "order_id": item.order_id, "menu_item_id": item.menu_item_id,
             "name": item.name, "price": float(item.price), "qty": item.qty,
             "emoji": item.emoji or "", "note": item.note or ""}
            for item in order.items
        ],
    }
