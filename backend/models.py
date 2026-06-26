import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Enum, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from .database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    emoji = Column(String(10), default="🍽️")
    description = Column(String(200), default="")
    sold = Column(Integer, default=0)
    bg = Column(String(200), default="")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()).upper()[:8])
    status = Column(Enum("pending", "accepted", "cooking", "completed", "cancelled"),
                    default="pending", nullable=False, index=True)
    note = Column(Text, default="")
    total = Column(DECIMAL(10, 2), default=0)
    guest_note = Column(Text, default="")
    chef_note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    menu_item_id = Column(Integer, nullable=True)
    name = Column(String(100), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    qty = Column(Integer, default=1)
    emoji = Column(String(10), default="")
    note = Column(Text, default="")

    order = relationship("Order", back_populates="items")
