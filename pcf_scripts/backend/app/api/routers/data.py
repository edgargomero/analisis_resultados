"""
CEAPSI Backend - Data Upload Router
Endpoints para subida y procesamiento de datos con validación de seguridad
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any
import tempfile
import pandas as pd
from datetime import datetime
import uuid
import os

from core.supabase_auth import get_current_user
from core.file_validation import validate_uploaded_file, file_validator

logger = logging.getLogger('CEAPSI_DATA_UPLOAD')
router = APIRouter()

@router.post("/upload")
async def upload_data_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload and process data file with security validation"""
    try:
        logger.info(f"File upload started by user {user.get('user_id')}: {file.filename}")
        
        # STEP 1: Validación de seguridad completa
        file_info = await validate_uploaded_file(file)
        logger.info(f"✅ File validation passed for {file.filename}")
        
        # STEP 2: Verificar permisos de usuario
        user_role = user.get('role', 'viewer')
        if user_role == 'viewer':
            raise HTTPException(
                status_code=403,
                detail="Los usuarios con rol 'viewer' no pueden subir archivos"
            )
        
        # STEP 3: Leer contenido del archivo (ya validado)
        content = await file.read()
        await file.seek(0)  # Reset
        
        # STEP 4: Guardar en archivo temporal seguro
        temp_dir = tempfile.gettempdir()
        safe_filename = f"ceapsi_{uuid.uuid4().hex}_{file.filename}"
        temp_path = os.path.join(temp_dir, safe_filename)
        
        with open(temp_path, 'wb') as tmp_file:
            tmp_file.write(content)
        
        # Establecer permisos restrictivos
        os.chmod(temp_path, 0o600)
        
        # STEP 5: Crear sesión para tracking
        session_id = str(uuid.uuid4())
        
        # STEP 6: Procesar archivo en background
        background_tasks.add_task(
            process_uploaded_file, 
            temp_path, 
            session_id, 
            user, 
            file_info
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "file_info": {
                "filename": file.filename,
                "size": file_info['size'],
                "extension": file_info['extension'],
                "mime_type": file_info['mime_type']
            },
            "user_id": user.get('user_id'),
            "message": "Archivo subido y validado exitosamente, procesamiento iniciado",
            "security_checks_passed": file_info['security_checks']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in file upload: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno procesando archivo"
        )

async def process_uploaded_file(
    file_path: str, 
    session_id: str, 
    user: dict, 
    file_info: dict
):
    """Process uploaded file in background with enhanced security"""
    try:
        logger.info(f"Processing file for session {session_id}")
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            logger.error(f"Temp file not found for session {session_id}")
            return
        
        # Cargar datos según el tipo
        try:
            if file_info['extension'] == '.csv':
                encodings = ['utf-8', 'latin-1', 'cp1252']
                df = None
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, sep=';', encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if df is None:
                    raise ValueError("No se pudo decodificar el archivo CSV")
                    
            elif file_info['extension'] in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Tipo de archivo no soportado: {file_info['extension']}")
                
        except Exception as e:
            logger.error(f"Error loading data for session {session_id}: {e}")
            return
        
        # Validación de estructura
        validation_errors = []
        required_columns = ['FECHA', 'TELEFONO']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            validation_errors.append(f"Columnas faltantes: {missing_columns}")
        
        if len(df) == 0:
            validation_errors.append("El archivo no contiene datos")
        
        if validation_errors:
            logger.error(f"Data validation errors for session {session_id}: {validation_errors}")
            return
        
        # Limpiar datos
        original_count = len(df)
        df = df.dropna(how='all').drop_duplicates()
        cleaned_count = len(df)
        
        logger.info(f"✅ File processed successfully for session {session_id}: {cleaned_count} records")
        
    except Exception as e:
        logger.error(f"Error processing file for session {session_id}: {e}")
    
    finally:
        # Limpiar archivo temporal de forma segura
        try:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                with open(file_path, 'wb') as f:
                    f.write(b'\0' * file_size)
                os.remove(file_path)
                logger.info(f"Temp file securely deleted for session {session_id}")
        except Exception as e:
            logger.error(f"Error deleting temp file for session {session_id}: {e}")

@router.get("/sessions/{session_id}/status")
async def get_processing_status(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    """Get file processing status"""
    try:
        return {
            "session_id": session_id,
            "status": "processing",
            "message": "Archivo siendo procesado",
            "user_id": user.get('user_id'),
            "estimated_completion": "2-5 minutos",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting status for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo estado de sesión"
        )

@router.get("/validation-stats")
async def get_validation_statistics(
    user: dict = Depends(get_current_user)
):
    """Get file validation statistics (admin only)"""
    try:
        if user.get('role') != 'admin':
            raise HTTPException(
                status_code=403,
                detail="Solo administradores pueden ver estadísticas de validación"
            )
        
        stats = file_validator.get_validation_stats()
        
        return {
            "validation_statistics": stats,
            "timestamp": datetime.now().isoformat(),
            "requested_by": user.get('user_id')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting validation stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo estadísticas"
        )