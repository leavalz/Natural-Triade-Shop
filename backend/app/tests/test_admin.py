import pytest


@pytest.fixture(scope="function")
def admin_user(client):
    """Create an admin user"""
    from app.tests.conftest import TestingSessionLocal
    from app.models.user import User, UserRole
    
    # Registrar admin usando el endpoint de registro
    response = client.post("/auth/register", json={
        "email": "admin@test.com",
        "username": "admintest",
        "full_name": "Admin User",
        "password": "AdminPass123!"
    })
    
    # Verificar que se creó correctamente
    assert response.status_code == 201
    user_data = response.json()
    
    # Actualizar el rol a ADMIN directamente en la base de datos de prueba
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin@test.com").first()
        if user:
            user.role = UserRole.ADMIN
            db.commit()
            db.refresh(user)
    finally:
        db.close()
    
    return user_data


@pytest.fixture
def admin_token(client, admin_user):
    """Get admin token"""
    response = client.post("/auth/login", data={
        "username": "admintest",
        "password": "AdminPass123!"
    })
    
    # Verificar que el login fue exitoso
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    
    return data["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    """Get admin headers"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def test_orders_data(client, test_user, auth_headers, test_products):
    """Create some test orders"""
    orders = []
    
    for i in range(3):
        # Add to cart
        client.post(
            "/cart/items",
            headers=auth_headers,
            json={"product_id": test_products[0]["id"], "quantity": 1}
        )
        
        # Create order
        response = client.post(
            "/orders/",
            headers=auth_headers,
            json={
                "shipping_address": f"Address {i}",
                "shipping_city": "Santiago",
                "contact_email": "test@example.com"
            }
        )
        orders.append(response.json())
    
    return orders


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
    
    product2 = client.post("/products/", json={
        "name": "Test Product Low Stock",
        "description": "Description 2",
        "price": 3000,
        "stock": 2,
        "category": "corporal"
    }).json()
    products.append(product2)
    
    return products


def test_admin_access_dashboard(client, admin_headers):
    """Test that admin can access dashboard"""
    response = client.get("/admin/dashboard", headers=admin_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "metrics" in data
    assert "top_products" in data
    assert "recent_orders" in data
    assert "low_stock_products" in data
    
    metrics = data["metrics"]
    assert "total_revenue" in metrics
    assert "total_orders" in metrics
    assert "pending_orders" in metrics


def test_non_admin_cannot_access_dashboard(client, auth_headers):
    """Test that regular users cannot access admin dashboard"""
    response = client.get("/admin/dashboard", headers=auth_headers)
    
    assert response.status_code == 403
    assert "no tienes permisos" in response.json()["detail"].lower()


def test_unauthenticated_cannot_access_dashboard(client):
    """Test that unauthenticated users cannot access admin"""
    response = client.get("/admin/dashboard")
    
    assert response.status_code == 401


def test_admin_get_all_orders(client, admin_headers, test_orders_data):
    """Test admin can see all orders"""
    response = client.get("/admin/orders", headers=admin_headers)
    
    assert response.status_code == 200
    orders = response.json()
    
    assert len(orders) >= len(test_orders_data)
    
    for order in orders:
        assert "id" in order
        assert "user_id" in order
        assert "status" in order
        assert "total" in order


def test_admin_filter_orders_by_status(client, admin_headers, test_orders_data):
    """Test admin can filter orders by status"""
    response = client.get("/admin/orders?status=pending", headers=admin_headers)
    
    assert response.status_code == 200
    orders = response.json()
    
    for order in orders:
        assert order["status"] == "pending"


def test_admin_update_order_status(client, admin_headers, test_orders_data):
    """Test admin can update order status"""
    order_id = test_orders_data[0]["id"]
    
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "processing"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"


def test_admin_update_order_to_shipped(client, admin_headers, test_orders_data):
    """Test admin can mark order as shipped"""
    order_id = test_orders_data[0]["id"]
    
    # First mark as paid
    client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "paid"}
    )
    
    # Then mark as shipped
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "shipped"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "shipped"
    assert data["shipped_at"] is not None


def test_admin_cannot_change_cancelled_order(client, admin_headers, test_orders_data):
    """Test admin cannot change status of cancelled order"""
    order_id = test_orders_data[0]["id"]
    
    # Cancel order
    client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "cancelled"}
    )
    
    # Try to change status
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "paid"}
    )
    
    assert response.status_code == 400
    assert "cancelada" in response.json()["detail"].lower()


def test_admin_cancel_order_restores_stock(client, admin_headers, test_products):
    """Test that cancelling an order restores stock"""
    initial_stock = test_products[0]["stock"]
    
    # Create regular user and order
    client.post("/auth/register", json={
        "email": "user@test.com",
        "username": "user",
        "password": "UserPass123!"
    })
    
    user_token = client.post("/auth/login", data={
        "username": "user",
        "password": "UserPass123!"
    }).json()["access_token"]
    
    # Add to cart and create order
    client.post(
        "/cart/items",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"product_id": test_products[0]["id"], "quantity": 3}
    )
    
    order = client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "shipping_address": "Address",
            "shipping_city": "Santiago",
            "contact_email": "user@test.com"
        }
    ).json()
    
    # Check stock was reduced
    product = client.get(f"/products/{test_products[0]['id']}").json()
    assert product["stock"] == initial_stock - 3
    
    # Admin cancels order
    client.put(
        f"/admin/orders/{order['id']}/status",
        headers=admin_headers,
        json={"status": "cancelled"}
    )
    
    # Check stock was restored
    product = client.get(f"/products/{test_products[0]['id']}").json()
    assert product["stock"] == initial_stock


def test_regular_user_cannot_update_order_status(client, auth_headers, test_orders_data):
    """Test regular users cannot update order status"""
    order_id = test_orders_data[0]["id"]
    
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=auth_headers,
        json={"status": "shipped"}
    )
    
    assert response.status_code == 403


def test_admin_get_all_products(client, admin_headers, test_products):
    """Test admin can see all products"""
    response = client.get("/admin/products", headers=admin_headers)
    
    assert response.status_code == 200
    products = response.json()
    assert len(products) >= len(test_products)


def test_admin_get_all_products_including_inactive(client, admin_headers, test_products):
    """Test admin can see inactive products"""
    # Mark a product as inactive
    client.delete(f"/products/{test_products[0]['id']}")
    
    # Get all products including inactive
    response = client.get("/admin/products?include_inactive=true", headers=admin_headers)
    
    assert response.status_code == 200
    products = response.json()
    
    # Should include both active and inactive
    active_count = sum(1 for p in products if p["is_active"])
    inactive_count = sum(1 for p in products if not p["is_active"])
    
    assert inactive_count > 0


def test_admin_get_low_stock_products(client, admin_headers, test_products):
    """Test admin can see products with low stock"""
    response = client.get("/admin/products/low-stock?threshold=5", headers=admin_headers)
    
    assert response.status_code == 200
    products = response.json()
    
    # Should only return products with stock < 5
    for product in products:
        assert product["stock"] < 5


def test_admin_get_all_users(client, admin_headers):
    """Test admin can see all users"""
    response = client.get("/admin/users", headers=admin_headers)
    
    assert response.status_code == 200
    users = response.json()
    
    assert len(users) > 0
    
    for user in users:
        assert "id" in user
        assert "email" in user
        assert "username" in user
        assert "role" in user
        assert "hashed_password" not in user  # Should not expose password


def test_admin_get_revenue_analytics(client, admin_headers, test_orders_data):
    """Test admin can get revenue analytics"""
    response = client.get("/admin/analytics/revenue?days=30", headers=admin_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    
    # If there are orders, should have analytics data
    if len(data) > 0:
        for day_data in data:
            assert "date" in day_data
            assert "revenue" in day_data
            assert "orders_count" in day_data


def test_dashboard_shows_low_stock_products(client, admin_headers, test_products):
    """Test dashboard shows products with low stock"""
    response = client.get("/admin/dashboard", headers=admin_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    low_stock = data["low_stock_products"]
    
    # Should show the product with stock = 2
    assert any(p["stock"] < 5 for p in low_stock)


def test_dashboard_metrics_with_orders(client, admin_headers, test_orders_data):
    """Test dashboard metrics reflect actual orders"""
    response = client.get("/admin/dashboard", headers=admin_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    metrics = data["metrics"]
    
    # Should have orders
    assert metrics["total_orders"] >= len(test_orders_data)
    assert metrics["pending_orders"] >= len(test_orders_data)


def test_admin_invalid_order_status(client, admin_headers, test_orders_data):
    """Test admin cannot set invalid order status"""
    order_id = test_orders_data[0]["id"]
    
    response = client.put(
        f"/admin/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "invalid_status"}
    )
    
    assert response.status_code == 400
    assert "inválido" in response.json()["detail"].lower()


def test_admin_pagination_orders(client, admin_headers, test_orders_data):
    """Test admin can paginate orders"""
    # Get first page
    response1 = client.get("/admin/orders?skip=0&limit=2", headers=admin_headers)
    assert response1.status_code == 200
    page1 = response1.json()
    
    # Get second page
    response2 = client.get("/admin/orders?skip=2&limit=2", headers=admin_headers)
    assert response2.status_code == 200
    page2 = response2.json()
    
    # Pages should be different (if we have enough orders)
    if len(page1) > 0 and len(page2) > 0:
        assert page1[0]["id"] != page2[0]["id"]


def test_admin_filter_orders_by_user(client, admin_headers, test_user, test_orders_data):
    """Test admin can filter orders by user"""
    user_id = test_user["id"]
    
    response = client.get(f"/admin/orders?user_id={user_id}", headers=admin_headers)
    
    assert response.status_code == 200
    orders = response.json()
    
    # All orders should belong to the specified user
    for order in orders:
        assert order["user_id"] == user_id