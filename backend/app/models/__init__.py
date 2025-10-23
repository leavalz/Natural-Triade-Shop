from app.models.product import Product, ProductCategory
from app.models.user import User
from app.models.cart import CartItem
from app.models.order import Order, OrderItem, OrderStatus
from sqlalchemy.orm import configure_mappers, relationship

CartItem.user = relationship("User", back_populates="cart_items")
CartItem.product = relationship("Product", back_populates="cart_items")

Order.user = relationship("User", back_populates="orders")
Order.items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

OrderItem.order = relationship("Order", back_populates="items")
OrderItem.product = relationship("Product")

configure_mappers()

__all__ = [
    "Product", 
    "ProductCategory", 
    "User", 
    "CartItem", 
    "Order", 
    "OrderItem", 
    "OrderStatus"
]