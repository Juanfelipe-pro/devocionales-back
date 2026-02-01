"""
Configuración de base de datos PostgreSQL para lista de espera.
Soporta SQLite para tests (variable DATABASE_URL).
Configurado para manejar alta concurrencia con connection pooling.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool, StaticPool
import os

# Cargar .env sin sobrescribir variables existentes
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

# Configuración de Base de Datos
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/waitlist_db"
)

# Configuración del engine según el tipo de BD
if DATABASE_URL.startswith("sqlite"):
    # SQLite para tests - usa StaticPool para conexiones en memoria
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    # PostgreSQL para producción - Connection pooling para alta concurrencia
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,           # Conexiones permanentes en el pool
        max_overflow=20,        # Conexiones extra cuando hay mucha demanda
        pool_timeout=30,        # Segundos de espera para obtener conexión
        pool_recycle=1800,      # Reciclar conexiones cada 30 minutos
        pool_pre_ping=True      # Verificar conexión antes de usar
    )

# Crear sesión con configuración para concurrencia
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Evita recargas innecesarias después de commit
)

# Base para modelos
Base = declarative_base()


def get_db():
    """
    Dependency que proporciona una sesión de base de datos.
    Se cierra automáticamente al terminar el request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa la base de datos creando todas las tablas.
    """
    Base.metadata.create_all(bind=engine)
