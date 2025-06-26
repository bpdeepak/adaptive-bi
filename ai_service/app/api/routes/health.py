from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database
from app.models.model_manager import ModelManager
from app.utils.logger import logger
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.dependencies import get_db, get_model_manager
from datetime import datetime

router = APIRouter()

@router.get("/", summary="Basic health check")
async def health_check():
    """
    Returns a simple OK status to indicate the service is running.
    """
    return {"status": "ok", "message": "AI service is running"}

@router.get("/detailed", summary="Detailed health check including database and model status")
async def detailed_health_check(
    db: AsyncIOMotorDatabase = Depends(get_db),
    model_manager: ModelManager = Depends(get_model_manager) # Use dependency to ensure manager is ready
):
    """
    Provides a detailed health check, including MongoDB connection status and ML model readiness.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database_status": "disconnected",
        "models_status": {
            "forecasting_model": "not_loaded",
            "anomaly_detection_model": "not_loaded",
            "recommendation_model": "not_loaded"
        },
        "message": "All systems nominal"
    }

    # Check MongoDB connection
    try:
        await db.command('ping')
        health_status["database_status"] = "connected"
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        health_status["database_status"] = "failed"
        health_status["status"] = "unhealthy"
        health_status["message"] = "MongoDB connection failed"

    # Check model readiness (via model manager)
    if model_manager.forecasting_model and model_manager.forecasting_model.is_trained:
        health_status["models_status"]["forecasting_model"] = "trained"
    else:
        health_status["models_status"]["forecasting_model"] = "not_trained"
        health_status["status"] = "degraded"
        health_status["message"] = "Forecasting model not ready"

    if model_manager.anomaly_model and model_manager.anomaly_model.is_trained:
        health_status["models_status"]["anomaly_detection_model"] = "trained"
    else:
        health_status["models_status"]["anomaly_detection_model"] = "not_trained"
        health_status["status"] = "degraded"
        health_status["message"] = "Anomaly detection model not ready"

    if model_manager.recommendation_model and model_manager.recommendation_model.is_trained:
        health_status["models_status"]["recommendation_model"] = "trained"
    else:
        health_status["models_status"]["recommendation_model"] = "not_trained"
        health_status["status"] = "degraded"
        health_status["message"] = "Recommendation model not ready"
    
    if not model_manager.models_loaded:
        health_status["status"] = "degraded"
        health_status["message"] = "Not all AI models are loaded or trained."

    if health_status["status"] != "healthy":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=health_status)

    return health_status