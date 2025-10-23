import stripe
from app.core.config import settings
from app.models.order import Order
from typing import Optional

# Configurar Stripe con la API key
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    """Servicio para interactuar con Stripe API"""
    @staticmethod
    def create_payment_intent(order: Order) -> stripe.PaymentIntent:
        """
        Crear un Payment Intent en Stripe para una orden
        
        Args:
            order: Orden para la cual crear el pago
            
        Returns:
            PaymentIntent de Stripe
        """
        
        # Convertir el total a centavos (Stripe trabaja en centavos)
        # CLP no tiene decimales, así que multiplicamos por 1
        amount = int(order.total)

        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=settings.CURRENCY,
                metadata={
                    'order_id': order.id,
                    'user_id': order.user_id,
                },
                # Configuración adicional
                automatic_payment_methods={
                    'enabled': True,
                },
                description=f"Orden #{order.id} - Natural Triade"
            )
            
            return payment_intent
            
        except stripe.error.StripeError as e:
            # Propagar el error para manejarlo en el endpoint
            raise Exception(f"Error de Stripe: {str(e)}")
        
    @staticmethod
    def retrieve_payment_intent(payment_intent_id: str) -> Optional[stripe.PaymentIntent]:
        """
        Obtener información de un Payment Intent
        
        Args:
            payment_intent_id: ID del Payment Intent
            
        Returns:
            PaymentIntent o None si no existe
        """
        try:
            return stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError:
            return None
        
    @staticmethod
    def cancel_payment_intent(payment_intent_id: str) -> Optional[stripe.PaymentIntent]:
        """
        Cancelar un Payment Intent
        
        Args:
            payment_intent_id: ID del Payment Intent a cancelar
            
        Returns:
            PaymentIntent cancelado o None si falló
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status in ['requires_payment_method', 'requires_confirmation']:
                return stripe.PaymentIntent.cancel(payment_intent_id)
            
            return None
            
        except stripe.error.StripeError:
            return None
        
    @staticmethod
    def construct_webhook_event(payload: bytes, sig_header: str):
        """
        Construir y verificar un evento de webhook
        
        Args:
            payload: Cuerpo de la petición (raw bytes)
            sig_header: Header de firma de Stripe
            
        Returns:
            Evento verificado
            
        Raises:
            ValueError: Si la firma es inválida
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
            
        except ValueError as e:
            # Payload inválido
            raise ValueError(f"Payload inválido: {str(e)}")
            
        except stripe.error.SignatureVerificationError as e:
            # Firma inválida
            raise ValueError(f"Firma de webhook inválida: {str(e)}")
        
    @staticmethod
    def create_refund(payment_intent_id: str, amount: Optional[int] = None) -> stripe.Refund:
        """
        Crear un reembolso para un pago
        
        Args:
            payment_intent_id: ID del Payment Intent
            amount: Cantidad a reembolsar (None = total)
            
        Returns:
            Refund de Stripe
        """
        try:
            refund_params = {'payment_intent': payment_intent_id}
            
            if amount:
                refund_params['amount'] = amount
            
            return stripe.Refund.create(**refund_params)
            
        except stripe.error.StripeError as e:
            raise Exception(f"Error al crear reembolso: {str(e)}")