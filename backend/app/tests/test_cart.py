import pytest

@pytest.fixture
def test_product(client):
    response = client.post("/products/", json={
        "name": "Test Crema Facial",
        "description": "Crema de prueba",
        "price": 5000,
        "stock": 10,
        "category": "facial",
        "image_url": "https://example.com/test.jpg"
    })
    return response.json()

def test_add_to_cart(client, auth_headers, test_product):
    response = client.post(
        "/cart/items",
        headers=auth_headers,
        json={
            "product_id": test_product["id"],
            "quantity": 2
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == test_product["id"]
    assert data["quantity"] == 2
    assert data["product_name"] == test_product["name"]
    assert data["subtotal"] == test_product["price"] * 2

def test_add_to_cart_without_auth(client, test_product):
    response = client.post(
        "/cart/items",
        json={
            "product_id": test_product["id"],
            "quantity": 1
        }
    )

    assert response.status_code == 401

def test_add_nonexistent_product_to_cart(client, auth_headers):
    response = client.post(
        "/cart/items",
        headers=auth_headers,
        json={
            "product_id": 99999,
            "quantity": 1
        }
    )
    
    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"].lower()

def test_add_to_cart_insufficient_stock(client, auth_headers, test_product):
    response = client.post(
        "/cart/items",
        headers=auth_headers,
        json={
            "product_id": test_product["id"],
            "quantity": 100  # Mas que el stock (10)
        }
    )

    assert response.status_code == 400
    assert "stock insuficiente" in response.json()["detail"].lower()

def test_add_existing_product_updates_quantity(client, auth_headers, test_product):
    client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_product["id"], "quantity": 2}
    )
    response = client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_product["id"], "quantity": 3}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 5

def test_get_empty_cart(client, auth_headers):
    response = client.get("/cart/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["subtotal"] == 0
    assert data["tax"] == 0
    assert data["total"] == 0
    assert data["items_count"] == 0

def test_get_cart_with_items(client, auth_headers, test_product):
    client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_product["id"], "quantity": 2}
    )

    response = client.get("/cart/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert data["subtotal"] == test_product["price"] * 2
    assert data["tax"] == round(data["subtotal"] * 0.19, 2)
    assert data["total"] == round(data["subtotal"] + data["tax"], 2)
    assert data["items_count"] == 1

def test_get_cart_without_auth(client):
    response = client.get("/cart/")
    assert response.status_code == 401

def test_update_cart_item_quantity(client, auth_headers, test_product):
    add_response = client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_product["id"], "quantity": 2}
    )
    item_id = add_response.json()["id"]

    response = client.put(
        f"/cart/items/{item_id}",
        headers=auth_headers,
        json={"quantity": 5}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 5
    assert data["subtotal"] == test_product["price"] * 5

def test_update_cart_item_insufficient_stock(client, auth_headers, test_product):
    add_response = client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_product["id"], "quantity": 2}
    )
    item_id = add_response.json()["id"]

    response = client.put(
        f"/cart/items/{item_id}",
        headers=auth_headers,
        json={"quantity": 100}
    )

    assert response.status_code == 400
    assert "stock insuficiente" in response.json()["detail"].lower()

def test_update_nonexistent_cart_item(client, auth_headers):
    response = client.put(
        "/cart/items/99999",
        headers=auth_headers,
        json={"quantity": 5}
    )
    
    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"].lower()

def test_remove_cart_item(client, auth_headers, test_product):
    add_response = client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_product["id"], "quantity": 2}
    )
    item_id = add_response.json()["id"]

    response = client.delete(
        f"/cart/items/{item_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    cart_response = client.get("/cart/", headers=auth_headers)
    assert len(cart_response.json()["items"]) == 0

def test_remove_nonexistent_cart_item(client, auth_headers):
    response = client.delete(
        "/cart/items/99999",
        headers=auth_headers
    )
    
    assert response.status_code == 404

def test_clear_cart(client, auth_headers, test_product):
    client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_product["id"], "quantity": 2}
    )
    
    product2 = client.post("/products/", json={
        "name": "Test Serum",
        "description": "Serum de prueba",
        "price": 8000,
        "stock": 15,
        "category": "facial"
    }).json()
    
    client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": product2["id"], "quantity": 1}
    )
    
    response = client.delete("/cart/", headers=auth_headers)
    
    assert response.status_code == 204

    cart_response = client.get("/cart/", headers=auth_headers)
    assert len(cart_response.json()["items"]) == 0
    assert cart_response.json()["items_count"] == 0

def test_invalid_quantity_zero(client, auth_headers, test_product):
    response = client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_product["id"], "quantity": 0}
    )
    
    assert response.status_code == 422

def test_invalid_quantity_negative(client, auth_headers, test_product):
    response = client.post(
        "/cart/items",
        headers=auth_headers,
        json={"product_id": test_product["id"], "quantity": -1}
    )
    
    assert response.status_code == 422

def test_cart_isolation_between_users(client, test_product):
    client.post("/auth/register", json={
        "email": "user1@test.com",
        "username": "user1",
        "password": "TestPass123!"
    })
    
    client.post("/auth/register", json={
        "email": "user2@test.com",
        "username": "user2",
        "password": "TestPass123!"
    })
    
    token1 = client.post("/auth/login", data={
        "username": "user1",
        "password": "TestPass123!"
    }).json()["access_token"]
    
    token2 = client.post("/auth/login", data={
        "username": "user2",
        "password": "TestPass123!"
    }).json()["access_token"]
    
    client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {token1}"},
        json={"product_id": test_product["id"], "quantity": 2}
    )
    
    cart2 = client.get(
        "/cart/",
        headers={"Authorization": f"Bearer {token2}"}
    ).json()
    
    assert len(cart2["items"]) == 0
    
    cart1 = client.get(
        "/cart/",
        headers={"Authorization": f"Bearer {token1}"}
    ).json()
    
    assert len(cart1["items"]) == 1