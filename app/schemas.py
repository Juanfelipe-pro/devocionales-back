"""
Schemas Pydantic para validación de datos de la lista de espera.

Incluye validaciones específicas para Colombia:
- Tipos de documento (CC, CE, TI, PA)
- Formato de teléfono colombiano
- Ley 1581 de 2012 (Protección de datos personales)
"""
from pydantic import BaseModel, Field, field_validator, model_validator, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum
import re


class TipoDocumento(str, Enum):
    """Tipos de documento de identidad válidos en Colombia."""
    CC = "CC"   # Cédula de Ciudadanía
    CE = "CE"   # Cédula de Extranjería  
    TI = "TI"   # Tarjeta de Identidad
    PA = "PA"   # Pasaporte


class Referido(str, Enum):
    """Opciones de cómo conoció el devocional."""
    REDES_SOCIALES = "redes_sociales"
    AMIGO = "amigo"
    PARROQUIA = "parroquia"
    COMUNIDAD = "comunidad"
    OTRO = "otro"


class WaitlistCreate(BaseModel):
    """
    Schema para crear un nuevo registro en la lista de espera.
    
    Todos los campos requeridos deben ser proporcionados.
    La aceptación de términos es obligatoria según Ley 1581 de 2012.
    """
    
    tipo_documento: TipoDocumento = Field(
        ...,
        description="Tipo de documento de identidad",
        examples=["CC"]
    )
    
    numero_documento: str = Field(
        ...,
        min_length=5,
        max_length=20,
        description="Número de documento sin puntos ni guiones",
        examples=["1234567890"]
    )
    
    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nombre(s) del usuario",
        examples=["María José"]
    )
    
    apellido: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Apellido(s) del usuario",
        examples=["García López"]
    )
    
    email: EmailStr = Field(
        ...,
        description="Correo electrónico válido",
        examples=["maria@ejemplo.com"]
    )
    
    indicativo_pais: str = Field(
        default="+57",
        pattern=r"^\+\d{1,4}$",
        description="Indicativo del país (ej: +57, +1, +34)",
        examples=["+57"]
    )
    
    telefono: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Número de celular (10 dígitos)",
        examples=["3001234567"]
    )
    
    ciudad: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Ciudad de residencia (opcional)",
        examples=["Barranquilla"]
    )
    
    referido: Optional[Referido] = Field(
        default=None,
        description="¿Cómo conociste el devocional? (opcional)",
        examples=["redes_sociales"]
    )
    
    acepta_terminos: bool = Field(
        ...,
        description="Aceptación de política de tratamiento de datos (Ley 1581 de 2012)"
    )

    @field_validator('nombre', 'apellido')
    @classmethod
    def validar_nombre(cls, v: str, info) -> str:
        """Valida que nombre y apellido contengan solo letras y espacios."""
        v = v.strip()
        if not v:
            campo = info.field_name
            raise ValueError(f'El {campo} no puede estar vacío')
        
        # Permite letras (incluyendo acentos), espacios y guiones
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']+$", v):
            campo = info.field_name
            raise ValueError(f'El {campo} solo puede contener letras, espacios y guiones')
        
        # Capitalizar cada palabra
        return ' '.join(word.capitalize() for word in v.split())

    @field_validator('numero_documento')
    @classmethod
    def validar_numero_documento(cls, v: str) -> str:
        """Valida formato básico del número de documento."""
        # Remover espacios y guiones
        v = re.sub(r'[\s\-\.]', '', v)
        
        if not v:
            raise ValueError('El número de documento no puede estar vacío')
        
        return v

    @model_validator(mode='after')
    def validar_documento_por_tipo(self):
        """
        Valida el número de documento según su tipo.
        
        - CC (Cédula de Ciudadanía): 6-10 dígitos numéricos
        - CE (Cédula de Extranjería): 6-7 caracteres alfanuméricos
        - TI (Tarjeta de Identidad): 10-11 dígitos numéricos
        - PA (Pasaporte): 5-15 caracteres alfanuméricos
        """
        tipo = self.tipo_documento
        numero = self.numero_documento
        
        if tipo == TipoDocumento.CC:
            if not numero.isdigit():
                raise ValueError('La Cédula de Ciudadanía debe contener solo números')
            if not (6 <= len(numero) <= 10):
                raise ValueError('La Cédula de Ciudadanía debe tener entre 6 y 10 dígitos')
                
        elif tipo == TipoDocumento.CE:
            if not numero.isalnum():
                raise ValueError('La Cédula de Extranjería debe ser alfanumérica')
            if not (6 <= len(numero) <= 7):
                raise ValueError('La Cédula de Extranjería debe tener entre 6 y 7 caracteres')
                
        elif tipo == TipoDocumento.TI:
            if not numero.isdigit():
                raise ValueError('La Tarjeta de Identidad debe contener solo números')
            if not (10 <= len(numero) <= 11):
                raise ValueError('La Tarjeta de Identidad debe tener entre 10 y 11 dígitos')
                
        elif tipo == TipoDocumento.PA:
            if not numero.isalnum():
                raise ValueError('El Pasaporte debe ser alfanumérico')
            if not (5 <= len(numero) <= 15):
                raise ValueError('El Pasaporte debe tener entre 5 y 15 caracteres')
        
        return self

    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v: str) -> str:
        """
        Valida formato de teléfono.
        Debe tener entre 7 y 15 dígitos.
        """
        # Remover espacios, guiones y paréntesis
        v = re.sub(r'[\s\-\(\)\.]', '', v)
        
        if not v.isdigit():
            raise ValueError('El teléfono debe contener solo números')
        
        if len(v) < 7 or len(v) > 15:
            raise ValueError('El teléfono debe tener entre 7 y 15 dígitos')
        
        return v
    
    @field_validator('indicativo_pais')
    @classmethod
    def validar_indicativo(cls, v: str) -> str:
        """Valida el indicativo de país."""
        if not v.startswith('+'):
            v = '+' + v
        if not re.match(r'^\+\d{1,4}$', v):
            raise ValueError('Indicativo inválido (ej: +57, +1, +34)')
        return v

    @field_validator('email')
    @classmethod
    def normalizar_email(cls, v: str) -> str:
        """Normaliza el email a minúsculas."""
        return v.lower().strip()

    @field_validator('ciudad')
    @classmethod
    def validar_ciudad(cls, v: Optional[str]) -> Optional[str]:
        """Valida y capitaliza la ciudad si se proporciona."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        return v.title()

    @field_validator('acepta_terminos')
    @classmethod
    def validar_aceptacion_terminos(cls, v: bool) -> bool:
        """
        Valida que el usuario acepte los términos.
        Requerido por Ley 1581 de 2012.
        """
        if not v:
            raise ValueError(
                'Debe aceptar la política de tratamiento de datos personales '
                'para continuar (Ley 1581 de 2012)'
            )
        return v


class WaitlistResponse(BaseModel):
    """Schema para respuesta de registro exitoso."""
    
    success: bool = True
    message: str
    data: dict
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "¡Estás en la lista! Te contactaremos pronto.",
                "data": {
                    "id": 1,
                    "nombre": "María José",
                    "apellido": "García López",
                    "email": "maria@ejemplo.com",
                    "posicion": 1
                }
            }
        }
    }


class WaitlistDetail(BaseModel):
    """Schema para detalle completo de un registro."""
    
    id: int
    tipo_documento: TipoDocumento
    numero_documento: str
    nombre: str
    apellido: str
    email: str
    indicativo_pais: str
    telefono: str
    ciudad: Optional[str]
    referido: Optional[Referido]
    fecha_registro: datetime
    
    model_config = {
        "from_attributes": True
    }


class WaitlistCount(BaseModel):
    """Schema para conteo de registros."""
    
    total: int
    message: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 150,
                "message": "150 personas esperando el lanzamiento"
            }
        }
    }


class EmailCheck(BaseModel):
    """Schema para verificar si un email existe."""
    
    exists: bool
    message: str


class HealthCheck(BaseModel):
    """Schema para estado del servidor."""
    
    status: str
    timestamp: datetime
    version: str


class AdminLogin(BaseModel):
    """Schema para login de administrador."""
    
    username: str = Field(..., min_length=3, description="Usuario administrador")
    password: str = Field(..., min_length=4, description="Contraseña")


class AdminLoginResponse(BaseModel):
    """Schema para respuesta de login exitoso."""
    
    success: bool
    message: str
    api_key: str
    expires: str
