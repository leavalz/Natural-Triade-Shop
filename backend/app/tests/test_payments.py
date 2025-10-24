import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def test_order(client, auth_headers, test_products):
    """Create a test order"""
    # Add products to cart
    client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_products[0]["id"], "quantity": 2}
    )
    
    # Create order
    response = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Av. Libertador 123",
            "shipping_city": "Santiago",
            "contact_email": "test@example.com"
        }
    )
    
    return response.json()


@pytest.fixture
def test_products(client):
    """Create test products"""
    products = []
    
    product1 = client.post("/products/", json={
        "name": "Test Product 1",
        "description": "Description 1",
        "price": 5000,
        "stock": 10,
        "category": "facial"
    }).json()
    products.append(product1)
    
    return products

def update_order_in_test_db(order_id, updates, engine):
    """Helper para actualizar orden en la base de datos de test"""
    from sqlalchemy.orm import Session
    from app.models.order import Order
    
    with Session(engine) as db:
        order = db.query(Order).filter(Order.id == order_id).first()
        assert order is not None, f"Order {order_id} not found in test database"
        
        for key, value in updates.items():
            setattr(order, key, value)
        
        db.commit()

def test_get_stripe_config(client):
    """Test getting Stripe public configuration"""
    response = client.get("/payments/config")
    
    assert response.status_code == 200
    data = response.json()
    assert "publishable_key" in data
    assert "currency" in data
    assert data["currency"] == "clp"


@patch('app.services.stripe_service.stripe.PaymentIntent.create')
def test_create_payment_intent(mock_create, client, auth_headers, test_order):
    """Test creating a payment intent for an order"""
    # Mock Stripe response
    mock_payment_intent = MagicMock()
    mock_payment_intent.id = "pi_test_123"
    mock_payment_intent.client_secret = "pi_test_123_secret_abc"
    mock_payment_intent.amount = int(test_order["total"])
    mock_payment_intent.currency = "clp"
    mock_create.return_value = mock_payment_intent
    
    # Create payment intent
    response = client.post(
        "/payments/create-payment-intent",
        headers=auth_headers,
        json={"order_id": test_order["id"]}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "client_secret" in data
    assert "payment_intent_id" in data
    assert data["order_id"] == test_order["id"]
    assert data["amount"] == int(test_order["total"])
    assert data["currency"] == "clp"
    
    # Verify Stripe was called
    mock_create.assert_called_once()


def test_create_payment_intent_nonexistent_order(client, auth_headers):
    """Test creating payment intent for non-existent order"""
    response = client.post(
        "/payments/create-payment-intent",
        headers=auth_headers,
        json={"order_id": 99999}
    )
    
    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"].lower()


def test_create_payment_intent_without_auth(client, test_order):
    """Test creating payment intent without authentication"""
    response = client.post(
        "/payments/create-payment-intent",
        json={"order_id": test_order["id"]}
    )
    
    assert response.status_code == 401


@patch('app.services.stripe_service.stripe.PaymentIntent.create')
def test_create_payment_intent_for_paid_order(mock_create, client, auth_headers, test_order):
    """Test that you cannot create payment intent for already paid order"""
    from app.tests.conftest import engine
    from app.models.order import OrderStatus
    
    # Mark order as paid using test database
    update_order_in_test_db(test_order["id"], {"status": OrderStatus.PAID}, engine)
    
    # Try to create payment intent
    response = client.post(
        "/payments/create-payment-intent",
        headers=auth_headers,
        json={"order_id": test_order["id"]}
    )
    
    assert response.status_code == 400
    assert "no se puede pagar" in response.json()["detail"].lower()
    
    # Verify Stripe was NOT called
    mock_create.assert_not_called()


@patch('app.services.stripe_service.stripe.PaymentIntent.retrieve')
@patch('app.services.stripe_service.stripe.PaymentIntent.create')
def test_reuse_existing_payment_intent(mock_create, mock_retrieve, client, auth_headers, test_order):
    """Test reusing existing payment intent if still valid"""
    # Mock existing payment intent
    mock_existing_pi = MagicMock()
    mock_existing_pi.id = "pi_existing_123"
    mock_existing_pi.client_secret = "pi_existing_secret"
    mock_existing_pi.amount = int(test_order["total"])
    mock_existing_pi.currency = "clp"
    mock_existing_pi.status = "requires_payment_method"
    mock_retrieve.return_value = mock_existing_pi
    
    # First call - create payment intent
    mock_create.return_value = mock_existing_pi
    response1 = client.post(
        "/payments/create-payment-intent",
        headers=auth_headers,
        json={"order_id": test_order["id"]}
    )
    
    assert response1.status_code == 200
    payment_intent_id = response1.json()["payment_intent_id"]
    
    # Second call - should reuse existing
    response2 = client.post(
        "/payments/create-payment-intent",
        headers=auth_headers,
        json={"order_id": test_order["id"]}
    )
    
    assert response2.status_code == 200
    assert response2.json()["payment_intent_id"] == payment_intent_id
    
    # Verify create was called only once
    assert mock_create.call_count == 1


@patch('app.services.stripe_service.stripe.Webhook.construct_event')
def test_webhook_payment_succeeded(mock_construct, client, test_order):
    """Test webhook handling for successful payment"""
    from app.tests.conftest import engine
    
    # Mock webhook event
    mock_event = {
        'type': 'payment_intent.succeeded',
        'data': {
            'object': {
                'id': 'pi_test_123',
                'amount': int(test_order["total"]),
                'currency': 'clp'
            }
        }
    }
    mock_construct.return_value = mock_event
    
    # Update order with payment_id using test database
    update_order_in_test_db(test_order["id"], {"payment_id": "pi_test_123"}, engine)
    
    # Send webhook
    response = client.post(
        "/payments/webhook",
        headers={"stripe-signature": "test_signature"},
        content=b'{"type":"payment_intent.succeeded"}'
    )
    
    assert response.status_code == 200
    
    # Verify order was marked as paid
    from sqlalchemy.orm import Session
    from app.models.order import Order
    
    with Session(engine) as db:
        order = db.query(Order).filter(Order.id == test_order["id"]).first()
        assert order.status.value == "paid"
        assert order.paid_at is not None


def test_webhook_missing_signature(client):
    """Test webhook without signature header"""
    response = client.post(
        "/payments/webhook",
        content=b'{"type":"payment_intent.succeeded"}'
    )
    
    assert response.status_code == 400


@patch('app.services.stripe_service.stripe.Webhook.construct_event')
def test_webhook_payment_failed(mock_construct, client, test_order):
    """Test webhook handling for failed payment"""
    from app.tests.conftest import engine
    
    # Mock webhook event
    mock_event = {
        'type': 'payment_intent.payment_failed',
        'data': {
            'object': {
                'id': 'pi_test_123',
                'last_payment_error': {
                    'message': 'Card declined'
                }
            }
        }
    }
    mock_construct.return_value = mock_event
    
    # Update order with payment_id using test database
    update_order_in_test_db(test_order["id"], {"payment_id": "pi_test_123"}, engine)
    
    # Send webhook
    response = client.post(
        "/payments/webhook",
        headers={"stripe-signature": "test_signature"},
        content=b'{"type":"payment_intent.payment_failed"}'
    )
    
    assert response.status_code == 200
    
    # Verify order is still pending
    from sqlalchemy.orm import Session
    from app.models.order import Order
    
    with Session(engine) as db:
        order = db.query(Order).filter(Order.id == test_order["id"]).first()
        assert order.status.value == "pending"


def test_create_payment_intent_other_user_order(client, test_products):
    """Test that users cannot create payment intent for other users' orders"""
    # Create user 1 and order
    client.post("/auth/register", json={
        "email": "user1@test.com",
        "username": "user1",
        "password": "TestPass123!"
    })
    
    token1 = client.post("/auth/login", data={
        "username": "user1",
        "password": "TestPass123!"
    }).json()["access_token"]
    
    client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {token1}"},
        json={"product_id": test_products[0]["id"], "quantity": 1}
    )
    
    order = client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "shipping_address": "Address 1",
            "shipping_city": "Santiago",
            "contact_email": "user1@test.com"
        }
    ).json()
    
    # Create user 2
    client.post("/auth/register", json={
        "email": "user2@test.com",
        "username": "user2",
        "password": "TestPass123!"
    })
    
    token2 = client.post("/auth/login", data={
        "username": "user2",
        "password": "TestPass123!"
    }).json()["access_token"]
    
    # User 2 tries to pay user 1's order
    response = client.post(
        "/payments/create-payment-intent",
        headers={"Authorization": f"Bearer {token2}"},
        json={"order_id": order["id"]}
    )
    
    assert response.status_code == 404