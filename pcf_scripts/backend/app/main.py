"""
CEAPSI Backend - FastAPI Application
Sistema de análisis de llamadas para call center
"""

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError
import uvicorn
import logging
from pathlib import Path
import sys
import os
from datetime import datetime
import tempfile
import pandas as pd

# Add src directory to path for imports
current_dir = Path(__file__).parent.parent.parent.absolute()
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from core.mcp_session_manager import get_mcp_session_manager
from api.routers import analysis, sessions, data, models, reservo
from core.config import get_settings
from core.supabase_auth import get_current_user, get_current_user_optional
from core.rate_limiter import apply_rate_limit, rate_limiter
from core.error_handler import error_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CEAPSI_BACKEND')

# Initialize FastAPI app
app = FastAPI(
    title="CEAPSI Backend API",
    description="Sistema de análisis de llamadas para call center",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for Streamlit Cloud
allowed_origins = [
    "https://*.streamlit.app",
    "http://localhost:8501",
    "http://localhost:3000",
    "https://ceapsi-app.streamlit.app",
    "https://ceapsi-frontend.streamlit.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware para aplicar rate limiting a todas las requests"""
    try:
        # Solo aplicar rate limiting a endpoints de API
        if request.url.path.startswith("/api/"):
            user_id = None
            
            # Intentar obtener user_id si hay token de autorización
            if "authorization" in request.headers:
                try:
                    from core.supabase_auth import supabase_auth
                    token = request.headers["authorization"].replace("Bearer ", "")
                    user_data = supabase_auth.verify_token(token)
                    user_id = user_data.get("user_id")
                except:
                    pass  # Token inválido o expirado, continuar sin user_id
            
            # Aplicar rate limiting
            await apply_rate_limit(
                request=request,
                endpoint=request.url.path,
                user_id=user_id
            )
        
        # Continuar con la request
        response = await call_next(request)
        
        # Agregar headers de rate limiting
        if request.url.path.startswith("/api/"):
            response.headers["X-RateLimit-Applied"] = "true"
        
        return response
        
    except HTTPException as e:
        # Rate limit excedido
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail,
            headers={
                "X-RateLimit-Applied": "true",
                "X-RateLimit-Exceeded": "true"
            }
        )
    except Exception as e:
        logger.error(f"Error in rate limit middleware: {e}")
        # En caso de error, permitir la request (fail open)
        return await call_next(request)

# Include routers
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(data.router, prefix="/api/v1/data", tags=["data"])
app.include_router(models.router, prefix="/api/v1/models", tags=["models"])
app.include_router(reservo.router, prefix="/api/v1/reservo", tags=["reservo"])

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "CEAPSI Backend API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        session_manager = get_mcp_session_manager()
        
        # Test Supabase Auth
        from core.supabase_auth import get_supabase_client
        supabase = get_supabase_client()
        
        # Test Reservo API if configured
        reservo_status = False
        try:
            import requests
            reservo_url = os.getenv('API_URL', 'https://reservo.cl/APIpublica/v2')
            reservo_key = os.getenv('API_KEY')
            if reservo_key:
                response = requests.get(f"{reservo_url}/test", 
                                      headers={"Authorization": reservo_key}, 
                                      timeout=5)
                reservo_status = response.status_code == 200
        except:
            reservo_status = False
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "mcp_supabase": True,
                "session_manager": True,
                "supabase_auth": True,
                "reservo_api": reservo_status,
                "error_handler": True,
                "rate_limiter": True
            }
        }
    except Exception as e:
        # Let the secure error handler manage this
        raise HTTPException(
            status_code=503,
            detail="Health check failed"
        )

@app.get("/admin/error-stats")
async def get_error_statistics(user: dict = Depends(get_current_user)):
    """Get error handling statistics (admin only)"""
    if user.get('role') != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden acceder a estadísticas de errores"
        )
    
    # Combinar estadísticas de diferentes sistemas
    stats = {
        "error_handler": error_handler.get_error_stats(),
        "rate_limiter": rate_limiter.get_stats(),
        "timestamp": datetime.now().isoformat(),
        "requested_by": user.get('user_id')
    }
    
    return stats

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Secure HTTP exception handler"""
    return await error_handler.handle_http_exception(request, exc)

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Secure validation exception handler"""
    return await error_handler.handle_validation_error(request, exc)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Secure general exception handler"""
    return await error_handler.handle_general_exception(request, exc)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )