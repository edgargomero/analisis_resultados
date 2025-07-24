"""
CEAPSI Backend - File Validation
Validación segura de archivos subidos
"""

import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, UploadFile
import magic
from pathlib import Path

logger = logging.getLogger('CEAPSI_FILE_VALIDATION')

class FileValidator:
    """Validador de archivos con verificaciones de seguridad"""
    
    # Configuración de seguridad
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MIN_FILE_SIZE = 100  # 100 bytes mínimo
    
    # Extensiones permitidas
    ALLOWED_EXTENSIONS = {
        '.csv': 'text/csv',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel'
    }
    
    # Magic numbers para verificación de contenido real
    MAGIC_NUMBERS = {
        'csv': [b'\xef\xbb\xbf', b''],  # UTF-8 BOM o inicio directo
        'xlsx': [b'PK\x03\x04'],  # ZIP header (XLSX es un ZIP)
        'xls': [b'\xd0\xcf\x11\xe0', b'\x09\x08']  # OLE2 header o BOF
    }
    
    # Nombres de archivo peligrosos
    DANGEROUS_NAMES = [
        'con', 'prn', 'aux', 'nul',
        'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
        'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
    ]
    
    def __init__(self):
        self.reset_stats()
    
    def reset_stats(self):
        """Resetear estadísticas de validación"""
        self.validation_stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'rejected_files': 0,
            'security_violations': 0
        }
    
    async def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Validar archivo subido con múltiples verificaciones de seguridad
        
        Returns:
            Dict con información de validación y metadata del archivo
        """
        self.validation_stats['total_validations'] += 1
        
        try:
            # 1. Validar nombre de archivo
            await self._validate_filename(file.filename)
            
            # 2. Leer contenido del archivo
            content = await file.read()
            await file.seek(0)  # Resetear puntero para uso posterior
            
            # 3. Validar tamaño
            self._validate_file_size(len(content), file.filename)
            
            # 4. Validar extensión
            file_ext = self._get_file_extension(file.filename)
            
            # 5. Validar tipo MIME real vs extensión
            await self._validate_mime_type(content, file_ext, file.filename)
            
            # 6. Validaciones específicas por tipo
            await self._validate_file_content(content, file_ext, file.filename)
            
            # 7. Scan de contenido malicioso
            self._scan_malicious_content(content, file.filename)
            
            # Estadísticas de éxito
            self.validation_stats['successful_validations'] += 1
            
            # Metadata del archivo
            file_info = {
                'filename': file.filename,
                'size': len(content),
                'extension': file_ext,
                'mime_type': self.ALLOWED_EXTENSIONS[file_ext],
                'validation_passed': True,
                'security_checks': {
                    'filename_safe': True,
                    'size_valid': True,
                    'mime_verified': True,
                    'content_safe': True,
                    'no_malicious_patterns': True
                }
            }
            
            logger.info(f"✅ Archivo validado exitosamente: {file.filename} ({len(content)} bytes)")
            return file_info
            
        except HTTPException:
            self.validation_stats['rejected_files'] += 1
            raise
        except Exception as e:
            self.validation_stats['rejected_files'] += 1
            logger.error(f"Error inesperado validando archivo {file.filename}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error interno validando archivo"
            )
    
    async def _validate_filename(self, filename: str):
        """Validar nombre de archivo por seguridad"""
        if not filename:
            raise HTTPException(
                status_code=400,
                detail="Nombre de archivo requerido"
            )
        
        # Verificar longitud
        if len(filename) > 255:
            raise HTTPException(
                status_code=400,
                detail="Nombre de archivo demasiado largo (máximo 255 caracteres)"
            )
        
        # Verificar caracteres peligrosos
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0']
        for char in dangerous_chars:
            if char in filename:
                raise HTTPException(
                    status_code=400,
                    detail=f"Carácter no permitido en nombre de archivo: {char}"
                )
        
        # Verificar nombres de archivos peligrosos (Windows)
        base_name = Path(filename).stem.lower()
        if base_name in self.DANGEROUS_NAMES:
            raise HTTPException(
                status_code=400,
                detail=f"Nombre de archivo reservado no permitido: {filename}"
            )
        
        # Verificar que no empiece con punto (archivos ocultos)
        if filename.startswith('.'):
            raise HTTPException(
                status_code=400,
                detail="Archivos ocultos no permitidos"
            )
    
    def _validate_file_size(self, size: int, filename: str):
        """Validar tamaño de archivo"""
        if size < self.MIN_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Archivo demasiado pequeño (mínimo {self.MIN_FILE_SIZE} bytes)"
            )
        
        if size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo demasiado grande (máximo {self.MAX_FILE_SIZE // 1024 // 1024}MB)"
            )
    
    def _get_file_extension(self, filename: str) -> str:
        """Obtener y validar extensión de archivo"""
        file_ext = Path(filename).suffix.lower()
        
        if not file_ext:
            raise HTTPException(
                status_code=400,
                detail="Archivo debe tener extensión"
            )
        
        if file_ext not in self.ALLOWED_EXTENSIONS:
            allowed = ', '.join(self.ALLOWED_EXTENSIONS.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no permitido. Permitidos: {allowed}"
            )
        
        return file_ext
    
    async def _validate_mime_type(self, content: bytes, file_ext: str, filename: str):
        """Validar tipo MIME real vs extensión declarada"""
        try:
            # Usar python-magic para detectar tipo real
            mime_type = magic.from_buffer(content, mime=True)
            expected_mime = self.ALLOWED_EXTENSIONS[file_ext]
            
            # Verificar que coincida con lo esperado
            if file_ext == '.csv':
                # CSV puede ser detectado como text/plain o text/csv
                if mime_type not in ['text/csv', 'text/plain', 'application/csv']:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Archivo {filename} no es un CSV válido (tipo detectado: {mime_type})"
                    )
            elif file_ext == '.xlsx':
                # XLSX es un ZIP
                if mime_type not in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/zip']:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Archivo {filename} no es un XLSX válido (tipo detectado: {mime_type})"
                    )
            elif file_ext == '.xls':
                # XLS es OLE2
                if 'microsoft' not in mime_type.lower() and 'excel' not in mime_type.lower():
                    raise HTTPException(
                        status_code=400,
                        detail=f"Archivo {filename} no es un XLS válido (tipo detectado: {mime_type})"
                    )
                        
        except ImportError:
            # Si python-magic no está disponible, usar verificación básica
            logger.warning("python-magic no disponible, usando validación básica de headers")
            await self._validate_basic_headers(content, file_ext, filename)
    
    async def _validate_basic_headers(self, content: bytes, file_ext: str, filename: str):
        """Validación básica de headers sin python-magic"""
        if file_ext == '.xlsx':
            # XLSX debe empezar como ZIP
            if not content.startswith(b'PK'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Archivo {filename} no tiene header de XLSX válido"
                )
        elif file_ext == '.xls':
            # XLS debe empezar con header OLE2
            ole_headers = [b'\xd0\xcf\x11\xe0', b'\x09\x08']
            if not any(content.startswith(header) for header in ole_headers):
                raise HTTPException(
                    status_code=400,
                    detail=f"Archivo {filename} no tiene header de XLS válido"
                )
    
    async def _validate_file_content(self, content: bytes, file_ext: str, filename: str):
        """Validaciones específicas por tipo de archivo"""
        if file_ext == '.csv':
            await self._validate_csv_content(content, filename)
        elif file_ext in ['.xlsx', '.xls']:
            await self._validate_excel_content(content, filename)
    
    async def _validate_csv_content(self, content: bytes, filename: str):
        """Validar contenido CSV específico"""
        try:
            # Intentar decodificar como UTF-8
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # Intentar con latin-1 como fallback
                text_content = content.decode('latin-1')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail=f"No se puede decodificar el archivo CSV {filename}"
                )
        
        # Verificar que tenga al menos una línea con separadores
        lines = text_content.split('\n')
        if len(lines) < 2:
            raise HTTPException(
                status_code=400,
                detail=f"Archivo CSV {filename} debe tener al menos 2 líneas (header + datos)"
            )
        
        # Verificar separadores comunes
        common_separators = [';', ',', '\t']
        header = lines[0]
        has_separator = any(sep in header for sep in common_separators)
        
        if not has_separator:
            raise HTTPException(
                status_code=400,
                detail=f"Archivo CSV {filename} no tiene separadores válidos (;, ,, o tab)"
            )
    
    async def _validate_excel_content(self, content: bytes, filename: str):
        """Validar contenido Excel básico"""
        # Verificar que no esté corrupto (tamaño mínimo)
        if len(content) < 1000:  # Excel files suelen ser > 1KB
            raise HTTPException(
                status_code=400,
                detail=f"Archivo Excel {filename} parece estar corrupto (muy pequeño)"
            )
    
    def _scan_malicious_content(self, content: bytes, filename: str):
        """Scan básico de contenido malicioso"""
        # Patrones de contenido sospechoso
        malicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'onload=',
            b'onerror=',
            b'eval(',
            b'exec(',
            b'system(',
            b'shell_exec',
            b'<?php',
            b'<%',
            b'SELECT * FROM',
            b'DROP TABLE',
            b'DELETE FROM',
            b'INSERT INTO',
            b'UPDATE SET'
        ]
        
        content_lower = content.lower()
        for pattern in malicious_patterns:
            if pattern in content_lower:
                self.validation_stats['security_violations'] += 1
                logger.warning(f"🚨 Patrón sospechoso detectado en {filename}: {pattern}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Contenido potencialmente malicioso detectado en archivo {filename}"
                )
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de validación"""
        return {
            **self.validation_stats,
            'success_rate': (
                self.validation_stats['successful_validations'] / 
                max(self.validation_stats['total_validations'], 1) * 100
            )
        }

# Instancia global del validador
file_validator = FileValidator()

async def validate_uploaded_file(file: UploadFile) -> Dict[str, Any]:
    """
    Función helper para validar archivos subidos
    
    Args:
        file: Archivo subido por FastAPI
        
    Returns:
        Dict con metadata del archivo validado
        
    Raises:
        HTTPException: Si la validación falla
    """
    return await file_validator.validate_file(file)