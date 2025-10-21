from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.cart import CartItem
from app.models.product import Product
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
    CartSummary
)

router = APIRouter()

TAX_RATE = 0.19  # 19% IVA Chile

@router.post("/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    item_data: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(
        Product.id == item_data.product_id,
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado o no disponible"
        )
    
    if product.stock < item_data.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. Disponible: {product.stock}"
        )
    
    existing_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == item_data.product_id
    ).first()

    if existing_item:
       new_quantity = existing_item.quantity + item_data.quantity

       if product.stock < new_quantity:
           raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente. Disponible: {product.stock}, en carrito: {existing_item.quantity}"
            )
       
       existing_item.quantity = new_quantity
       db.commit()
       db.refresh(existing_item)

       return CartItemResponse(
            id=existing_item.id,
            product_id=existing_item.product_id,
            product_name=product.name,
            product_price=product.price,
            product_image_url=product.image_url,
            quantity=existing_item.quantity,
            price_at_addition=existing_item.price_at_addition,
            subtotal=existing_item.subtotal
        )
    
    cart_item = CartItem(
        user_id=current_user.id,
        product_id=item_data.product_id,
        quantity=item_data.quantity,
        price_at_addition=product.price
    )
    
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)

    return CartItemResponse(
        id=cart_item.id,
        product_id=cart_item.product_id,
        product_name=product.name,
        product_price=product.price,
        product_image_url=product.image_url,
        quantity=cart_item.quantity,
        price_at_addition=cart_item.price_at_addition,
        subtotal=cart_item.subtotal
    )
    
@router.get("/", response_model=CartSummary)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).options(joinedload(CartItem.product)).all()
    
    items_response = []
    subtotal = 0

    for item in cart_items:
        if item.product and item.product.is_active:
            item_response = CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name,
                product_price=item.product.price,
                product_image_url=item.product.image_url,
                quantity=item.quantity,
                price_at_addition=item.price_at_addition,
                subtotal=item.subtotal
            )
            items_response.append(item_response)
            subtotal += item.subtotal
    
    tax = subtotal * TAX_RATE
    total = subtotal + tax

    return CartSummary(
        items=items_response,
        subtotal=round(subtotal, 2),
        tax=round(tax, 2),
        total=round(total, 2),
        items_count=len(items_response)
    )

@router.put("/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(
    item_id: int,
    item_update: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Item no encontrado en el carrito"
        )
    
    product = db.query(Product).filter(Product.id == cart_item.product_id).first()

    if not product or not product.is_active:
        raise HTTPException(
            status_code=400,
            detail="Producto no disponible"
        )
    if product.stock < item_update.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. Disponible: {product.stock}"
        )
    
    cart_item.quantity = item_update.quantity
    db.commit()
    db.refresh(cart_item)
    
    return CartItemResponse(
        id=cart_item.id,
        product_id=cart_item.product_id,
        product_name=product.name,
        product_price=product.price,
        product_image_url=product.image_url,
        quantity=cart_item.quantity,
        price_at_addition=cart_item.price_at_addition,
        subtotal=cart_item.subtotal
    )

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Item no encontrado en el carrito"
        )
    
    db.delete(cart_item)
    db.commit()

    return None

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()

    return None