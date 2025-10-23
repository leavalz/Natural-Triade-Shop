from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import stripe
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.schemas.payment import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentConfirmation
)
from app.services.stripe_service import StripeService

router = APIRouter()

@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
def create_payment_intent(
    payment_data: PaymentIntentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear un Payment Intent de Stripe para una orden
    
    Flujo:
    1. Verificar que la orden existe y pertenece al usuario
    2. Verificar que la orden está en estado PENDING
    3. Crear Payment Intent en Stripe
    4. Guardar payment_intent_id en la orden
    5. Retornar client_secret para el frontend
    """
    
    # 1. Buscar la orden
    order = db.query(Order).filter(
        Order.id == payment_data.order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Orden no encontrada"
        )
    
    # 2. Verificar estado de la orden
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede pagar una orden con estado '{order.status.value}'"
        )
    
    # 3. Si ya tiene un payment_intent_id, verificar su estado
    if order.payment_id:
        existing_pi = StripeService.retrieve_payment_intent(order.payment_id)
        
        if existing_pi and existing_pi.status in ['requires_payment_method', 'requires_confirmation']:
            # Reusar el Payment Intent existente
            return PaymentIntentResponse(
                client_secret=existing_pi.client_secret,
                payment_intent_id=existing_pi.id,
                amount=existing_pi.amount,
                currency=existing_pi.currency,
                order_id=order.id
            )
    
    # 4. Crear nuevo Payment Intent
    try:
        payment_intent = StripeService.create_payment_intent(order)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear Payment Intent: {str(e)}"
        )
    
    # 5. Guardar payment_intent_id en la orden
    order.payment_id = payment_intent.id
    order.payment_method = "stripe"
    db.commit()
    
    # 6. Retornar client_secret para el frontend
    return PaymentIntentResponse(
        client_secret=payment_intent.client_secret,
        payment_intent_id=payment_intent.id,
        amount=payment_intent.amount,
        currency=payment_intent.currency,
        order_id=order.id
    )

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """
    Webhook para recibir eventos de Stripe
    
    Este endpoint es llamado por Stripe cuando hay cambios en el pago:
    - payment_intent.succeeded: Pago exitoso
    - payment_intent.payment_failed: Pago fallido
    - payment_intent.canceled: Pago cancelado
    """
    
    if not stripe_signature:
        raise HTTPException(
            status_code=400,
            detail="Missing Stripe signature"
        )
    
    # Leer el payload raw
    payload = await request.body()
    
    # Verificar la firma del webhook
    try:
        event = StripeService.construct_webhook_event(
            payload, 
            stripe_signature
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
    # Procesar el evento
    event_type = event['type']
    
    if event_type == 'payment_intent.succeeded':
        # Pago exitoso
        payment_intent = event['data']['object']
        _handle_payment_succeeded(payment_intent, db)
    
    elif event_type == 'payment_intent.payment_failed':
        # Pago fallido
        payment_intent = event['data']['object']
        _handle_payment_failed(payment_intent, db)
    
    elif event_type == 'payment_intent.canceled':
        # Pago cancelado
        payment_intent = event['data']['object']
        _handle_payment_canceled(payment_intent, db)
    
    # Retornar 200 para confirmar recepción
    return {"status": "success"}

@router.get("/config")
def get_stripe_config():
    """
    Obtener configuración pública de Stripe para el frontend
    """
    return {
        "publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        "currency": settings.CURRENCY
    }

# Funciones auxiliares para procesar eventos de webhook

def _handle_payment_succeeded(payment_intent: dict, db: Session):
    """
    Manejar pago exitoso
    
    1. Buscar la orden por payment_intent_id
    2. Actualizar estado a PAID
    3. Guardar fecha de pago
    """
    payment_intent_id = payment_intent['id']
    
    order = db.query(Order).filter(
        Order.payment_id == payment_intent_id
    ).first()
    
    if order:
        order.status = OrderStatus.PAID
        order.paid_at = datetime.now()
        db.commit()
        
        print(f"Orden #{order.id} marcada como PAID")

def _handle_payment_failed(payment_intent: dict, db: Session):
    """
    Manejar pago fallido
   
    """
    payment_intent_id = payment_intent['id']
    error = payment_intent.get('last_payment_error', {})
    
    order = db.query(Order).filter(
        Order.payment_id == payment_intent_id
    ).first()
    
    if order:
        print(f"Pago fallido para orden #{order.id}: {error.get('message', 'Unknown')}")

def _handle_payment_canceled(payment_intent: dict, db: Session):
    """
    Manejar pago cancelado
    
    El payment intent fue cancelado antes de completarse
    """
    payment_intent_id = payment_intent['id']
    
    order = db.query(Order).filter(
        Order.payment_id == payment_intent_id
    ).first()
    
    if order:
        print(f"Payment Intent cancelado para orden #{order.id}")