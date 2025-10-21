from fastapi import FastAPI
from app.core.database import Base, engine
from app.api import products, auth, cart

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Natural Triade API", description="API para tienda e-commerce Natural Triade")

app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(cart.router, prefix="/cart", tags=["Cart"])

@app.get("/")
def root():
    return {"message": "Natural Triade API", "docs": "/docs", "health": "/health"}

@app.get("/health")
def health():
    return {"status": "healthy"}

