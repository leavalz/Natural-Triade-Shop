from fastapi import FastAPI
from app.core.database import Base, engine
from app.api import products

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Natural Triade API")

app.include_router(products.router, prefix="/products", tags=["Products"])

@app.get("/")
def root():
    return {"message": "Natural Triade API", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}