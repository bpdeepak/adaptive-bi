from app.database import get_database
from app.models.model_manager import ModelManager
from typing import Any
from fastapi import HTTPException, status
from app.utils.logger import logger

def get_db() -> Any:
    """
    Dependency to get the MongoDB database instance.
    """
    db = get_database()
    if db is None:
        logger.error("Database connection not available.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database connection not available")
    return db

def get_model_manager() -> ModelManager:
    """
    Dependency to get the singleton ModelManager instance.
    Ensures models are ready before serving requests.
    """
    manager = ModelManager()
    if not manager.models_loaded:
        logger.warning("AI models are not fully loaded or trained yet.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI models are not ready. Please try again shortly or trigger training.")
    return manager