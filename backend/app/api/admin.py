from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.user import User
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.admin import (
    DashboardData,
    SalesMetrics,
    TopProduct,
    RecentOrder,
    OrderStatusUpdate
)
from app.schemas.order import OrderResponse, OrderItemResponse
from app.schemas.product import ProductResponse


router = APIRouter()

@router.get("/dashboard", response_model=DashboardData)
def get_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Dashboard con métricas principales para admin
    
    Incluye:
    - Métricas generales (revenue, órdenes)
    - Top 5 productos más vendidos
    - Últimas 10 órdenes
    - Productos con stock bajo (< 5 unidades)
    """
    
    # 1. Métricas generales de ventas
    total_orders = db.query(func.count(Order.id)).scalar()
    
    pending_orders = db.query(func.count(Order.id)).filter(
        Order.status == OrderStatus.PENDING
    ).scalar()
    
    paid_orders = db.query(func.count(Order.id)).filter(
        Order.status == OrderStatus.PAID
    ).scalar()
    
    completed_orders = db.query(func.count(Order.id)).filter(
        Order.status == OrderStatus.DELIVERED
    ).scalar()
    
    cancelled_orders = db.query(func.count(Order.id)).filter(
        Order.status == OrderStatus.CANCELLED
    ).scalar()
    
    # Total revenue (solo órdenes pagadas y completadas)
    total_revenue = db.query(func.sum(Order.total)).filter(
        Order.status.in_([OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED])
    ).scalar() or 0
    
    # Average order value
    avg_order_value = total_revenue / paid_orders if paid_orders > 0 else 0
    
    metrics = SalesMetrics(
        total_revenue=round(total_revenue, 2),
        total_orders=total_orders,
        pending_orders=pending_orders,
        paid_orders=paid_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        average_order_value=round(avg_order_value, 2)
    )
    
    # 2. Top 5 productos más vendidos
    top_products_query = db.query(
        Product.id,
        Product.name,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.subtotal).label('total_revenue')
    ).join(OrderItem).join(Order).filter(
        Order.status.in_([OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED])
    ).group_by(Product.id, Product.name).order_by(desc('total_quantity')).limit(5).all()
    
    top_products = [
        TopProduct(
            product_id=p.id,
            product_name=p.name,
            total_quantity_sold=p.total_quantity,
            total_revenue=round(p.total_revenue, 2)
        )
        for p in top_products_query
    ]
    
    # 3. Últimas 10 órdenes
    recent_orders_query = db.query(Order).options(
        joinedload(Order.user),
        joinedload(Order.items)
    ).order_by(desc(Order.created_at)).limit(10).all()
    
    recent_orders = [
        RecentOrder(
            id=order.id,
            user_email=order.user.email,
            total=order.total,
            status=order.status.value,
            created_at=order.created_at,
            items_count=len(order.items)
        )
        for order in recent_orders_query
    ]
    
    # 4. Productos con stock bajo (< 5 unidades)
    low_stock_products = db.query(Product).filter(
        Product.stock < 5,
        Product.is_active == True
    ).all()
    
    low_stock = [
        {
            "id": p.id,
            "name": p.name,
            "stock": p.stock,
            "price": p.price
        }
        for p in low_stock_products
    ]
    
    return DashboardData(
        metrics=metrics,
        top_products=top_products,
        recent_orders=recent_orders,
        low_stock_products=low_stock
    )

@router.get("/orders", response_model=List[OrderResponse])
def get_all_orders(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    status: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Ver todas las órdenes (admin)
    
    Filtros opcionales:
    - status: Filtrar por estado
    - user_id: Filtrar por usuario
    - skip/limit: Paginación
    """
    
    query = db.query(Order).options(
        joinedload(Order.user),
        joinedload(Order.items)
    )
    
    # Aplicar filtros
    if status:
        try:
            order_status = OrderStatus(status)
            query = query.filter(Order.status == order_status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Estado inválido: {status}"
            )
    
    if user_id:
        query = query.filter(Order.user_id == user_id)
    
    # Ordenar por más reciente
    query = query.order_by(desc(Order.created_at))
    
    # Paginación
    orders = query.offset(skip).limit(limit).all()
    
    return [
        OrderResponse(
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
        for order in orders
    ]

@router.put("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Actualizar el estado de una orden (admin)
    
    Estados válidos:
    - paid: Marcada como pagada
    - processing: En preparación
    - shipped: Enviada
    - delivered: Entregada
    - cancelled: Cancelada
    """
    
    order = db.query(Order).options(joinedload(Order.items)).filter(
        Order.id == order_id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Orden no encontrada"
        )
    
    # Validar estado
    try:
        new_status = OrderStatus(status_update.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido: {status_update.status}"
        )
    
    # Validar transiciones de estado
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=400,
            detail="No se puede cambiar el estado de una orden cancelada"
        )
    
    if order.status == OrderStatus.DELIVERED and new_status != OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=400,
            detail="No se puede cambiar el estado de una orden entregada"
        )
    
    # Actualizar estado
    old_status = order.status
    order.status = new_status
    
    # Actualizar timestamps según el nuevo estado
    if new_status == OrderStatus.PAID and not order.paid_at:
        order.paid_at = datetime.now()
    
    elif new_status == OrderStatus.SHIPPED and not order.shipped_at:
        order.shipped_at = datetime.now()
    
    elif new_status == OrderStatus.DELIVERED and not order.delivered_at:
        order.delivered_at = datetime.now()
    
    elif new_status == OrderStatus.CANCELLED and not order.cancelled_at:
        order.cancelled_at = datetime.now()
        
        # Si se cancela, restaurar stock
        if old_status in [OrderStatus.PENDING, OrderStatus.PAID, OrderStatus.PROCESSING]:
            for item in order.items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    product.stock += item.quantity
    
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

@router.get("/products", response_model=List[ProductResponse])
def get_all_products_admin(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    include_inactive: bool = Query(False)
):
    """
    Ver todos los productos incluyendo inactivos (admin)
    """
    query = db.query(Product)
    
    if not include_inactive:
        query = query.filter(Product.is_active == True)
    
    products = query.all()
    return products

@router.get("/products/low-stock", response_model=List[ProductResponse])
def get_low_stock_products(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    threshold: int = Query(5, ge=1)
):
    """
    Ver productos con stock bajo (admin)
    
    threshold: Umbral de stock (default: 5)
    """
    products = db.query(Product).filter(
        Product.stock < threshold,
        Product.is_active == True
    ).all()
    
    return products

@router.get("/users", response_model=List[dict])
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Ver todos los usuarios (admin)
    """
    users = db.query(User).offset(skip).limit(limit).all()
    
    return [
        {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "last_login": user.last_login
        }
        for user in users
    ]


@router.get("/analytics/revenue")
def get_revenue_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    days: int = Query(30, ge=1, le=365)
):
    """
    Análisis de revenue por día (últimos N días)
    """
    from datetime import timedelta
    from sqlalchemy import cast, Date
    
    start_date = datetime.now() - timedelta(days=days)
    
    revenue_by_day = db.query(
        cast(Order.created_at, Date).label('date'),
        func.sum(Order.total).label('revenue'),
        func.count(Order.id).label('orders_count')
    ).filter(
        Order.created_at >= start_date,
        Order.status.in_([OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED])
    ).group_by('date').order_by('date').all()
    
    return [
        {
            "date": str(row.date),
            "revenue": float(row.revenue),
            "orders_count": row.orders_count
        }
        for row in revenue_by_day
    ]