def test_get_products_empty(client):
    response = client.get("/products/")
    assert response.status_code == 200
    assert response.json() == []

def test_create_product(client):
    response = client.post("/products/", json={
        "name": "Test Product Facial",
        "description": "Test Description",
        "price": 7000,
        "stock": 5,
        "category": "facial",
        "image_url": "https://example.com/image.jpg"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Product Facial"
    assert data["price"] == 7000
    assert data["category"] == "facial"
    assert data["image_url"] == "https://example.com/image.jpg"
    assert "id" in data

def test_get_product(client):
    create_response = client.post("/products/", json={
        "name": "Test Product Cabello",
        "description": "Test Description",
        "price": 7000,
        "stock": 5,
        "category": "cabello"
    })
    product_id = create_response.json()["id"]

    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Product Cabello"

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

def test_search_products(client):
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

    response = client.get("/products/?search=Facial")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert "Facial" in results[0]["name"]

def test_filter_by_price_range(client):
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

    response = client.get("/products/?min_price=2000&max_price=4000")
    assert response.status_code == 200
    assert len(response.json()) == 0

    response = client.get("/products/?max_price=20000")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_update_product(client):
    create_response = client.post("/products", json={
        "name": "Test Product Facial",
        "description": "Test Description",
        "price": 7000,
        "stock": 5,
        "category": "facial"
    })

    product_id = create_response.json()["id"]

    update_response = client.put(f"/products/{product_id}", json={
        "name": "Test Product Updated",
        "price": 10000
    })

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Test Product Updated"
    assert data["price"] == 10000
    assert data["description"] == "Test Description"

def test_delete_product(client): 
    create_response = client.post("/products", json={
        "name": "Test Product Facial",
        "description": "Test Description",
        "price": 7000,
        "stock": 5,
        "category": "facial"
    })
    product_id = create_response.json()["id"]

    delete_response = client.delete(f"/products/{product_id}")
    assert delete_response.status_code == 204

    list_response = client.get("/products/")
    assert all(p["id"] != product_id for p in list_response.json())

def test_get_nonexistent_product(client):
    response = client.get("/products/5000")
    assert response.status_code == 404

def test_update_nonexistent_product(client):
    response = client.put("/products/10000", json={"name": "Test"})
    assert response.status_code == 404

def test_invalid_category(client):
    response = client.post("/products", json={
        "name": "Test Product Facial",
        "description": "Test Description",
        "price": 7000,
        "stock": 5,
        "category": "invalida"
    })

    assert response.status_code == 422
