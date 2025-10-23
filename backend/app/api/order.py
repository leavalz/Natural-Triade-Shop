from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.cart import CartItem
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderSummary,
    OrderItemResponse
)

router = APIRouter()

TAX_RATE = 0.19

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    # 1. Obtener items del carrito
    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).options(joinedload(CartItem.product)).all()
    
    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="El carrito está vacío. Agrega productos antes de hacer checkout."
        )
    
    # 2. Verificar stock y calcular totales
    subtotal = 0
    order_items_data = []
    
    for cart_item in cart_items:
        product = cart_item.product
        
        # Verificar que el producto existe y está activo
        if not product or not product.is_active:
            raise HTTPException(
                status_code=400,
                detail=f"El producto '{cart_item.product.name if product else 'desconocido'}' ya no está disponible"
            )
        
        # Verificar stock suficiente
        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para '{product.name}'. Disponible: {product.stock}, solicitado: {cart_item.quantity}"
            )
        
        # Calcular subtotal del item (usar precio actual del producto)
        item_subtotal = product.price * cart_item.quantity
        subtotal += item_subtotal
        
        # Guardar data para crear OrderItems después
        order_items_data.append({
            'product': product,
            'quantity': cart_item.quantity,
            'unit_price': product.price,
            'subtotal': item_subtotal
        })
    
    # 3. Calcular impuestos y total
    tax = subtotal * TAX_RATE
    total = subtotal + tax
    
    # 4. Crear la orden
    new_order = Order(
        user_id=current_user.id,
        subtotal=round(subtotal, 2),
        tax=round(tax, 2),
        total=round(total, 2),
        status=OrderStatus.PENDING,
        shipping_address=order_data.shipping_address,
        shipping_city=order_data.shipping_city,
        shipping_postal_code=order_data.shipping_postal_code,
        contact_email=order_data.contact_email,
        contact_phone=order_data.contact_phone,
        payment_method=order_data.payment_method
    )
    
    db.add(new_order)
    db.flush() # Para obtener el ID de la orden sin hacer commit aún

    # 5. Crear los items de la orden y reducir stock
    for item_data in order_items_data:
        product = item_data['product']
        
        # Crear OrderItem con snapshot del producto
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            product_name=product.name,
            product_description=product.description,
            product_image_url=product.image_url,
            unit_price=item_data['unit_price'],
            quantity=item_data['quantity'],
            subtotal=item_data['subtotal']
        )
        
        db.add(order_item)
        
        # Reducir stock del producto
        product.stock -= item_data['quantity']

    # 6. Vaciar el carrito
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()

    # 7. Hacer commit de todo
    db.commit()
    db.refresh(new_order)

    # 8. Preparar respuesta con items
    return OrderResponse(
        id=new_order.id,
        user_id=new_order.user_id,
        subtotal=new_order.subtotal,
        tax=new_order.tax,
        total=new_order.total,
        status=new_order.status,
        shipping_address=new_order.shipping_address,
        shipping_city=new_order.shipping_city,
        shipping_postal_code=new_order.shipping_postal_code,
        contact_email=new_order.contact_email,
        contact_phone=new_order.contact_phone,
        created_at=new_order.created_at,
        updated_at=new_order.updated_at,
        paid_at=new_order.paid_at,
        shipped_at=new_order.shipped_at,
        delivered_at=new_order.delivered_at,
        cancelled_at=new_order.cancelled_at,
        payment_method=new_order.payment_method,
        payment_id=new_order.payment_id,
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                product_description=item.product_description,
                product_image_url=item.product_image_url,
                unit_price=item.unit_price,
                quantity=item.quantity,
                subtotal=item.subtotal
            )
            for item in new_order.items
        ]
    )

@router.get("/", response_model=List[OrderSummary])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).options(joinedload(Order.items)).order_by(Order.created_at.desc()).all()

    return [
        OrderSummary(
            id=order.id,
            status=order.status,
            total=order.total,
            items_count=len(order.items),
            created_at=order.created_at
        )
        for order in orders
    ]

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id  # Seguridad: solo sus propias órdenes
    ).options(joinedload(Order.items)).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Orden no encontrada"
        )
    
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        subtotal=order.subtotal,
        tax=order.tax,
        total=order.total,
        status=order.status,
        shipping_address=order.shipping_address,
        shipping_city=order.shipping_city,
        shipping_postal_code=order.shipping_postal_code,
        contact_email=order.contact_email,
        contact_phone=order.contact_phone,
        created_at=order.created_at,
        updated_at=order.updated_at,
        paid_at=order.paid_at,
        shipped_at=order.shipped_at,
        delivered_at=order.delivered_at,
        cancelled_at=order.cancelled_at,
        payment_method=order.payment_method,
        payment_id=order.payment_id,
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                product_description=item.product_description,
                product_image_url=item.product_image_url,
                unit_price=item.unit_price,
                quantity=item.quantity,
                subtotal=item.subtotal
            )
            for item in order.items
        ]
    )

@router.put("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).options(joinedload(Order.items)).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Orden no encontrada"
        )
    
    # Verificar que se puede cancelar
    if order.status not in [OrderStatus.PENDING, OrderStatus.PAID]:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede cancelar una orden con status '{order.status.value}'"
        )
    
    # Devolver stock a los productos
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
    
    # Actualizar status de la orden
    order.status = OrderStatus.CANCELLED
    order.cancelled_at = datetime.now()
    
    db.commit()
    db.refresh(order)

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        subtotal=order.subtotal,
        tax=order.tax,
        total=order.total,
        status=order.status,
        shipping_address=order.shipping_address,
        shipping_city=order.shipping_city,
        shipping_postal_code=order.shipping_postal_code,
        contact_email=order.contact_email,
        contact_phone=order.contact_phone,
        created_at=order.created_at,
        updated_at=order.updated_at,
        paid_at=order.paid_at,
        shipped_at=order.shipped_at,
        delivered_at=order.delivered_at,
        cancelled_at=order.cancelled_at,
        payment_method=order.payment_method,
        payment_id=order.payment_id,
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                product_description=item.product_description,
                product_image_url=item.product_image_url,
                unit_price=item.unit_price,
                quantity=item.quantity,
                subtotal=item.subtotal
            )
            for item in order.items
        ]
    )