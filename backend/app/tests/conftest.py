import pytest
from fastapi.testclient import TestClient #This class allows for making requests to your FastAPI application directly in a testing environment without requiring an actual HTTP server or network connection.
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    