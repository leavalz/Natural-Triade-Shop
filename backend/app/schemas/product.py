from pydantic import BaseModel
from enum import Enum

class ProductCategoryEnum(str, Enum):
    FACIAL = "facial"
    CORPORAL = "corporal"
    CABELLO = "cabello"

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    stock: int = 0
    category: ProductCategoryEnum | None = None 

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int 
    is_active: bool

    class Config: 
        from_attributes = True
