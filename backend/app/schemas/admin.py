from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SalesMetrics(BaseModel):
    """Métricas generales de ventas"""
    total_revenue: float
    total_orders: int
    pending_orders: int
    paid_orders: int
    completed_orders: int
    cancelled_orders: int
    average_order_value: float

class TopProduct(BaseModel):
    """Producto más vendido"""
    product_id: int
    product_name: str
    total_quantity_sold: int
    total_revenue: float

class RecentOrder(BaseModel):
    """Orden reciente para dashboard"""
    id: int
    user_email: str
    total: float
    status: str
    created_at: datetime
    items_count: int

class DashboardData(BaseModel):
    """Datos del dashboard admin"""
    metrics: SalesMetrics
    top_products: List[TopProduct]
    recent_orders: List[RecentOrder]
    low_stock_products: List[dict]  # Productos con stock bajo

class OrderStatusUpdate(BaseModel):
    """Update de estado de orden"""
    status: str  # 'paid', 'processing', 'shipped', 'delivered', 'cancelled'

class AllOrdersFilter(BaseModel):
    """Filtros para ver todas las órdenes"""
    status: Optional[str] = None
    user_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


