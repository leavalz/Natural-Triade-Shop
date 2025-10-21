from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

class CartItem(Base):
     __tablename__ = "cart_items"
     id = Column(Integer, primary_key=True, index=True)
     user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
     product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
     quantity = Column(Integer, default=1, nullable=False)
     price_at_addition = Column(Float, nullable=False)
     created_at = Column(DateTime, default=datetime.now())

     @property
     def subtotal(self):
          return self.price_at_addition * self.quantity
     
     def __repr__(self):
          return f"<CartItem(user_id={self.user_id}, product_id={self.product_id}, qty={self.quantity})>"