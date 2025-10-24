from fastapi import FastAPI
from app.core.database import Base, engine
from app.api import products, auth, cart, order, payments, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Natural Triade API", description="API para tienda e-commerce Natural Triade")

app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(cart.router, prefix="/cart", tags=["Cart"])
app.include_router(order.router, prefix="/orders", tags=["Orders"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

@app.get("/")
def root():
    return {"message": "Natural Triade API", "docs": "/docs", "health": "/health"}

@app.get("/health")
def health():
    return {"status": "healthy"}

