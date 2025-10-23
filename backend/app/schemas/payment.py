from pydantic import BaseModel
from typing import Optional

class PaymentIntentCreate(BaseModel):
    """Request para crear un Payment Intent de Stripe"""
    order_id: int

class PaymentIntentResponse(BaseModel):
    """Response con el client_secret para el frontend"""
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str
    order_id: int

class PaymentConfirmation(BaseModel):
    """Confirmación de pago exitoso"""
    order_id: int
    payment_intent_id: str
    status: str
    amount_paid: int

class StripeWebhookEvent(BaseModel):
    """Evento de webhook de Stripe"""
    type: str
    data: dict