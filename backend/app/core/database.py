from sqlalchemy import create_engine #function is fundamental for establishing a connection to a database.
from sqlalchemy.ext.declarative import declarative_base #function that returns a new base class
from sqlalchemy.orm import sessionmaker #enerates new Session objects with a fixed configuration.
from .config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally: 
        db.close()