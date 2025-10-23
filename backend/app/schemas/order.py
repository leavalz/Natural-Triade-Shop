from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum

class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_description: Optional[str]
    product_image_url: Optional[str]
    unit_price: float
    quantity: int
    subtotal: float
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    shipping_address: str = Field(..., min_length=5, max_length=500)
    shipping_city: str = Field(..., min_length=2, max_length=100)
    shipping_postal_code: Optional[str] = Field(None, max_length=20)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=50)
    payment_method: Optional[str] = Field("pending", max_length=50)

class OrderResponse(BaseModel):
    id: int
    user_id: int
    subtotal: float
    tax: float
    total: float
    status: OrderStatusEnum
    shipping_address: str
    shipping_city: str
    shipping_postal_code: Optional[str]
    contact_email: str
    contact_phone: Optional[str]
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime]
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    payment_method: Optional[str]
    payment_id: Optional[str]
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

class OrderSummary(BaseModel):
    id: int
    status: OrderStatusEnum
    total: float
    items_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True