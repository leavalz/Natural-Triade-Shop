from pydantic import BaseModel

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    stock: int = 0

class ProductCreate(ProductBase):
    pass

class ProductResponse (ProductBase):
    id: int 
    is_active: bool

    class Config: 
        from_attributes = True
