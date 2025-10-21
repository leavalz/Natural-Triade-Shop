from app.models.product import Product, ProductCategory
from app.models.user import User
from app.models.cart import CartItem
from sqlalchemy.orm import configure_mappers, relationship

CartItem.user = relationship("User", back_populates="cart_items")
CartItem.product = relationship("Product", back_populates="cart_items")

configure_mappers()

__all__ = ["Product", "ProductCategory", "User","CartItem"]