from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session  
from typing import List

from app.core.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse, ProductCategoryEnum

router = APIRouter()

@router.get("/", response_model=List[ProductResponse]) #Obtener todos los productos activos
def get_products(
    db: Session = Depends(get_db),
    category: ProductCategoryEnum | None = None
):
    query = db.query(Product).filter(Product.is_active == True)

    if category:
        query = query.filter(Product.category == category.value)

    return query.all()

@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    db_product  = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product