# 🕊️ API Lista de Espera - Sembradores de Fe

API REST para la lista de espera del devocional "Despertando con el Espíritu Santo".

## 📋 Características

- ✅ Validación de documentos colombianos (CC, CE, TI, PA)
- ✅ Indicativo de país para teléfonos internacionales
- ✅ Cumplimiento Ley 1581 de 2012
- ✅ Login de administrador
- ✅ API Key de seguridad
- ✅ PostgreSQL con **connection pooling** (alta concurrencia)
- ✅ 42 tests automatizados

## 🚀 Instalación

```bash
cd waitlist-api

# Instalar dependencias
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic[email] pytest httpx python-dotenv

# Crear base de datos
psql -U postgres -c "CREATE DATABASE waitlist_db;"

# Editar .env con tu password de PostgreSQL

# Ejecutar
uvicorn app.main:app --reload
```

## 🔧 Configuración (.env)

```env
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/waitlist_db
API_KEY=a7f3e9b1c4d8f2a6e0b5c9d3f7a1e4b8c2d6f0a9e3b7c1d5f8a2e6b0c4d9f3a7
ADMIN_USERNAME=admin
ADMIN_PASSWORD=SembradoresDeFe2025
ALLOWED_ORIGINS=http://localhost:4321,http://localhost:3000
```

## 🔐 Login Admin

```bash
POST /api/admin/login
{
  "username": "admin",
  "password": "SembradoresDeFe2025"
}
```

## 📡 Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /health | Estado del servidor |
| POST | /api/admin/login | Login administrador |
| POST | /api/waitlist | Registrar en lista |
| GET | /api/waitlist | Listar registros |
| GET | /api/waitlist/count | Contar registros |
| GET | /api/waitlist/{id} | Obtener registro |
| DELETE | /api/waitlist/{id} | Eliminar registro |

## 🔥 Alta Concurrencia

El backend está configurado con connection pooling:

- **pool_size=10**: 10 conexiones permanentes
- **max_overflow=20**: Hasta 30 conexiones en picos
- **pool_pre_ping=True**: Verifica conexiones antes de usar

Esto permite manejar muchos usuarios simultáneos sin problemas.

## 🧪 Tests

```bash
pytest tests/ -v
# 42 passed ✅
```

---

**Sembradores de Fe** - Barranquilla, Colombia
