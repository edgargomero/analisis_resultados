"""
CEAPSI Backend - Reservo API Integration Router
Endpoints para integración con API de Reservo
"""

import os
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
import requests
import pandas as pd
from datetime import datetime, timedelta

from core.supabase_auth import get_current_user, get_current_user_optional

logger = logging.getLogger('CEAPSI_RESERVO_API')

router = APIRouter()

class ReservoAPIClient:
    """Cliente para la API de Reservo"""
    
    def __init__(self):
        self.api_url = os.getenv('API_URL', 'https://reservo.cl/APIpublica/v2')
        self.api_key = os.getenv('API_KEY')
        
        if not self.api_key:
            logger.warning("API_KEY de Reservo no configurada")
    
    def _get_headers(self) -> Dict[str, str]:
        """Headers para requests a Reservo API"""
        if not self.api_key:
            raise HTTPException(status_code=500, detail="API Key de Reservo no configurada")
        
        return {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Prueba la conexión con la API de Reservo"""
        try:
            response = requests.get(
                f"{self.api_url}/test",
                headers=self._get_headers(),
                timeout=10
            )
            
            return {
                "connected": response.status_code == 200,
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "api_url": self.api_url
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error conectando con Reservo API: {e}")
            return {
                "connected": False,
                "error": str(e),
                "api_url": self.api_url
            }
    
    def get_professionals(self) -> List[Dict[str, Any]]:
        """Obtiene lista de profesionales desde Reservo"""
        try:
            response = requests.get(
                f"{self.api_url}/professionals",
                headers=self._get_headers(),
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error en Reservo API: {response.text}"
                )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo profesionales: {e}")
            raise HTTPException(status_code=503, detail=f"Error de conectividad: {str(e)}")
    
    def get_appointments(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Obtiene citas desde Reservo"""
        try:
            params = {}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            
            response = requests.get(
                f"{self.api_url}/appointments",
                headers=self._get_headers(),
                params=params,
                timeout=20
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error en Reservo API: {response.text}"
                )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo citas: {e}")
            raise HTTPException(status_code=503, detail=f"Error de conectividad: {str(e)}")

# Instancia global del cliente
reservo_client = ReservoAPIClient()

@router.get("/status")
async def get_reservo_status(user: dict = Depends(get_current_user_optional)):
    """Estado de la integración con Reservo API"""
    try:
        status = reservo_client.test_connection()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "api_configured": reservo_client.api_key is not None,
            "connection_status": status,
            "user_authenticated": user is not None
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado Reservo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-connection")
async def test_reservo_connection(user: dict = Depends(get_current_user)):
    """Prueba la conexión con Reservo API"""
    try:
        result = reservo_client.test_connection()
        
        if result["connected"]:
            return {
                "message": "✅ Conexión exitosa con Reservo API",
                "details": result
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "message": "❌ Error de conexión con Reservo API",
                    "details": result
                }
            )
            
    except Exception as e:
        logger.error(f"Error en test de conexión: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/professionals")
async def get_professionals(user: dict = Depends(get_current_user)):
    """Obtiene lista de profesionales desde Reservo"""
    try:
        professionals = reservo_client.get_professionals()
        
        return {
            "total_count": len(professionals),
            "professionals": professionals,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo profesionales: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/appointments")
async def get_appointments(
    start_date: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    user: dict = Depends(get_current_user)
):
    """Obtiene citas desde Reservo API"""
    try:
        # Validar fechas si se proporcionan
        if start_date:
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha inicio inválido (YYYY-MM-DD)")
        
        if end_date:
            try:
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha fin inválido (YYYY-MM-DD)")
        
        # Si no se especifican fechas, usar últimos 30 días
        if not start_date and not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        appointments = reservo_client.get_appointments(start_date, end_date)
        
        return {
            "total_count": len(appointments),
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "appointments": appointments,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo citas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_reservo_statistics(
    days: int = Query(30, description="Días hacia atrás para estadísticas"),
    user: dict = Depends(get_current_user)
):
    """Obtiene estadísticas de uso de Reservo API"""
    try:
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Días debe estar entre 1 y 365")
        
        # Aquí se podría implementar estadísticas desde la base de datos
        # Por ahora retornamos estadísticas mock
        
        stats = {
            "period_days": days,
            "api_calls": {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0
            },
            "response_times": {
                "average_ms": 0,
                "min_ms": 0,
                "max_ms": 0
            },
            "data_retrieved": {
                "professionals": 0,
                "appointments": 0,
                "total_records": 0
            },
            "last_call": None,
            "message": "Estadísticas en desarrollo. Requiere implementación de auditoría."
        }
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-data")
async def sync_reservo_data(
    sync_professionals: bool = Query(True, description="Sincronizar profesionales"),
    sync_appointments: bool = Query(True, description="Sincronizar citas"),
    days_back: int = Query(30, description="Días hacia atrás para sincronizar"),
    user: dict = Depends(get_current_user)
):
    """Sincroniza datos desde Reservo API"""
    try:
        # Verificar permisos
        user_role = user.get('role', 'viewer')
        if user_role not in ['admin', 'analista']:
            raise HTTPException(
                status_code=403, 
                detail="Solo administradores y analistas pueden sincronizar datos"
            )
        
        results = {
            "sync_started": datetime.now().isoformat(),
            "user_id": user.get('user_id'),
            "operations": []
        }
        
        # Sincronizar profesionales
        if sync_professionals:
            try:
                professionals = reservo_client.get_professionals()
                results["operations"].append({
                    "type": "professionals",
                    "status": "success",
                    "records_count": len(professionals),
                    "message": f"✅ {len(professionals)} profesionales sincronizados"
                })
            except Exception as e:
                results["operations"].append({
                    "type": "professionals",
                    "status": "error",
                    "error": str(e),
                    "message": f"❌ Error sincronizando profesionales: {str(e)}"
                })
        
        # Sincronizar citas
        if sync_appointments:
            try:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                
                appointments = reservo_client.get_appointments(start_date, end_date)
                results["operations"].append({
                    "type": "appointments",
                    "status": "success",
                    "records_count": len(appointments),
                    "date_range": {"start": start_date, "end": end_date},
                    "message": f"✅ {len(appointments)} citas sincronizadas"
                })
            except Exception as e:
                results["operations"].append({
                    "type": "appointments",
                    "status": "error",
                    "error": str(e),
                    "message": f"❌ Error sincronizando citas: {str(e)}"
                })
        
        # Determinar estado general
        successful_ops = sum(1 for op in results["operations"] if op["status"] == "success")
        total_ops = len(results["operations"])
        
        results["summary"] = {
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "failed_operations": total_ops - successful_ops,
            "success_rate": (successful_ops / total_ops * 100) if total_ops > 0 else 0,
            "overall_status": "success" if successful_ops == total_ops else "partial" if successful_ops > 0 else "failed"
        }
        
        results["sync_completed"] = datetime.now().isoformat()
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en sincronización: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_reservo_config(user: dict = Depends(get_current_user)):
    """Obtiene configuración actual de Reservo API"""
    try:
        # Solo administradores pueden ver configuración completa
        user_role = user.get('role', 'viewer')
        
        if user_role == 'admin':
            config = {
                "api_url": reservo_client.api_url,
                "api_key_configured": reservo_client.api_key is not None,
                "api_key_preview": f"{reservo_client.api_key[:10]}..." if reservo_client.api_key else None,
                "endpoints_available": [
                    "/professionals",
                    "/appointments", 
                    "/test",
                    "/statistics"
                ]
            }
        else:
            config = {
                "api_url": reservo_client.api_url,
                "api_key_configured": reservo_client.api_key is not None,
                "access_level": user_role,
                "message": "Configuración completa solo disponible para administradores"
            }
        
        return config
        
    except Exception as e:
        logger.error(f"Error obteniendo configuración: {e}")
        raise HTTPException(status_code=500, detail=str(e))