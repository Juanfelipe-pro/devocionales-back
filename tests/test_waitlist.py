"""
Tests para la API de Lista de Espera.

Ejecutar con: pytest tests/ -v
"""
import pytest
from fastapi import status


class TestHealthCheck:
    """Tests para el endpoint de salud."""
    
    def test_health_check_sin_api_key(self, client):
        """El health check no requiere API key."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestAPIKeySecurity:
    """Tests de seguridad con API Key."""
    
    def test_endpoint_sin_api_key_retorna_422(self, client):
        """Endpoints protegidos sin API key retornan 422."""
        response = client.get("/api/waitlist")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_endpoint_con_api_key_invalida_retorna_401(self, client):
        """API key inválida retorna 401."""
        response = client.get(
            "/api/waitlist",
            headers={"X-API-Key": "clave-invalida"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "API Key inválida" in response.json()["error"]
    
    def test_endpoint_con_api_key_valida_funciona(self, client, api_headers):
        """API key válida permite acceso."""
        response = client.get("/api/waitlist", headers=api_headers)
        assert response.status_code == status.HTTP_200_OK


class TestRegistroExitoso:
    """Tests para registro exitoso en lista de espera."""
    
    def test_registro_completo_exitoso(self, client, api_headers, registro_valido):
        """Registro con todos los campos funciona."""
        response = client.post(
            "/api/waitlist",
            json=registro_valido,
            headers=api_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert "María José" in data["message"]
        assert data["data"]["nombre"] == "María José"
        assert data["data"]["apellido"] == "García López"
        assert data["data"]["posicion"] == 1
    
    def test_registro_minimo_exitoso(self, client, api_headers, registro_minimo):
        """Registro con campos mínimos funciona."""
        response = client.post(
            "/api/waitlist",
            json=registro_minimo,
            headers=api_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
    
    def test_email_se_normaliza_a_minusculas(self, client, api_headers, registro_valido):
        """Email se guarda en minúsculas."""
        registro_valido["email"] = "MARIA@EJEMPLO.COM"
        response = client.post(
            "/api/waitlist",
            json=registro_valido,
            headers=api_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["email"] == "maria@ejemplo.com"
    
    def test_nombre_se_capitaliza(self, client, api_headers, registro_valido):
        """Nombre se capitaliza correctamente."""
        registro_valido["nombre"] = "maría josé"
        registro_valido["apellido"] = "garcía lópez"
        response = client.post(
            "/api/waitlist",
            json=registro_valido,
            headers=api_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()["data"]
        assert data["nombre"] == "María José"
        assert data["apellido"] == "García López"


class TestValidacionDocumentos:
    """Tests de validación de documentos de identidad."""
    
    def test_cedula_ciudadania_valida(self, client, api_headers, registro_valido):
        """CC con 8 dígitos es válida."""
        registro_valido["tipo_documento"] = "CC"
        registro_valido["numero_documento"] = "12345678"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_cedula_ciudadania_muy_corta(self, client, api_headers, registro_valido):
        """CC con menos de 6 dígitos es inválida."""
        registro_valido["tipo_documento"] = "CC"
        registro_valido["numero_documento"] = "12345"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_cedula_ciudadania_con_letras(self, client, api_headers, registro_valido):
        """CC no puede tener letras."""
        registro_valido["tipo_documento"] = "CC"
        registro_valido["numero_documento"] = "1234567A"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_cedula_extranjeria_valida(self, client, api_headers, registro_valido):
        """CE alfanumérica de 6-7 caracteres es válida."""
        registro_valido["tipo_documento"] = "CE"
        registro_valido["numero_documento"] = "ABC1234"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_tarjeta_identidad_valida(self, client, api_headers, registro_valido):
        """TI de 10-11 dígitos es válida."""
        registro_valido["tipo_documento"] = "TI"
        registro_valido["numero_documento"] = "10012345678"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_pasaporte_valido(self, client, api_headers, registro_valido):
        """Pasaporte alfanumérico de 5-15 caracteres es válido."""
        registro_valido["tipo_documento"] = "PA"
        registro_valido["numero_documento"] = "AB1234567"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_201_CREATED


class TestValidacionTelefono:
    """Tests de validación de teléfono."""
    
    def test_telefono_valido(self, client, api_headers, registro_valido):
        """Teléfono de 10 dígitos es válido."""
        registro_valido["telefono"] = "3001234567"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_telefono_muy_corto(self, client, api_headers, registro_valido):
        """Teléfono de menos de 7 dígitos es inválido."""
        registro_valido["telefono"] = "123456"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_telefono_internacional(self, client, api_headers, registro_valido):
        """Teléfono con indicativo diferente es válido."""
        registro_valido["indicativo_pais"] = "+1"
        registro_valido["telefono"] = "2025551234"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_indicativo_invalido(self, client, api_headers, registro_valido):
        """Indicativo inválido retorna error."""
        registro_valido["indicativo_pais"] = "abc"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_telefono_con_espacios(self, client, api_headers, registro_valido):
        """Teléfono con espacios se normaliza."""
        registro_valido["telefono"] = "300 123 4567"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_201_CREATED


class TestValidacionEmail:
    """Tests de validación de email."""
    
    def test_email_invalido(self, client, api_headers, registro_valido):
        """Email mal formateado es rechazado."""
        registro_valido["email"] = "correo-invalido"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_email_sin_dominio(self, client, api_headers, registro_valido):
        """Email sin dominio es rechazado."""
        registro_valido["email"] = "correo@"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestValidacionNombre:
    """Tests de validación de nombre y apellido."""
    
    def test_nombre_muy_corto(self, client, api_headers, registro_valido):
        """Nombre de 1 carácter es rechazado."""
        registro_valido["nombre"] = "A"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_nombre_con_numeros(self, client, api_headers, registro_valido):
        """Nombre con números es rechazado."""
        registro_valido["nombre"] = "María123"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_nombre_con_acentos(self, client, api_headers, registro_valido):
        """Nombre con acentos es aceptado."""
        registro_valido["nombre"] = "José María"
        registro_valido["apellido"] = "González Muñoz"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_201_CREATED


class TestValidacionTerminos:
    """Tests de aceptación de términos (Ley 1581)."""
    
    def test_sin_aceptar_terminos(self, client, api_headers, registro_valido):
        """No aceptar términos es rechazado."""
        registro_valido["acepta_terminos"] = False
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Ley 1581" in str(response.json())


class TestDuplicados:
    """Tests de manejo de duplicados."""
    
    def test_email_duplicado(self, client, api_headers, registro_valido):
        """Email duplicado retorna 409."""
        # Primer registro
        client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        
        # Segundo registro con mismo email
        registro_valido["numero_documento"] = "9999999999"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "correo" in response.json()["error"].lower()
    
    def test_documento_duplicado(self, client, api_headers, registro_valido):
        """Documento duplicado retorna 409."""
        # Primer registro
        client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        
        # Segundo registro con mismo documento
        registro_valido["email"] = "otro@ejemplo.com"
        response = client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "documento" in response.json()["error"].lower()


class TestListarRegistros:
    """Tests para listar registros."""
    
    def test_listar_vacio(self, client, api_headers):
        """Lista vacía retorna array vacío."""
        response = client.get("/api/waitlist", headers=api_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_listar_con_registros(self, client, api_headers, registro_valido):
        """Lista con registros retorna datos."""
        client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        
        response = client.get("/api/waitlist", headers=api_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["nombre"] == "María José"


class TestContarRegistros:
    """Tests para contar registros."""
    
    def test_contar_vacio(self, client, api_headers):
        """Conteo sin registros retorna 0."""
        response = client.get("/api/waitlist/count", headers=api_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 0
    
    def test_contar_con_registros(self, client, api_headers, registro_valido):
        """Conteo con registros retorna cantidad correcta."""
        client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        
        response = client.get("/api/waitlist/count", headers=api_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 1


class TestVerificarEmail:
    """Tests para verificar email."""
    
    def test_email_no_existe(self, client, api_headers):
        """Email no registrado retorna exists=False."""
        response = client.get(
            "/api/waitlist/check/nuevo@ejemplo.com",
            headers=api_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["exists"] is False
    
    def test_email_existe(self, client, api_headers, registro_valido):
        """Email registrado retorna exists=True."""
        client.post("/api/waitlist", json=registro_valido, headers=api_headers)
        
        response = client.get(
            f"/api/waitlist/check/{registro_valido['email']}",
            headers=api_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["exists"] is True


class TestEliminarRegistro:
    """Tests para eliminar registros."""
    
    def test_eliminar_existente(self, client, api_headers, registro_valido):
        """Eliminar registro existente funciona."""
        # Crear
        create_response = client.post(
            "/api/waitlist",
            json=registro_valido,
            headers=api_headers
        )
        registro_id = create_response.json()["data"]["id"]
        
        # Eliminar
        response = client.delete(
            f"/api/waitlist/{registro_id}",
            headers=api_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        
        # Verificar eliminación
        count_response = client.get("/api/waitlist/count", headers=api_headers)
        assert count_response.json()["total"] == 0
    
    def test_eliminar_no_existente(self, client, api_headers):
        """Eliminar registro inexistente retorna 404."""
        response = client.delete("/api/waitlist/99999", headers=api_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestObtenerRegistro:
    """Tests para obtener registro por ID."""
    
    def test_obtener_existente(self, client, api_headers, registro_valido):
        """Obtener registro existente funciona."""
        create_response = client.post(
            "/api/waitlist",
            json=registro_valido,
            headers=api_headers
        )
        registro_id = create_response.json()["data"]["id"]
        
        response = client.get(
            f"/api/waitlist/{registro_id}",
            headers=api_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["nombre"] == "María José"
    
    def test_obtener_no_existente(self, client, api_headers):
        """Obtener registro inexistente retorna 404."""
        response = client.get("/api/waitlist/99999", headers=api_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPoliticaDatos:
    """Tests para endpoint de política de datos."""
    
    def test_obtener_politica(self, client, api_headers):
        """Política de datos está disponible."""
        response = client.get("/api/legal/politica-datos", headers=api_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Ley 1581" in data["ley"]
        assert "Sembradores de Fe" in data["responsable"]


class TestAdminLogin:
    """Tests para login de administrador."""
    
    def test_login_exitoso(self, client):
        """Login con credenciales correctas retorna API key."""
        # Usa las credenciales por defecto del código
        response = client.post(
            "/api/admin/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "api_key" in data
        assert len(data["api_key"]) > 0
    
    def test_login_usuario_incorrecto(self, client):
        """Login con usuario incorrecto retorna 401."""
        response = client.post(
            "/api/admin/login",
            json={"username": "wrong", "password": "admin123"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_password_incorrecto(self, client):
        """Login con contraseña incorrecta retorna 401."""
        response = client.post(
            "/api/admin/login",
            json={"username": "admin", "password": "wrongpass"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_sin_credenciales(self, client):
        """Login sin credenciales retorna 422."""
        response = client.post("/api/admin/login", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
