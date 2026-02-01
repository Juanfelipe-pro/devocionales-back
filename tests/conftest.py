"""
Configuración y fixtures para tests de la API de Lista de Espera.

Nota: Los tests usan SQLite en memoria para velocidad y portabilidad.
La aplicación en producción usa PostgreSQL.
"""
import os
# IMPORTANTE: Configurar variables ANTES de importar la app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin123"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app, API_KEY

# Base de datos SQLite en memoria para tests (no requiere PostgreSQL)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de la dependencia de base de datos para tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override de la dependencia
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session():
    """
    Fixture que proporciona una sesión de base de datos limpia para cada test.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Fixture que proporciona un cliente de test con base de datos limpia.
    """
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def api_headers():
    """
    Fixture que proporciona headers con API Key válida.
    """
    return {"X-API-Key": API_KEY}


@pytest.fixture
def registro_valido():
    """
    Fixture que proporciona datos de un registro válido.
    """
    return {
        "tipo_documento": "CC",
        "numero_documento": "1234567890",
        "nombre": "María José",
        "apellido": "García López",
        "email": "maria@ejemplo.com",
        "indicativo_pais": "+57",
        "telefono": "3001234567",
        "ciudad": "Barranquilla",
        "referido": "redes_sociales",
        "acepta_terminos": True
    }


@pytest.fixture
def registro_minimo():
    """
    Fixture con datos mínimos requeridos (sin opcionales).
    """
    return {
        "tipo_documento": "CC",
        "numero_documento": "9876543210",
        "nombre": "Juan",
        "apellido": "Pérez",
        "email": "juan@ejemplo.com",
        "indicativo_pais": "+57",
        "telefono": "3109876543",
        "acepta_terminos": True
    }
