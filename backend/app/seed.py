from app.core.database import SessionLocal, engine, Base
from app.models.product import Product, ProductCategory
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def clear_data():
    db = SessionLocal()
    db.query(Product).delete()
    db.query(User).delete()
    db.commit()
    db.close()
    print("Datos eliminados de la base de datos")


def seed_admin_user():
    """Crear usuario administrador"""
    db = SessionLocal()
    
    admin = User(
        email="admin@naturaltriade.com",
        username="admin",
        full_name="Administrador",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    
    db.add(admin)
    db.commit()
    print("✅ Usuario admin creado:")
    print("   Email: admin@naturaltriade.com")
    print("   Username: admin")
    print("   Password: Admin123!")
    db.close()


def seed_products():
    db = SessionLocal()
  
    products_data = [
        {
            "name": "Crema Hidratante de Rosa",
            "description": "Crema facial con extracto de rosa orgánica. Hidratación profunda para todo tipo de piel.",
            "price": 3500,
            "stock": 50,
            "category": ProductCategory.FACIAL,
            "image_url": "https://example.com/image.jpg",
            "is_active": True
        },
        {
            "name": "Serum Vitamina C",
            "description": "Serum antioxidante con vitamina C pura. Ilumina y unifica el tono de piel.",
            "price": 4500,
            "stock": 30,
            "category": ProductCategory.FACIAL,
            "image_url": "https://example.com/image.jpg",
            "is_active": True
        },
        {
            "name": "Limpiador Facial Suave",
            "description": "Gel limpiador con aloe vera. Elimina impurezas sin resecar.",
            "price": 2500,
            "stock": 75,
            "category": ProductCategory.FACIAL,
            "image_url": "https://example.com/image.jpg",
            "is_active": True
        },
        {
            "name": "Aceite Corporal de Coco",
            "description": "Aceite nutritivo con coco orgánico. Piel suave y radiante.",
            "price": 2990,
            "stock": 40,
            "category": ProductCategory.CORPORAL,
            "image_url": "https://example.com/image.jpg",
            "is_active": True
        },
        {
            "name": "Exfoliante de Café",
            "description": "Scrub corporal con granos de café. Renueva y suaviza la piel.",
            "price": 2200,
            "stock": 60,
            "category": ProductCategory.CORPORAL,
            "image_url": "https://example.com/image.jpg",
            "is_active": True
        },
        {
            "name": "Champú de Argán",
            "description": "Champú reparador con aceite de argán. Cabello suave y brillante.",
            "price": 10000,
            "stock": 2,  # Stock bajo para testing
            "category": ProductCategory.CABELLO,
            "image_url": "https://example.com/image.jpg"
        },
    ]

    for product_data in products_data:
        product = Product(**product_data)
        db.add(product)
    
    db.commit()
    print(f"✅ {len(products_data)} productos creados")
    db.close()

def main():
    print("🌱 Iniciando seed de la base de datos")
    Base.metadata.create_all(bind=engine)

    clear_data()
    
    seed_admin_user()
    seed_products()

    print("✅ Seed completado exitosamente!")


if __name__ == "__main__":
    main()