from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session  
from typing import List, Optional

from app.core.database import get_db
from app.models.product import Product, ProductCategory
from app.schemas.product import (
    ProductCreate, 
    ProductResponse, 
    ProductCategoryEnum,
    ProductUpdate
)

router = APIRouter()

@router.get("/", response_model=List[ProductResponse]) #Obtener todos los productos activos
def get_products(
    db: Session = Depends(get_db),
    category: Optional[ProductCategoryEnum] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0)
):
    query = db.query(Product).filter(Product.is_active == True)

    if category: #Filtrar por categoria
        query = query.filter(Product.category == category.value)

    if search: #Busqueda por nombre y descripcion
        search_term = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_term)) |
            (Product.description.ilike(search_term))
        )
    
    if min_price is not None: #Filtrar por precio
        query = query.filter(Product.price >= min_price)

    if max_price is not None: 
        query = query.filter(Product.price <= max_price)

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
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    product.is_active = False
    db.commit()
    return None
    