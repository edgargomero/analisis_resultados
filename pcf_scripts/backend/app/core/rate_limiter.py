"""
CEAPSI Backend - Rate Limiter
Sistema de rate limiting para proteger endpoints contra abuso
"""

import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
import asyncio
import threading

logger = logging.getLogger('CEAPSI_RATE_LIMITER')

class RateLimiter:
    """Rate limiter con múltiples estrategias de limitación"""
    
    def __init__(self):
        self.requests = defaultdict(deque)  # IP -> deque of timestamps
        self.user_requests = defaultdict(deque)  # user_id -> deque of timestamps
        self.global_requests = deque()  # Global request tracking
        self.blocked_ips = {}  # IP -> expiry time
        self.lock = threading.RLock()
        
        # Configuración de límites
        self.limits = {
            # Límites por IP
            'per_ip': {
                'requests_per_minute': 60,
                'requests_per_hour': 300,
                'burst_limit': 10,  # Máximo en 10 segundos
                'burst_window': 10
            },
            
            # Límites por usuario autenticado
            'per_user': {
                'requests_per_minute': 100,
                'requests_per_hour': 500,
                'upload_per_hour': 10,
                'analysis_per_hour': 20
            },
            
            # Límites globales
            'global': {
                'requests_per_minute': 1000,
                'requests_per_hour': 5000
            },
            
            # Límites por endpoint específico
            'endpoints': {
                '/api/v1/data/upload': {
                    'requests_per_hour': 10,
                    'requests_per_minute': 2
                },
                '/api/v1/analysis/start': {
                    'requests_per_hour': 20,
                    'requests_per_minute': 5
                },
                '/api/v1/reservo/sync-data': {
                    'requests_per_hour': 5,
                    'requests_per_minute': 1
                }
            }
        }
        
        # Configuración de bloqueo
        self.block_config = {
            'threshold_violations': 3,  # Violaciones antes de bloquear
            'block_duration_minutes': 15,  # Duración del bloqueo
            'escalation_factor': 2  # Factor de escalación para bloqueos repetidos
        }
        
        self.violations = defaultdict(int)  # IP -> violation count
        
        # Limpiar caches cada 5 minutos
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Iniciar tarea de limpieza en background"""
        def cleanup_loop():
            while True:
                try:
                    self._cleanup_old_requests()
                    time.sleep(300)  # 5 minutos
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_requests(self):
        """Limpiar requests antiguos para liberar memoria"""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - 3600  # 1 hora atrás
            
            # Limpiar requests por IP
            for ip in list(self.requests.keys()):
                while self.requests[ip] and self.requests[ip][0] < cutoff_time:
                    self.requests[ip].popleft()
                
                if not self.requests[ip]:
                    del self.requests[ip]
            
            # Limpiar requests por usuario
            for user_id in list(self.user_requests.keys()):
                while self.user_requests[user_id] and self.user_requests[user_id][0] < cutoff_time:
                    self.user_requests[user_id].popleft()
                
                if not self.user_requests[user_id]:
                    del self.user_requests[user_id]
            
            # Limpiar requests globales
            while self.global_requests and self.global_requests[0] < cutoff_time:
                self.global_requests.popleft()
            
            # Limpiar IPs bloqueadas expiradas
            expired_blocks = [
                ip for ip, expiry in self.blocked_ips.items() 
                if current_time > expiry
            ]
            for ip in expired_blocks:
                del self.blocked_ips[ip]
                if ip in self.violations:
                    # Reducir violaciones gradualmente
                    self.violations[ip] = max(0, self.violations[ip] - 1)
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP real del cliente considerando proxies"""
        # Verificar headers de proxy comunes
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Tomar la primera IP (cliente original)
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback a client IP directo
        return request.client.host if request.client else "unknown"
    
    def _count_requests_in_window(self, requests_deque: deque, window_seconds: int) -> int:
        """Contar requests en ventana de tiempo"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        # Remover requests antiguos
        while requests_deque and requests_deque[0] < cutoff_time:
            requests_deque.popleft()
        
        return len(requests_deque)
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Verificar si IP está bloqueada"""
        if ip in self.blocked_ips:
            if time.time() < self.blocked_ips[ip]:
                return True
            else:
                # Expiró el bloqueo
                del self.blocked_ips[ip]
        return False
    
    def _block_ip(self, ip: str, reason: str):
        """Bloquear IP por violaciones repetidas"""
        violation_count = self.violations[ip]
        
        # Duración del bloqueo con escalación
        base_duration = self.block_config['block_duration_minutes']
        escalated_duration = base_duration * (self.block_config['escalation_factor'] ** min(violation_count, 5))
        
        block_until = time.time() + (escalated_duration * 60)
        self.blocked_ips[ip] = block_until
        
        logger.warning(
            f"🚨 IP bloqueada: {ip} por {escalated_duration} minutos. "
            f"Razón: {reason}. Violaciones: {violation_count}"
        )
    
    async def check_rate_limit(
        self, 
        request: Request, 
        endpoint: str = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Verificar límites de rate limiting
        
        Returns:
            Dict con información del rate limiting
            
        Raises:
            HTTPException: Si se exceden los límites
        """
        with self.lock:
            current_time = time.time()
            client_ip = self._get_client_ip(request)
            
            # 1. Verificar si IP está bloqueada
            if self._is_ip_blocked(client_ip):
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "IP temporalmente bloqueada por exceso de requests",
                        "blocked_until": datetime.fromtimestamp(self.blocked_ips[client_ip]).isoformat(),
                        "type": "ip_blocked"
                    }
                )
            
            # 2. Verificar límites globales
            self.global_requests.append(current_time)
            global_minute = self._count_requests_in_window(self.global_requests, 60)
            global_hour = self._count_requests_in_window(self.global_requests, 3600)
            
            if global_minute > self.limits['global']['requests_per_minute']:
                logger.warning(f"🚨 Límite global por minuto excedido: {global_minute}")
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "Servicio temporalmente sobrecargado, intente más tarde",
                        "type": "global_limit_exceeded",
                        "retry_after": 60
                    }
                )
            
            # 3. Verificar límites por IP
            self.requests[client_ip].append(current_time)
            
            ip_minute = self._count_requests_in_window(self.requests[client_ip], 60)
            ip_hour = self._count_requests_in_window(self.requests[client_ip], 3600)
            ip_burst = self._count_requests_in_window(self.requests[client_ip], self.limits['per_ip']['burst_window'])
            
            # Verificar burst limit
            if ip_burst > self.limits['per_ip']['burst_limit']:
                self.violations[client_ip] += 1
                
                if self.violations[client_ip] >= self.block_config['threshold_violations']:
                    self._block_ip(client_ip, f"Burst limit exceeded: {ip_burst} requests")
                
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": f"Demasiadas requests en poco tiempo ({ip_burst} en {self.limits['per_ip']['burst_window']}s)",
                        "type": "burst_limit_exceeded",
                        "retry_after": self.limits['per_ip']['burst_window']
                    }
                )
            
            # Verificar límites por minuto/hora
            if ip_minute > self.limits['per_ip']['requests_per_minute']:
                self.violations[client_ip] += 1
                
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": f"Límite de requests por minuto excedido ({ip_minute}/min)",
                        "type": "rate_limit_exceeded",
                        "retry_after": 60
                    }
                )
            
            if ip_hour > self.limits['per_ip']['requests_per_hour']:
                self.violations[client_ip] += 1
                
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": f"Límite de requests por hora excedido ({ip_hour}/hour)",
                        "type": "rate_limit_exceeded", 
                        "retry_after": 3600
                    }
                )
            
            # 4. Verificar límites por usuario (si está autenticado)
            if user_id:
                self.user_requests[user_id].append(current_time)
                
                user_minute = self._count_requests_in_window(self.user_requests[user_id], 60)
                user_hour = self._count_requests_in_window(self.user_requests[user_id], 3600)
                
                if user_minute > self.limits['per_user']['requests_per_minute']:
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "error": f"Límite de usuario por minuto excedido ({user_minute}/min)",
                            "type": "user_limit_exceeded",
                            "retry_after": 60
                        }
                    )
                
                if user_hour > self.limits['per_user']['requests_per_hour']:
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "error": f"Límite de usuario por hora excedido ({user_hour}/hour)",
                            "type": "user_limit_exceeded",
                            "retry_after": 3600
                        }
                    )
            
            # 5. Verificar límites por endpoint específico
            if endpoint and endpoint in self.limits['endpoints']:
                endpoint_limits = self.limits['endpoints'][endpoint]
                endpoint_key = f"{client_ip}:{endpoint}"
                
                if endpoint_key not in self.requests:
                    self.requests[endpoint_key] = deque()
                
                self.requests[endpoint_key].append(current_time)
                
                endpoint_minute = self._count_requests_in_window(self.requests[endpoint_key], 60)
                endpoint_hour = self._count_requests_in_window(self.requests[endpoint_key], 3600)
                
                if endpoint_minute > endpoint_limits.get('requests_per_minute', 999):
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "error": f"Límite específico del endpoint excedido ({endpoint_minute}/min)",
                            "endpoint": endpoint,
                            "type": "endpoint_limit_exceeded",
                            "retry_after": 60
                        }
                    )
                
                if endpoint_hour > endpoint_limits.get('requests_per_hour', 9999):
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "error": f"Límite específico del endpoint excedido ({endpoint_hour}/hour)",
                            "endpoint": endpoint,
                            "type": "endpoint_limit_exceeded",
                            "retry_after": 3600
                        }
                    )
            
            # Si llegamos aquí, la request está permitida
            return {
                "allowed": True,
                "client_ip": client_ip,
                "user_id": user_id,
                "endpoint": endpoint,
                "current_usage": {
                    "ip_minute": ip_minute,
                    "ip_hour": ip_hour,
                    "user_minute": user_minute if user_id else 0,
                    "user_hour": user_hour if user_id else 0,
                    "global_minute": global_minute
                },
                "limits": {
                    "ip_minute_limit": self.limits['per_ip']['requests_per_minute'],
                    "ip_hour_limit": self.limits['per_ip']['requests_per_hour'],
                    "user_minute_limit": self.limits['per_user']['requests_per_minute'],
                    "user_hour_limit": self.limits['per_user']['requests_per_hour']
                }
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del rate limiter"""
        with self.lock:
            return {
                "active_ips": len(self.requests),
                "active_users": len(self.user_requests),
                "blocked_ips": len(self.blocked_ips),
                "total_violations": sum(self.violations.values()),
                "global_requests_last_hour": len(self.global_requests),
                "blocked_ips_list": [
                    {
                        "ip": ip,
                        "blocked_until": datetime.fromtimestamp(expiry).isoformat(),
                        "violations": self.violations.get(ip, 0)
                    }
                    for ip, expiry in self.blocked_ips.items()
                ],
                "top_violators": [
                    {"ip": ip, "violations": count}
                    for ip, count in sorted(self.violations.items(), key=lambda x: x[1], reverse=True)[:10]
                ]
            }

# Instancia global del rate limiter
rate_limiter = RateLimiter()

async def apply_rate_limit(
    request: Request,
    endpoint: str = None,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Aplicar rate limiting a una request
    
    Args:
        request: Request de FastAPI
        endpoint: Endpoint específico (opcional)
        user_id: ID del usuario autenticado (opcional)
        
    Returns:
        Dict con información del rate limiting
        
    Raises:
        HTTPException: Si se exceden los límites
    """
    return await rate_limiter.check_rate_limit(request, endpoint, user_id)