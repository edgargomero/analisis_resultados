"""
CEAPSI Backend - Sessions Router
Endpoints for session management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any
import sys
from pathlib import Path
import logging

# Add src directory to path
current_dir = Path(__file__).parent.parent.parent.parent.absolute()
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from models.schemas import SessionResponse, SessionList
from core.auth import get_current_user
from core.mcp_session_manager import get_mcp_session_manager

logger = logging.getLogger('CEAPSI_SESSIONS')
router = APIRouter()

@router.get("/", response_model=SessionList)
async def list_user_sessions(
    user_id: str = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: str = Query(None, description="Filter by status")
):
    """List user sessions with pagination"""
    
    try:
        session_manager = get_mcp_session_manager()
        sessions = session_manager.list_user_sessions(user_id, page_size * page)
        
        # Filter by status if provided
        if status:
            sessions = [s for s in sessions if s.get('status') == status]
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_sessions = sessions[start_idx:end_idx]
        
        return SessionList(
            sessions=paginated_sessions,
            total_count=len(sessions),
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get session details"""
    
    try:
        session_manager = get_mcp_session_manager()
        session_data = session_manager.load_analysis_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        # Verify user owns this session
        if session_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        return session_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/results")
async def get_session_results(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get session analysis results"""
    
    try:
        session_manager = get_mcp_session_manager()
        session_data = session_manager.load_analysis_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        # Verify user owns this session
        if session_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        results = session_data.get('analysis_results', {})
        
        if not results:
            raise HTTPException(status_code=404, detail="Resultados no disponibles")
        
        return {
            "session_id": session_id,
            "status": session_data.get('status'),
            "results": results,
            "summary": session_data.get('results_summary', {}),
            "completed_at": session_data.get('completed_at')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a session"""
    
    try:
        session_manager = get_mcp_session_manager()
        session_data = session_manager.load_analysis_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        # Verify user owns this session
        if session_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        success = session_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Error eliminando sesión")
        
        return {"message": "Sesión eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/restore")
async def restore_session(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """Restore session to current context"""
    
    try:
        session_manager = get_mcp_session_manager()
        session_data = session_manager.load_analysis_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        # Verify user owns this session
        if session_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        return {
            "message": "Sesión restaurada exitosamente",
            "session_data": session_data,
            "has_results": bool(session_data.get('analysis_results'))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring session: {e}")
        raise HTTPException(status_code=500, detail=str(e))