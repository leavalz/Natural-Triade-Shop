from pydantic import BaseModel, Field
from typing import List

class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_price: float
    product_image_url: str | None
    quantity: int
    price_at_addition: float
    subtotal: float

    class Config:
        from_attributes = True

class CartSummary(BaseModel):
    items: List[CartItemResponse]
    subtotal: float
    tax: float
    total: float
    items_count: int