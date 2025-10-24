import pytest


@pytest.fixture
def test_products(client):
    products = []
    
    product1 = client.post("/products/", json={
        "name": "Crema Facial",
        "description": "Crema hidratante",
        "price": 5000,
        "stock": 10,
        "category": "facial"
    }).json()
    products.append(product1)
    
    product2 = client.post("/products/", json={
        "name": "Serum",
        "description": "Serum vitamina C",
        "price": 8000,
        "stock": 5,
        "category": "facial"
    }).json()
    products.append(product2)
    
    return products

@pytest.fixture
def cart_with_items(client, auth_headers, test_products):
    client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_products[0]["id"], "quantity": 2}
    )
    
    client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_products[1]["id"], "quantity": 1}
    )
    
    return True

def update_order_status(order_id, new_status, engine):
    """Helper para actualizar estado de orden en tests"""
    from sqlalchemy.orm import Session
    from app.models.order import Order
    from datetime import datetime
    
    with Session(engine) as db:
        order = db.query(Order).filter(Order.id == order_id).first()
        assert order is not None, f"Order {order_id} not found"
        order.status = new_status
        
        # Set timestamp según el estado
        if new_status.value == "shipped":
            order.shipped_at = datetime.now()
        elif new_status.value == "delivered":
            order.delivered_at = datetime.now()
        elif new_status.value == "cancelled":
            order.cancelled_at = datetime.now()
        elif new_status.value == "paid":
            order.paid_at = datetime.now()
        
        db.commit()

def test_create_order_from_cart(client, auth_headers, cart_with_items):
    response = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Av. Libertador 123",
            "shipping_city": "Santiago",
            "shipping_postal_code": "8320000",
            "contact_email": "test@example.com",
            "contact_phone": "+56912345678",
            "payment_method": "pending"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert "id" in data
    assert data["status"] == "pending"
    assert data["user_id"] is not None
    assert data["subtotal"] > 0
    assert data["tax"] > 0
    assert data["total"] > 0
    assert data["shipping_address"] == "Av. Libertador 123"
    assert data["shipping_city"] == "Santiago"
    assert len(data["items"]) == 2
    
    for item in data["items"]:
        assert "product_name" in item
        assert "unit_price" in item
        assert "quantity" in item
        assert "subtotal" in item

def test_create_order_without_auth(client, cart_with_items):
    response = client.post(
        "/orders/",
        json={
            "shipping_address": "Av. Libertador 123",
            "shipping_city": "Santiago",
            "contact_email": "test@example.com"
        }
    )
    
    assert response.status_code == 401

def test_create_order_reduces_stock(client, auth_headers, test_products):
    initial_stock = test_products[0]["stock"]

    client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_products[0]["id"], "quantity": 3}
    )

    client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Av. Libertador 123",
            "shipping_city": "Santiago",
            "contact_email": "test@example.com"
        }
    )
 
    product_response = client.get(f"/products/{test_products[0]['id']}")
    updated_stock = product_response.json()["stock"]
    
    assert updated_stock == initial_stock - 3

def test_create_order_clears_cart(client, auth_headers, cart_with_items):

    cart_before = client.get("/cart/", headers=auth_headers).json()
    assert len(cart_before["items"]) > 0
    
    client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Av. Libertador 123",
            "shipping_city": "Santiago",
            "contact_email": "test@example.com"
        }
    )
 
    cart_after = client.get("/cart/", headers=auth_headers).json()
    assert len(cart_after["items"]) == 0

def test_create_order_insufficient_stock(client, auth_headers, test_products):

    client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_products[1]["id"], "quantity": 3} 
    )
    
    product = test_products[1]
    client.put(f"/products/{product['id']}", json={"stock": 2})
    
    response = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Av. Libertador 123",
            "shipping_city": "Santiago",
            "contact_email": "test@example.com"
        }
    )

    assert response.status_code == 400
    assert "stock insuficiente" in response.json()["detail"].lower()

def test_get_my_orders_empty(client, auth_headers):

    response = client.get("/orders/", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json() == []

def test_get_my_orders(client, auth_headers, cart_with_items):

    client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Address 1",
            "shipping_city": "Santiago",
            "contact_email": "test@example.com"
        }
    )
    
    product = client.post("/products/", json={
        "name": "Test Product",
        "description": "Test",
        "price": 3000,
        "stock": 10,
        "category": "facial"
    }).json()
    
    client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": product["id"], "quantity": 1}
    )
    
    client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Address 2",
            "shipping_city": "Valparaíso",
            "contact_email": "test@example.com"
        }
    )
    
    response = client.get("/orders/", headers=auth_headers)
    
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) == 2

    for order in orders:
        assert "id" in order
        assert "status" in order
        assert "total" in order
        assert "items_count" in order
        assert "created_at" in order

    assert orders[0]["id"] > orders[1]["id"]

def test_get_my_orders_without_auth(client):

    response = client.get("/orders/")
    assert response.status_code == 401

def test_get_order_detail(client, auth_headers, cart_with_items):
 
    create_response = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Av. Libertador 123",
            "shipping_city": "Santiago",
            "shipping_postal_code": "8320000",
            "contact_email": "test@example.com",
            "contact_phone": "+56912345678"
        }
    )
    
    order_id = create_response.json()["id"]

    response = client.get(f"/orders/{order_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == order_id
    assert data["status"] == "pending"
    assert data["shipping_address"] == "Av. Libertador 123"
    assert data["shipping_city"] == "Santiago"
    assert data["shipping_postal_code"] == "8320000"
    assert data["contact_email"] == "test@example.com"
    assert data["contact_phone"] == "+56912345678"
    assert len(data["items"]) > 0

    for item in data["items"]:
        assert "product_name" in item
        assert "product_description" in item
        assert "unit_price" in item
        assert "quantity" in item
        assert "subtotal" in item

def test_get_nonexistent_order(client, auth_headers):
    response = client.get("/orders/99999", headers=auth_headers)
    
    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"].lower()

def test_get_other_user_order(client, test_products):

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
    
    order_response = client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "shipping_address": "Address 1",
            "shipping_city": "Santiago",
            "contact_email": "user1@test.com"
        }
    )
    order_id = order_response.json()["id"]

    client.post("/auth/register", json={
        "email": "user2@test.com",
        "username": "user2",
        "password": "TestPass123!"
    })
    
    token2 = client.post("/auth/login", data={
        "username": "user2",
        "password": "TestPass123!"
    }).json()["access_token"]

    response = client.get(
        f"/orders/{order_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    assert response.status_code == 404

def test_cancel_pending_order(client, auth_headers, cart_with_items):

    create_response = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Av. Libertador 123",
            "shipping_city": "Santiago",
            "contact_email": "test@example.com"
        }
    )
    
    order_id = create_response.json()["id"]

    response = client.put(f"/orders/{order_id}/cancel", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    assert data["cancelled_at"] is not None

def test_cancel_order_restores_stock(client, auth_headers, test_products):

    initial_stock = test_products[0]["stock"]

    client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_products[0]["id"], "quantity": 3}
    )
    
    order_response = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Av. Libertador 123",
            "shipping_city": "Santiago",
            "contact_email": "test@example.com"
        }
    )
    
    order_id = order_response.json()["id"]

    product_after_order = client.get(f"/products/{test_products[0]['id']}").json()
    assert product_after_order["stock"] == initial_stock - 3

    client.put(f"/orders/{order_id}/cancel", headers=auth_headers)

    product_after_cancel = client.get(f"/products/{test_products[0]['id']}").json()
    assert product_after_cancel["stock"] == initial_stock

def test_cancel_nonexistent_order(client, auth_headers):

    response = client.put("/orders/99999/cancel", headers=auth_headers)
    
    assert response.status_code == 404

def test_cancel_other_user_order(client, test_products):

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
    
    order_response = client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "shipping_address": "Address 1",
            "shipping_city": "Santiago",
            "contact_email": "user1@test.com"
        }
    )
    order_id = order_response.json()["id"]

    client.post("/auth/register", json={
        "email": "user2@test.com",
        "username": "user2",
        "password": "TestPass123!"
    })
    
    token2 = client.post("/auth/login", data={
        "username": "user2",
        "password": "TestPass123!"
    }).json()["access_token"]
 
    response = client.put(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    assert response.status_code == 404

def test_cannot_cancel_shipped_order(client, auth_headers):
    """Test that shipped orders cannot be cancelled"""
    from app.tests.conftest import engine
    from app.models.order import OrderStatus
    
    # Create product and order
    product = client.post("/products/", json={
        "name": "Test Product",
        "description": "Test",
        "price": 5000,
        "stock": 10,
        "category": "facial"
    }).json()
    
    client.post("/cart/items", headers=auth_headers, 
                json={"product_id": product["id"], "quantity": 2})
    
    order = client.post("/orders/", headers=auth_headers, json={
        "shipping_address": "Av. Libertador 123",
        "shipping_city": "Santiago",
        "contact_email": "test@example.com"
    }).json()
    
    # Update to shipped status
    update_order_status(order["id"], OrderStatus.SHIPPED, engine)
    
    # Try to cancel (should fail)
    response = client.put(f"/orders/{order['id']}/cancel", headers=auth_headers)
    
    assert response.status_code == 400
    assert "no se puede cancelar" in response.json()["detail"].lower()
    
def test_order_calculates_tax_correctly(client, auth_headers, test_products):

    client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_products[0]["id"], "quantity": 2}
    )

    response = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Av. Libertador 123",
            "shipping_city": "Santiago",
            "contact_email": "test@example.com"
        }
    )
    
    data = response.json()

    expected_tax = round(data["subtotal"] * 0.19, 2)
    assert data["tax"] == expected_tax
    assert data["total"] == data["subtotal"] + data["tax"]

def test_order_validation_required_fields(client, auth_headers, cart_with_items):

    response = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_city": "Santiago",
            "contact_email": "test@example.com"
        }
    )
    assert response.status_code == 422

    response = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Av. Libertador 123",
            "contact_email": "test@example.com"
        }
    )
    assert response.status_code == 422

    response = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Av. Libertador 123",
            "shipping_city": "Santiago"
        }
    )
    assert response.status_code == 422

def test_order_invalid_email(client, auth_headers, cart_with_items):
    """Test order creation with invalid email"""
    response = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "shipping_address": "Av. Libertador 123",
            "shipping_city": "Santiago",
            "contact_email": "invalid-email"
        }
    )
    
    assert response.status_code == 422

