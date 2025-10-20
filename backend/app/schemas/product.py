from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List

class ProductCategoryEnum(str, Enum):
    FACIAL = "facial"
    CORPORAL = "corporal"
    CABELLO = "cabello"

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str
    price: float  = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    category: Optional[ProductCategoryEnum] = None 
    image_url: Optional[str] = None
    image_urls: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[ProductCategoryEnum] = None 
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int 
    is_active: bool

    class Config: 
        from_attributes = True
