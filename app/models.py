"""
Modelos SQLAlchemy para la lista de espera.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum


class TipoDocumento(str, enum.Enum):
    """Tipos de documento de identidad en Colombia."""
    CC = "CC"   # Cédula de Ciudadanía
    CE = "CE"   # Cédula de Extranjería
    TI = "TI"   # Tarjeta de Identidad
    PA = "PA"   # Pasaporte


class Referido(str, enum.Enum):
    """Cómo conoció el usuario el devocional."""
    REDES_SOCIALES = "redes_sociales"
    AMIGO = "amigo"
    PARROQUIA = "parroquia"
    COMUNIDAD = "comunidad"
    OTRO = "otro"


class WaitlistEntry(Base):
    """
    Modelo para registros en la lista de espera.
    
    Almacena información de usuarios interesados en el devocional
    antes del lanzamiento oficial.
    """
    __tablename__ = "waitlist"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Documento de identidad
    tipo_documento = Column(SQLEnum(TipoDocumento), nullable=False)
    numero_documento = Column(String(20), nullable=False, unique=True, index=True)
    
    # Datos personales
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    indicativo_pais = Column(String(5), nullable=False, default="+57")
    telefono = Column(String(15), nullable=False)
    ciudad = Column(String(100), nullable=True)
    
    # Marketing
    referido = Column(SQLEnum(Referido), nullable=True)
    
    # Legal - Ley 1581 de 2012
    acepta_terminos = Column(Boolean, nullable=False, default=False)
    
    # Metadatos
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    ip_registro = Column(String(45), nullable=True)  # Soporta IPv6
    
    def __repr__(self):
        return f"<WaitlistEntry {self.nombre} {self.apellido} ({self.email})>"
    
    @property
    def telefono_completo(self):
        return f"{self.indicativo_pais}{self.telefono}"
