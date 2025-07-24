"""
CEAPSI Backend Pydantic Models
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class AnalysisType(str, Enum):
    """Types of analysis"""
    CALL_CENTER_ANALYSIS = "call_center_analysis"
    CALL_PREDICTION = "call_prediction"
    DATA_AUDIT = "data_audit"

class SessionStatus(str, Enum):
    """Session status options"""
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class FileInfo(BaseModel):
    """File information model"""
    filename: str
    size: int
    type: str
    records_count: int
    columns: List[str]
    temp_path: Optional[str] = None

class SessionCreate(BaseModel):
    """Session creation model"""
    user_id: str
    analysis_type: AnalysisType = AnalysisType.CALL_CENTER_ANALYSIS
    file_info: FileInfo

class SessionResponse(BaseModel):
    """Session response model"""
    session_id: str
    user_id: str
    analysis_type: str
    status: SessionStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: datetime
    file_info: Dict[str, Any]
    results_summary: Optional[Dict[str, Any]] = None

class DataUploadResponse(BaseModel):
    """Data upload response"""
    success: bool
    message: str
    file_info: Optional[FileInfo] = None
    session_id: Optional[str] = None

class AnalysisRequest(BaseModel):
    """Analysis request model"""
    session_id: str
    analysis_config: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    """Analysis response model"""
    success: bool
    message: str
    session_id: str
    results: Optional[Dict[str, Any]] = None

class PredictionRequest(BaseModel):
    """Prediction request model"""
    session_id: str
    prediction_days: int = Field(default=28, ge=1, le=90)
    models: List[str] = Field(default=["arima", "prophet", "random_forest", "gradient_boosting"])

class PredictionResponse(BaseModel):
    """Prediction response model"""
    success: bool
    session_id: str
    predictions: Dict[str, Any]
    metrics: Dict[str, float]
    prediction_period: Dict[str, str]

class ModelMetrics(BaseModel):
    """Model performance metrics"""
    mae: float
    rmse: float
    mape: float
    r2_score: Optional[float] = None

class ModelInfo(BaseModel):
    """Model information"""
    name: str
    type: str
    metrics: ModelMetrics
    trained_at: datetime
    features_used: List[str]

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    services: Dict[str, bool]

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    timestamp: datetime
    details: Optional[str] = None

class UserCreate(BaseModel):
    """User creation model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=100)

class UserLogin(BaseModel):
    """User login model"""
    username: str
    password: str

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class DataValidationResult(BaseModel):
    """Data validation result"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    statistics: Dict[str, Any] = {}

class ProcessingStatus(BaseModel):
    """Processing status model"""
    step: str
    progress: float = Field(ge=0, le=100)
    message: str
    estimated_time_remaining: Optional[int] = None  # seconds

class SessionList(BaseModel):
    """Session list response"""
    sessions: List[SessionResponse]
    total_count: int
    page: int
    page_size: int