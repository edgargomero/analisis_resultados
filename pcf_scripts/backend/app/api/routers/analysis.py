"""
CEAPSI Backend - Analysis Router
Endpoints for data analysis and model training
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from typing import Dict, Any
import pandas as pd
import tempfile
import os
import sys
from pathlib import Path
import logging

# Add src directory to path
current_dir = Path(__file__).parent.parent.parent.parent.absolute()
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from models.schemas import AnalysisRequest, AnalysisResponse, PredictionRequest, PredictionResponse
from core.auth import get_current_user
from core.mcp_session_manager import get_mcp_session_manager

# Import analysis modules
from services.auditoria_datos_llamadas import AuditoriaLlamadasAlodesk
from services.segmentacion_llamadas import SegmentadorLlamadas
from models.sistema_multi_modelo import SistemaMultiModeloCEAPSI

logger = logging.getLogger('CEAPSI_ANALYSIS')
router = APIRouter()

@router.post("/upload", response_model=Dict[str, Any])
async def upload_data(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """Upload and validate data file"""
    
    # Validate file type
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Tipo de archivo no soportado")
    
    try:
        # Save temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            temp_path = tmp_file.name
        
        # Read and validate data
        if file.filename.endswith('.csv'):
            df = pd.read_csv(temp_path, sep=';', encoding='utf-8')
        else:
            df = pd.read_excel(temp_path)
        
        # Validate required columns
        required_columns = ['FECHA', 'TELEFONO']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            os.unlink(temp_path)
            raise HTTPException(
                status_code=400, 
                detail=f"Columnas faltantes: {missing_columns}"
            )
        
        # Create session
        session_manager = get_mcp_session_manager()
        file_info = {
            'filename': file.filename,
            'size': len(content),
            'type': file.content_type,
            'records_count': len(df),
            'columns': list(df.columns),
            'temp_path': temp_path
        }
        
        session_id = session_manager.create_analysis_session(
            user_id, file_info, "call_center_analysis"
        )
        
        return {
            "success": True,
            "message": "Archivo cargado exitosamente",
            "session_id": session_id,
            "file_info": file_info,
            "preview": df.head().to_dict('records')
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")

@router.post("/audit", response_model=AnalysisResponse)
async def run_data_audit(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """Run data quality audit"""
    
    try:
        # Get session data
        session_manager = get_mcp_session_manager()
        session_data = session_manager.load_analysis_session(request.session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        # Run audit in background
        background_tasks.add_task(
            _run_audit_background, 
            request.session_id, 
            session_data['file_info']['temp_path']
        )
        
        return AnalysisResponse(
            success=True,
            message="Auditoría iniciada en segundo plano",
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error running audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/segment", response_model=AnalysisResponse)
async def run_call_segmentation(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """Run call segmentation analysis"""
    
    try:
        session_manager = get_mcp_session_manager()
        session_data = session_manager.load_analysis_session(request.session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        background_tasks.add_task(
            _run_segmentation_background,
            request.session_id,
            session_data['file_info']['temp_path']
        )
        
        return AnalysisResponse(
            success=True,
            message="Segmentación iniciada en segundo plano",
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error running segmentation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict", response_model=PredictionResponse)
async def generate_predictions(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """Generate call predictions using multi-model system"""
    
    try:
        session_manager = get_mcp_session_manager()
        session_data = session_manager.load_analysis_session(request.session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        background_tasks.add_task(
            _run_prediction_background,
            request.session_id,
            session_data['file_info']['temp_path'],
            request.prediction_days,
            request.models
        )
        
        return PredictionResponse(
            success=True,
            session_id=request.session_id,
            predictions={},
            metrics={},
            prediction_period={"start": "", "end": ""}
        )
        
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{session_id}")
async def get_analysis_status(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get analysis status for a session"""
    
    try:
        session_manager = get_mcp_session_manager()
        session_data = session_manager.load_analysis_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        return {
            "session_id": session_id,
            "status": session_data.get('status', 'created'),
            "results_available": bool(session_data.get('analysis_results')),
            "created_at": session_data.get('created_at'),
            "completed_at": session_data.get('completed_at'),
            "summary": session_data.get('results_summary', {})
        }
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def _run_audit_background(session_id: str, file_path: str):
    """Run audit analysis in background"""
    try:
        auditor = AuditoriaLlamadasAlodesk(file_path)
        if auditor.cargar_y_limpiar_datos():
            results = auditor.generar_reporte_diagnostico(".")
            
            # Save results
            session_manager = get_mcp_session_manager()
            session_manager.save_analysis_results(session_id, {"audit": results})
            
    except Exception as e:
        logger.error(f"Background audit failed: {e}")

async def _run_segmentation_background(session_id: str, file_path: str):
    """Run segmentation analysis in background"""
    try:
        segmentador = SegmentadorLlamadas()
        results = segmentador.procesar_datos_llamadas(file_path)
        
        # Save results
        session_manager = get_mcp_session_manager()
        session_manager.save_analysis_results(session_id, {"segmentation": results})
        
    except Exception as e:
        logger.error(f"Background segmentation failed: {e}")

async def _run_prediction_background(session_id: str, file_path: str, days: int, models: list):
    """Run prediction analysis in background"""
    try:
        # Load data and run multi-model system
        sistema = SistemaMultiModeloCEAPSI()
        
        # This would need to be adapted based on your specific model training logic
        # For now, just save a placeholder result
        results = {
            "predictions": {},
            "models_trained": models,
            "prediction_days": days
        }
        
        session_manager = get_mcp_session_manager()
        session_manager.save_analysis_results(session_id, {"predictions": results})
        
    except Exception as e:
        logger.error(f"Background prediction failed: {e}")