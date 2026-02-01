"""
API de Lista de Espera - Sembradores de Fe
==========================================

API REST para gestionar registros de lista de espera del devocional
"Despertando con el Espíritu Santo".

Seguridad: Todos los endpoints requieren API Key en header X-API-Key

Cumplimiento: Ley 1581 de 2012 (Protección de Datos Personales - Colombia)
"""
import os
from dotenv import load_dotenv

# Cargar .env sin sobrescribir variables ya existentes (útil para tests)
load_dotenv(override=False)

from fastapi import FastAPI, Depends, HTTPException, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime

from app.database import get_db, init_db
from app.models import WaitlistEntry, TipoDocumento as TipoDocumentoModel, Referido as ReferidoModel
from app.schemas import (
    WaitlistCreate, 
    WaitlistResponse, 
    WaitlistDetail,
    WaitlistCount,
    EmailCheck,
    HealthCheck,
    AdminLogin,
    AdminLoginResponse
)

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

API_KEY = os.getenv("API_KEY", "tu-api-key-segura-cambiar-en-produccion")
API_VERSION = "1.0.0"
LAUNCH_DATE = os.getenv("LAUNCH_DATE", "2025-02-05")

# Credenciales Admin
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Dominios permitidos para CORS (configurar según tu dominio)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:5500,https://devocionales-taupe.vercel.app").split(",")


# =============================================================================
# LIFESPAN (inicialización de BD)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa la base de datos al arrancar."""
    init_db()
    yield


# =============================================================================
# APLICACIÓN FASTAPI
# =============================================================================

app = FastAPI(
    title="Sembradores de Fe - Lista de Espera API",
    description="""
## API de Lista de Espera

Sistema de registro para el devocional **"Despertando con el Espíritu Santo"**.

### Características:
- ✅ Registro de usuarios en lista de espera
- ✅ Validación de documentos colombianos (CC, CE, TI, PA)
- ✅ Cumplimiento Ley 1581 de 2012
- ✅ Protección con API Key

### Seguridad:
Todos los endpoints requieren el header `X-API-Key` con una clave válida.

### Contacto:
Sembradores de Fe - Barranquilla, Colombia
    """,
    version=API_VERSION,
    lifespan=lifespan,
    contact={
        "name": "Sembradores de Fe",
        "url": "https://sembradoresdefé.com",
    },
    license_info={
        "name": "Privado",
    }
)

# =============================================================================
# MIDDLEWARE
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# =============================================================================
# DEPENDENCIAS DE SEGURIDAD
# =============================================================================

async def verify_api_key(x_api_key: str = Header(..., description="API Key de autenticación")):
    """
    Verifica que la API Key proporcionada sea válida.
    
    Se requiere en TODOS los endpoints.
    Enviar en header: X-API-Key: tu-clave
    """
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o no proporcionada",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    return x_api_key


# =============================================================================
# MANEJADORES DE EXCEPCIONES
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejador personalizado para excepciones HTTP."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get(
    "/health",
    response_model=HealthCheck,
    tags=["Sistema"],
    summary="Estado del servidor",
    description="Verifica que el servidor esté funcionando correctamente."
)
async def health_check():
    """
    Endpoint de salud del servidor.
    
    No requiere autenticación.
    """
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        version=API_VERSION
    )


@app.post(
    "/api/admin/login",
    response_model=AdminLoginResponse,
    tags=["Admin"],
    summary="Login de administrador",
    description="Autentica al administrador y devuelve la API Key para acceder a los endpoints protegidos."
)
async def admin_login(credentials: AdminLogin):
    """
    Login para administrador.
    
    Devuelve la API Key si las credenciales son correctas.
    """
    if credentials.username != ADMIN_USERNAME or credentials.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos"
        )
    
    return AdminLoginResponse(
        success=True,
        message=f"Bienvenido {credentials.username}",
        api_key=API_KEY,
        expires="Session activa mientras el servidor esté corriendo"
    )


@app.post(
    "/api/waitlist",
    response_model=WaitlistResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Lista de Espera"],
    summary="Registrar en lista de espera",
    description="""
Registra un nuevo usuario en la lista de espera.

**Campos requeridos:**
- tipo_documento: CC, CE, TI o PA
- numero_documento: Según tipo de documento
- nombre: Nombre(s)
- apellido: Apellido(s)
- email: Correo electrónico válido
- telefono: Celular colombiano (10 dígitos, inicia con 3)
- acepta_terminos: Debe ser `true`

**Campos opcionales:**
- ciudad: Ciudad de residencia
- referido: Cómo conoció el devocional

**Validaciones de documento:**
- CC: 6-10 dígitos numéricos
- CE: 6-7 caracteres alfanuméricos
- TI: 10-11 dígitos numéricos
- PA: 5-15 caracteres alfanuméricos
    """
)
async def crear_registro(
    registro: WaitlistCreate,
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Crea un nuevo registro en la lista de espera."""
    
    # Obtener IP del cliente (para auditoría)
    client_ip = request.client.host if request.client else None
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    # Crear entrada en base de datos
    db_entry = WaitlistEntry(
        tipo_documento=TipoDocumentoModel(registro.tipo_documento.value),
        numero_documento=registro.numero_documento,
        nombre=registro.nombre,
        apellido=registro.apellido,
        email=registro.email,
        indicativo_pais=registro.indicativo_pais,
        telefono=registro.telefono,
        ciudad=registro.ciudad,
        referido=ReferidoModel(registro.referido.value) if registro.referido else None,
        acepta_terminos=registro.acepta_terminos,
        ip_registro=client_ip
    )
    
    try:
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig).lower()
        
        if "email" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este correo electrónico ya está registrado en la lista de espera."
            )
        elif "numero_documento" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este número de documento ya está registrado en la lista de espera."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un registro con estos datos."
            )
    
    # Calcular posición en la lista
    posicion = db.query(WaitlistEntry).filter(
        WaitlistEntry.id <= db_entry.id
    ).count()
    
    return WaitlistResponse(
        success=True,
        message=f"¡Bienvenido/a {registro.nombre}! Estás en la lista de espera. "
                f"Te contactaremos al correo {registro.email} cuando lancemos el {LAUNCH_DATE}.",
        data={
            "id": db_entry.id,
            "nombre": db_entry.nombre,
            "apellido": db_entry.apellido,
            "email": db_entry.email,
            "posicion": posicion,
            "fecha_registro": db_entry.fecha_registro.isoformat() if db_entry.fecha_registro else None
        }
    )


@app.get(
    "/api/waitlist",
    response_model=List[WaitlistDetail],
    tags=["Lista de Espera"],
    summary="Listar todos los registros",
    description="Obtiene todos los registros de la lista de espera. Uso administrativo."
)
async def listar_registros(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Lista todos los registros con paginación."""
    
    registros = db.query(WaitlistEntry).order_by(
        WaitlistEntry.fecha_registro.desc()
    ).offset(skip).limit(limit).all()
    
    return registros


@app.get(
    "/api/waitlist/count",
    response_model=WaitlistCount,
    tags=["Lista de Espera"],
    summary="Contar registros",
    description="Obtiene el número total de registros en la lista de espera."
)
async def contar_registros(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Cuenta el total de registros."""
    
    total = db.query(WaitlistEntry).count()
    
    return WaitlistCount(
        total=total,
        message=f"{total} {'persona espera' if total == 1 else 'personas esperan'} el lanzamiento"
    )


@app.get(
    "/api/waitlist/check/{email}",
    response_model=EmailCheck,
    tags=["Lista de Espera"],
    summary="Verificar email",
    description="Verifica si un email ya está registrado en la lista de espera."
)
async def verificar_email(
    email: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Verifica si un email existe en la lista."""
    
    email_lower = email.lower().strip()
    exists = db.query(WaitlistEntry).filter(
        WaitlistEntry.email == email_lower
    ).first() is not None
    
    if exists:
        return EmailCheck(
            exists=True,
            message="Este correo ya está registrado en la lista de espera."
        )
    
    return EmailCheck(
        exists=False,
        message="Este correo está disponible."
    )


@app.get(
    "/api/waitlist/{registro_id}",
    response_model=WaitlistDetail,
    tags=["Lista de Espera"],
    summary="Obtener registro por ID",
    description="Obtiene los detalles de un registro específico."
)
async def obtener_registro(
    registro_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Obtiene un registro por su ID."""
    
    registro = db.query(WaitlistEntry).filter(
        WaitlistEntry.id == registro_id
    ).first()
    
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró registro con ID {registro_id}"
        )
    
    return registro


@app.delete(
    "/api/waitlist/{registro_id}",
    tags=["Lista de Espera"],
    summary="Eliminar registro",
    description="Elimina un registro de la lista de espera. Uso administrativo."
)
async def eliminar_registro(
    registro_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Elimina un registro por su ID."""
    
    registro = db.query(WaitlistEntry).filter(
        WaitlistEntry.id == registro_id
    ).first()
    
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró registro con ID {registro_id}"
        )
    
    nombre_completo = f"{registro.nombre} {registro.apellido}"
    
    db.delete(registro)
    db.commit()
    
    return {
        "success": True,
        "message": f"Registro de {nombre_completo} eliminado correctamente",
        "deleted_id": registro_id
    }


# =============================================================================
# ENDPOINT DE INFORMACIÓN LEGAL
# =============================================================================

@app.get(
    "/api/legal/politica-datos",
    tags=["Legal"],
    summary="Política de tratamiento de datos",
    description="Texto de la política de tratamiento de datos según Ley 1581 de 2012."
)
async def politica_datos(api_key: str = Depends(verify_api_key)):
    """Retorna el texto de la política de datos."""
    
    return {
        "titulo": "Política de Tratamiento de Datos Personales",
        "ley": "Ley 1581 de 2012 y Decreto 1377 de 2013",
        "responsable": "Sembradores de Fe",
        "direccion": "Calle 76 # 57-61, Barranquilla, Colombia",
        "contacto": "300 3211933",
        "texto": """
Al registrarte en nuestra lista de espera, autorizas a Sembradores de Fe para:

1. RECOLECCIÓN: Recopilar tus datos personales (nombre, documento de identidad, 
   correo electrónico, teléfono y ciudad) con el fin de informarte sobre el 
   lanzamiento del devocional "Despertando con el Espíritu Santo".

2. TRATAMIENTO: Usar tus datos para enviarte comunicaciones relacionadas con 
   el devocional, incluyendo el aviso de lanzamiento, instrucciones de acceso 
   y contenido relacionado.

3. ALMACENAMIENTO: Conservar tus datos de forma segura mientras dure tu 
   suscripción al devocional o hasta que solicites su eliminación.

4. DERECHOS: Tienes derecho a conocer, actualizar, rectificar y eliminar tus 
   datos personales en cualquier momento, contactándonos a través de nuestros 
   canales oficiales.

5. SEGURIDAD: Implementamos medidas de seguridad técnicas y organizativas para 
   proteger tus datos contra acceso no autorizado.

Esta autorización es voluntaria. Al marcar la casilla de aceptación, confirmas 
que has leído y aceptas esta política.
        """,
        "fecha_actualizacion": "2025-01-31"
    }


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
