from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum


from app.core.database import Base

class OrderStatus(str, enum.Enum):
    PENDING = "pending"           # Orden creada, esperando pago
    PAID = "paid"                 # Pagada
    PROCESSING = "processing"     # En preparación
    SHIPPED = "shipped"           # Enviada
    DELIVERED = "delivered"       # Entregada
    CANCELLED = "cancelled"       # Cancelada

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    shipping_address = Column(Text, nullable=False)
    shipping_city = Column(String(100), nullable=False)
    shipping_postal_code = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    payment_method = Column(String(50), nullable=True)
    payment_id = Column(String(255), nullable=True)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, total={self.total}, status={self.status})>"
    
class OrderItem(Base):
     __tablename__ = "order_items"

     id = Column(Integer, primary_key=True, index=True)
     order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
     product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
     product_name = Column(String(300), nullable=False)
     product_description = Column(Text, nullable=True)
     product_image_url = Column(String(500), nullable=True)
     unit_price = Column(Float, nullable=False)
     quantity = Column(Integer, nullable=False)
     subtotal = Column(Float, nullable=False)
     order = relationship("Order", back_populates="items")
     product = relationship("Product")

     def __repr__(self):
        return f"<OrderItem(order_id={self.order_id}, product={self.product_name}, qty={self.quantity})>"