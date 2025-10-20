from sqlalchemy import Column, Integer, String, Float, Boolean, Enum
import enum
from app.core.database import Base

class ProductCategory(str, enum.Enum):
    FACIAL = "facial"
    CORPORAL = "corporal"
    CABELLO = "cabello"

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False)
    description = Column(String(600), nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    category = Column(Enum(ProductCategory), nullable=True)