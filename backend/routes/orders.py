from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from ..database import get_session
from ..models import Order, OrderItem, MenuItem
from ..schemas import OrderOut, OrderCreate, OrderStatusUpdate
from ..websocket_manager import manager

router = APIRouter(prefix="/api/orders", tags=["订单"])


@router.get("", response_model=List[OrderOut])
async def get_orders(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """获取订单列表，可选按状态筛选"""
    query = select(Order).order_by(desc(Order.created_at))
    if status:
        query = query.where(Order.status == status)
    result = await session.execute(query)
    orders = result.scalars().all()

    # 确保 items 被加载
    for o in orders:
        await session.refresh(o, ["items"])

    return orders


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: str, session: AsyncSession = Depends(get_session)):
    """获取单个订单详情"""
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    await session.refresh(order, ["items"])
    return order


@router.post("", response_model=OrderOut)
async def create_order(data: OrderCreate, session: AsyncSession = Depends(get_session)):
    """创建新订单"""
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
            price=price,
            qty=qty,
            emoji=item_data.emoji,
            note=item_data.note,
        ))

        # 更新销量
        result = await session.execute(select(MenuItem).where(MenuItem.id == item_data.id))
        menu_item = result.scalar_one_or_none()
        if menu_item:
            menu_item.sold = (menu_item.sold or 0) + qty

    order = Order(
        note=data.note,
        total=total,
        created_at=datetime.now(),
        items=order_items,
    )

    session.add(order)
    await session.commit()
    await session.refresh(order, ["items"])

    # 广播给所有厨师端
    order_data = _order_to_dict(order)
    await manager.broadcast_to_role("chef", {
        "type": "order_new",
        "data": order_data,
    })

    # 也广播给客人端（同设备多标签）
    await manager.broadcast_to_role("guest", {
        "type": "order_new",
        "data": order_data,
    })

    return order


@router.put("/{order_id}/status", response_model=OrderOut)
async def update_order_status(
    order_id: str,
    update: OrderStatusUpdate,
    session: AsyncSession = Depends(get_session),
):
    """更新订单状态（接单/完成/取消等）"""
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

    # 广播状态更新
    order_data = _order_to_dict(order)
    await manager.broadcast_to_role("chef", {
        "type": "order_update",
        "data": order_data,
    })
    await manager.broadcast_to_role("guest", {
        "type": "order_update",
        "data": order_data,
    })

    return order


# ============ WebSocket 实时通信 ============

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket 连接：客户端连接后发送 {"type":"subscribe","role":"chef|guest"}"""
    role = "guest"

    try:
        # 先接受连接
        await ws.accept()

        # 等待订阅消息
        raw = await ws.receive_text()
        import json
        msg = json.loads(raw)

        if msg.get("type") == "subscribe" and msg.get("role") in ("guest", "chef"):
            role = msg["role"]

        manager.connections[role].add(ws)
        print(f"[WS] {role} 已订阅 (共 {len(manager.connections[role])} 个)")

        # 保持连接，持续接收心跳
        while True:
            try:
                data = await ws.receive_text()
                # 心跳响应
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
        print(f"[WS] {role} 已断开 (剩余 {len(manager.connections[role])} 个)")


def _order_to_dict(order: Order) -> dict:
    """将 Order ORM 对象转为字典"""
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
            {
                "id": item.id,
                "order_id": item.order_id,
                "menu_item_id": item.menu_item_id,
                "name": item.name,
                "price": float(item.price),
                "qty": item.qty,
                "emoji": item.emoji or "",
                "note": item.note or "",
            }
            for item in order.items
        ],
    }
