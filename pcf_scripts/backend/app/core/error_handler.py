"""
CEAPSI Backend - Secure Error Handler
Middleware para manejo seguro de errores sin exponer información sensible
"""

import logging
import uuid
from typing import Dict, Any
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import os

logger = logging.getLogger('CEAPSI_ERROR_HANDLER')

class SecureErrorHandler:
    """Manejador de errores seguro para producción"""
    
    def __init__(self):
        self.is_development = os.getenv('ENVIRONMENT', 'production').lower() in ['development', 'dev', 'debug']
        
        # Configurar nivel de logs según entorno
        if self.is_development:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        
        # Patrones de información sensible a sanitizar
        self.sensitive_patterns = [
            # Credenciales y keys
            r'password["\s]*[:=]["\s]*[^"\s]+',
            r'token["\s]*[:=]["\s]*[^"\s]+',
            r'key["\s]*[:=]["\s]*[^"\s]+',
            r'secret["\s]*[:=]["\s]*[^"\s]+',
            
            # Database connections
            r'postgresql://[^"\s]+',
            r'mysql://[^"\s]+',
            r'mongodb://[^"\s]+',
            
            # File paths que pueden exponer estructura
            r'[C-Z]:\\[^"\s]+',
            r'/home/[^"\s]+',
            r'/var/[^"\s]+',
            r'/usr/[^"\s]+',
            
            # Stack traces específicos
            r'File "[^"]+", line \d+',
            r'at [^\s]+ \([^)]+\)',
            
            # Información de sistema
            r'Python \d+\.\d+\.\d+',
            r'FastAPI \d+\.\d+\.\d+',
            r'uvicorn \d+\.\d+\.\d+'
        ]
    
    def generate_error_id(self) -> str:
        """Generar ID único para el error para tracking"""
        return f"ERR_{uuid.uuid4().hex[:8].upper()}"
    
    def sanitize_error_message(self, message: str) -> str:
        """Sanitizar mensaje de error removiendo información sensible"""
        import re
        
        sanitized = message
        
        # Reemplazar patrones sensibles
        for pattern in self.sensitive_patterns:
            sanitized = re.sub(pattern, '[SENSITIVE_DATA_REMOVED]', sanitized, flags=re.IGNORECASE)
        
        # Remover paths absolutos largos
        sanitized = re.sub(r'[/\\][a-zA-Z0-9_\\/-]{20,}', '[PATH_REMOVED]', sanitized)
        
        # Remover stack traces completos en producción
        if not self.is_development:
            # Mantener solo la primera línea del error
            lines = sanitized.split('\n')
            if len(lines) > 1:
                sanitized = lines[0] + " [Stack trace removed in production]"
        
        return sanitized
    
    def create_safe_error_response(
        self, 
        status_code: int, 
        error_type: str, 
        user_message: str,
        error_id: str,
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Crear respuesta de error segura para el usuario"""
        
        response = {
            "error": True,
            "error_id": error_id,
            "type": error_type,
            "message": user_message,
            "timestamp": datetime.now().isoformat(),
            "status_code": status_code
        }
        
        # Solo agregar detalles en desarrollo
        if self.is_development and details:
            response["debug_details"] = details
        
        return response
    
    def log_error_securely(
        self, 
        error: Exception, 
        request: Request, 
        error_id: str,
        additional_context: Dict[str, Any] = None
    ):
        """Log del error con información completa para debugging"""
        
        # Información básica del request (sanitizada)
        request_info = {
            "method": request.method,
            "url": str(request.url).split('?')[0],  # Remover query params
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")[:100],  # Limitar longitud
            "error_id": error_id
        }
        
        # Headers sanitizados (remover authorization)
        safe_headers = {
            k: v for k, v in request.headers.items() 
            if k.lower() not in ['authorization', 'cookie', 'x-api-key']
        }
        request_info["headers"] = safe_headers
        
        # Contexto adicional
        if additional_context:
            request_info.update(additional_context)
        
        # Log completo del error
        logger.error(
            f"Error {error_id}: {type(error).__name__}: {str(error)}\n"
            f"Request Info: {request_info}",
            exc_info=True if self.is_development else False
        )
    
    async def handle_http_exception(
        self, 
        request: Request, 
        exc: HTTPException
    ) -> JSONResponse:
        """Manejar HTTPExceptions de forma segura"""
        
        error_id = self.generate_error_id()
        
        # Log del error
        self.log_error_securely(exc, request, error_id, {
            "status_code": exc.status_code,
            "detail": exc.detail
        })
        
        # Determinar mensaje de usuario seguro
        if exc.status_code == 400:
            user_message = "Solicitud inválida. Verifique los datos enviados."
        elif exc.status_code == 401:
            user_message = "No autorizado. Verifique sus credenciales."
        elif exc.status_code == 403:
            user_message = "Acceso denegado. No tiene permisos para esta operación."
        elif exc.status_code == 404:
            user_message = "Recurso no encontrado."
        elif exc.status_code == 409:
            user_message = "Conflicto en la operación. El recurso ya existe o está en uso."
        elif exc.status_code == 413:
            user_message = "Archivo o datos demasiado grandes."
        elif exc.status_code == 422:
            user_message = "Datos inválidos. Verifique el formato."
        elif exc.status_code == 429:
            user_message = "Demasiadas solicitudes. Intente más tarde."
        else:
            user_message = "Error en la solicitud."
        
        # En desarrollo, mostrar el detalle original (sanitizado)
        if self.is_development and exc.detail:
            debug_detail = self.sanitize_error_message(str(exc.detail))
        else:
            debug_detail = None
        
        response_data = self.create_safe_error_response(
            status_code=exc.status_code,
            error_type="http_exception",
            user_message=user_message,
            error_id=error_id,
            details={"original_detail": debug_detail} if debug_detail else None
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response_data
        )
    
    async def handle_general_exception(
        self, 
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """Manejar excepciones generales de forma segura"""
        
        error_id = self.generate_error_id()
        
        # Log completo del error
        self.log_error_securely(exc, request, error_id, {
            "exception_type": type(exc).__name__
        })
        
        # Mensaje genérico para el usuario
        user_message = "Error interno del servidor. Por favor contacte al soporte."
        
        # En desarrollo, proporcionar más información (sanitizada)
        debug_details = None
        if self.is_development:
            debug_details = {
                "exception_type": type(exc).__name__,
                "message": self.sanitize_error_message(str(exc))
            }
        
        response_data = self.create_safe_error_response(
            status_code=500,
            error_type="internal_error",
            user_message=user_message,
            error_id=error_id,
            details=debug_details
        )
        
        return JSONResponse(
            status_code=500,
            content=response_data
        )
    
    async def handle_validation_error(
        self, 
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """Manejar errores de validación de Pydantic"""
        
        error_id = self.generate_error_id()
        
        # Log del error
        self.log_error_securely(exc, request, error_id, {
            "validation_error": True
        })
        
        # Extraer errores de validación de forma segura
        validation_errors = []
        if hasattr(exc, 'errors'):
            for error in exc.errors():
                safe_error = {
                    "field": ".".join(str(loc) for loc in error.get("loc", [])),
                    "message": error.get("msg", "Invalid field"),
                    "type": error.get("type", "validation_error")
                }
                validation_errors.append(safe_error)
        
        response_data = self.create_safe_error_response(
            status_code=422,
            error_type="validation_error",
            user_message="Datos de entrada inválidos.",
            error_id=error_id,
            details={"validation_errors": validation_errors} if validation_errors else None
        )
        
        return JSONResponse(
            status_code=422,
            content=response_data
        )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de errores (solo para admins)"""
        return {
            "environment": "development" if self.is_development else "production",
            "error_logging_enabled": True,
            "sensitive_data_sanitization": True,
            "timestamp": datetime.now().isoformat()
        }

# Instancia global del manejador de errores
error_handler = SecureErrorHandler()