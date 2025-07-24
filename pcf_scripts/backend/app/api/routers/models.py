"""
CEAPSI Backend - Models Router
Endpoints for ML model management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import sys
from pathlib import Path
import logging

# Add src directory to path
current_dir = Path(__file__).parent.parent.parent.parent.absolute()
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from models.schemas import ModelInfo
from core.auth import get_current_user

logger = logging.getLogger('CEAPSI_MODELS')
router = APIRouter()

@router.get("/available")
async def get_available_models():
    """Get list of available ML models"""
    
    return {
        "models": [
            {
                "name": "arima",
                "display_name": "ARIMA",
                "description": "Autoregressive Integrated Moving Average",
                "type": "time_series",
                "suitable_for": ["trending", "seasonal_data"]
            },
            {
                "name": "prophet",
                "display_name": "Prophet",
                "description": "Facebook Prophet forecasting model",
                "type": "time_series",
                "suitable_for": ["seasonal_patterns", "holidays"]
            },
            {
                "name": "random_forest",
                "display_name": "Random Forest",
                "description": "Random Forest Regressor",
                "type": "machine_learning",
                "suitable_for": ["feature_rich_data", "non_linear_patterns"]
            },
            {
                "name": "gradient_boosting",
                "display_name": "Gradient Boosting",
                "description": "Gradient Boosting Regressor",
                "type": "machine_learning",
                "suitable_for": ["complex_patterns", "high_accuracy"]
            }
        ]
    }

@router.get("/performance/{session_id}")
async def get_model_performance(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get model performance metrics for a session"""
    
    try:
        # This would integrate with session results to get actual metrics
        return {
            "session_id": session_id,
            "metrics": {},
            "message": "Model performance functionality coming soon"
        }
        
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comparison/{session_id}")
async def compare_models(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """Compare model performance for a session"""
    
    try:
        # This would integrate with session results to compare models
        return {
            "session_id": session_id,
            "comparison": {},
            "message": "Model comparison functionality coming soon"
        }
        
    except Exception as e:
        logger.error(f"Error comparing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))