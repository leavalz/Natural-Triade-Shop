def test_get_products_empty(client):
    response = client.get("/products/")
    assert response.status_code == 200
    assert response.json() == []

def test_create_product(client):
    response = client.post("/products/", json={
        "name": "Test Product",
        "description": "Test Description",
        "price": 7000,
        "stock": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["price"] == 7000
    assert "id" in data

def test_get_product(client):
    create_response = client.post("/products/", json={
        "name": "Test Product",
        "description": "Test Description",
        "price": 7000,
        "stock": 5
    })
    product_id = create_response.json()["id"]

    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Product"

def test_get_nonexistent_product(client):
    response = client.get("/products/5000")
    assert response.status_code == 404

def test_filter_by_category(client):
    client.post("/products/", json={
        "name": "Test Product Facial",
        "description": "Test Description",
        "price": 7000,
        "stock": 5,
        "category": "facial"
    })
    client.post("/products/", json={
        "name": "Test Product Cabello",
        "description": "Test Description",
        "price": 10000,
        "stock": 10,
        "category": "cabello"
    })

    response = client.get("/products/?category=facial")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["category"] == "facial"