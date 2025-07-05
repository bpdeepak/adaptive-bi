import os
import uvicorn
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Import existing core modules
from app.config import settings # This refers to the app/config.py file for main settings
from app.database import close_mongo_connection, connect_to_mongo, get_database
from app.utils.logger import logger, log_memory_usage, force_memory_cleanup # Your custom logger with memory functions

# Import existing Phase 3 API routes
from app.api.routes import forecast, anomaly, recommend, health

# Import new Phase 4 API routes
from app.api.routes import advanced_endpoints

# Import existing Phase 3 Model Manager
from app.models.model_manager import model_manager, ModelManager

# Import new Phase 4 services for global initialization
# NOTE: The ModelConfig import here uses the *new* path 'app.model_configs'
from app.services.pricing_service import PricingService
from app.services.churn_service import ChurnService
from app.services.reasoning_service import ReasoningService
from app.services.feedback_service import FeedbackService

# APScheduler for periodic tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Global service instances (initialized once during app startup)
pricing_service_instance: Optional[PricingService] = None
churn_service_instance: Optional[ChurnService] = None
reasoning_service_instance: Optional[ReasoningService] = None
feedback_service_instance: Optional[FeedbackService] = None


# Define the periodic task function for retraining all models
async def periodic_model_retraining_all():
    logger.info("Starting scheduled intelligent model retraining (Phase 3 & 4 models)...")
    
    # Memory monitoring before retraining
    log_memory_usage("before scheduled retraining")
    
    try:
        # Check if there's enough new data to warrant retraining
        retrain_interval = getattr(settings, 'MODEL_RETRAIN_INTERVAL_MINUTES', 0)
        if not await should_retrain_models(retrain_interval):
            logger.info("Skipping retraining - insufficient new data or recent training.")
            return
            
        # Memory-safe sequential retraining (one model at a time)
        logger.info("Training Phase 3 models sequentially...")
        
        # Phase 3 Models via existing ModelManager (with memory monitoring)
        await model_manager.train_all_models()
        log_memory_usage("after Phase 3 model training")
        force_memory_cleanup()
        
        logger.info("Phase 3 models (Forecasting, Anomaly, Recommendation) retraining completed.")

        # Phase 4 Models via FeedbackService (sequential, not parallel)
        if feedback_service_instance:
            logger.info("Training Phase 4 models sequentially...")
            
            # Train one model at a time to conserve memory
            await feedback_service_instance.trigger_retraining('pricing', force_retrain=True)
            log_memory_usage("after pricing model training")
            force_memory_cleanup()
            
            await feedback_service_instance.trigger_retraining('churn', force_retrain=True)  
            log_memory_usage("after churn model training")
            force_memory_cleanup()
            
            await feedback_service_instance.trigger_retraining('knowledge_graph', force_retrain=True)
            log_memory_usage("after knowledge graph rebuild")
            force_memory_cleanup()
            
            logger.info("Phase 4 models retraining/rebuilding completed.")
        else:
            logger.warning("FeedbackService not initialized, skipping Phase 4 model retraining.")

        # Final memory cleanup
        log_memory_usage("after all model training")
        force_memory_cleanup()
        log_memory_usage("after final cleanup")
        
        logger.info("Scheduled intelligent model retraining completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during scheduled model retraining: {e}", exc_info=True)
        # Emergency memory cleanup on error
        force_memory_cleanup()


async def should_retrain_models(retrain_interval: int = 1440) -> bool:
    """
    Intelligent check to determine if models should be retrained.
    Returns True if retraining is needed, False otherwise.
    """
    try:
        # Check if we have enough new data since last training
        # This is a simplified check - could be enhanced with more sophisticated logic
        db = get_database()
        
        if db is None:
            logger.warning("Database not connected - defaulting to not retrain")
            return False
        
        # Only retrain if we have meaningful new data
        # Adjust thresholds based on retraining frequency
        if retrain_interval <= 30:  # For testing (every 30 minutes or less)
            min_transactions_for_retrain = 10   # Lower threshold for testing
            min_feedback_for_retrain = 2        # Lower threshold for testing
            time_window_hours = max(1, retrain_interval // 60)  # At least 1 hour window
        else:  # For production intervals
            min_transactions_for_retrain = 100  # Higher threshold for production
            min_feedback_for_retrain = 10       # Higher threshold for production
            time_window_hours = 24               # 24 hour window
            
        # Get recent data counts
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        # Use correct field names based on actual data structure
        recent_transactions = await db.transactions.count_documents({
            "createdAt": {"$gte": cutoff_time}  # Changed from "timestamp" to "createdAt"
        })
        
        recent_feedback = await db.feedback.count_documents({
            "createdAt": {"$gte": cutoff_time}  # Changed from "timestamp" to "createdAt"
        })
        
        logger.info(f"Data check for retraining: {recent_transactions} transactions, {recent_feedback} feedback in last {time_window_hours}h (need {min_transactions_for_retrain} transactions, {min_feedback_for_retrain} feedback)")
        
        if recent_transactions < min_transactions_for_retrain:
            logger.info(f"Insufficient new transactions ({recent_transactions}/{min_transactions_for_retrain}) - skipping retraining")
            return False
            
        if recent_feedback < min_feedback_for_retrain:
            logger.info(f"Insufficient new feedback ({recent_feedback}/{min_feedback_for_retrain}) - skipping retraining")
            return False
            
        logger.info(f"Sufficient new data found (transactions: {recent_transactions}, feedback: {recent_feedback}) - proceeding with retraining")
        return True
        
    except Exception as e:
        logger.error(f"Error checking if models should retrain: {e}")
        # Default to not retraining if we can't determine
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the startup and shutdown events for the FastAPI application.
    """
    logger.info("AI Service starting up...")
    log_memory_usage("startup")
    settings.display_config()

    # Memory monitoring setup
    log_memory_usage("after config display")

    # 1. Connect to MongoDB
    await connect_to_mongo()
    logger.info("MongoDB connection established.")
    log_memory_usage("after MongoDB connection")
    
    db_client: Any = get_database()

    # 2. Initialize Phase 3 Model Manager with database connection
    logger.info("Initializing Phase 3 Model Manager with database connection...")
    model_manager.db_connected = True  # Set the connection flag
    
    # Initialize Phase 3 models (memory-safe, lazy loading)
    await model_manager.initialize_models()
    log_memory_usage("after Model Manager initialization")

    # 3. Initialize new Phase 4 services globally (LAZY INITIALIZATION)
    global pricing_service_instance, churn_service_instance, reasoning_service_instance, feedback_service_instance
    
    # Create service instances without initializing (lazy)
    pricing_service_instance = PricingService(db_client)
    log_memory_usage("after PricingService creation")
    
    churn_service_instance = ChurnService(db_client)
    log_memory_usage("after ChurnService creation")
    
    reasoning_service_instance = ReasoningService(db_client)
    log_memory_usage("after ReasoningService creation")
    
    feedback_service_instance = FeedbackService(db_client)
    log_memory_usage("after FeedbackService creation")
    
    # Force memory cleanup after service creation
    force_memory_cleanup()
    log_memory_usage("after memory cleanup")
    
    logger.info("All AI services created (lazy initialization - will initialize on first use to conserve memory).")
    
    # 4. Disable automatic retraining to save memory during startup
    # Schedule periodic retraining using APScheduler only if explicitly enabled
    retrain_interval = getattr(settings, 'MODEL_RETRAIN_INTERVAL_MINUTES', 0)
    if retrain_interval and retrain_interval > 0:
        scheduler = AsyncIOScheduler()
        
        retrain_interval_seconds = retrain_interval * 60
        
        scheduler.add_job(
            periodic_model_retraining_all,
            IntervalTrigger(seconds=retrain_interval_seconds),
            id='full_model_retraining_job',
            name='Full Model Retraining Task',
            replace_existing=True
        )
        scheduler.start()
        
        # More descriptive interval message
        if retrain_interval >= 1440:
            interval_desc = f"daily ({retrain_interval//60} hours)"
        elif retrain_interval >= 60:
            interval_desc = f"every {retrain_interval//60} hours"
        else:
            interval_desc = f"every {retrain_interval} minutes"
            
        logger.info(f"Intelligent model retraining scheduled {interval_desc} with data-driven triggers.")
        
        app.state.scheduler = scheduler
    else:
        logger.info("Automatic model retraining DISABLED (interval set to 0) to conserve memory and prevent crashes.")

    yield # Application will run now

    # 5. Shutdown logic
    logger.info("AI Service shutting down...")
    
    if hasattr(app.state, 'scheduler') and app.state.scheduler.running:
        logger.info("Shutting down APScheduler...")
        app.state.scheduler.shutdown()
        logger.info("APScheduler shut down.")
        
    await close_mongo_connection()
    logger.info("AI Service shut down complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    description="FastAPI based AI microservice for Adaptive Business Intelligence. Provides forecasting, anomaly detection, recommendation, dynamic pricing, churn prediction, knowledge graph insights, and feedback capabilities."
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get model manager instance (Phase 3)
def get_model_manager() -> ModelManager:
    return model_manager

# Dependency functions for Phase 4 services to be used by endpoints
async def get_pricing_service_actual() -> PricingService:
    logger.info(f"get_pricing_service_actual called, pricing_service_instance: {pricing_service_instance}")
    if pricing_service_instance is not None:
        logger.info(f"Returning pricing service instance: {type(pricing_service_instance)}")
        return pricing_service_instance
    logger.error("Pricing service instance is None!")
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Pricing service is not available.")

async def get_churn_service_actual() -> ChurnService:
    logger.info(f"get_churn_service_actual called, churn_service_instance: {churn_service_instance}")
    if churn_service_instance is not None:
        return churn_service_instance
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Churn service is not available.")

async def get_reasoning_service_actual() -> ReasoningService:
    logger.info(f"get_reasoning_service_actual called, reasoning_service_instance: {reasoning_service_instance}")
    if reasoning_service_instance is not None:
        return reasoning_service_instance
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Reasoning service is not available.")

async def get_feedback_service_actual() -> FeedbackService:
    logger.info(f"get_feedback_service_actual called, feedback_service_instance: {feedback_service_instance}")
    if feedback_service_instance is not None:
        return feedback_service_instance
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Feedback service is not available.")


# Assign the actual dependency functions BEFORE including routers
advanced_endpoints.get_pricing_service_dependency.actual_func = get_pricing_service_actual
advanced_endpoints.get_churn_service_dependency.actual_func = get_churn_service_actual
advanced_endpoints.get_reasoning_service_dependency.actual_func = get_reasoning_service_actual
advanced_endpoints.get_feedback_service_dependency.actual_func = get_feedback_service_actual

# Include API routers (Phase 3)
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(forecast.router, prefix="/api/v1/forecast", tags=["Forecasting"])
app.include_router(anomaly.router, prefix="/api/v1/anomaly", tags=["Anomaly Detection"])
app.include_router(recommend.router, prefix="/api/v1/recommend", tags=["Recommendation"])

# Include new advanced API routers (Phase 4)
app.include_router(advanced_endpoints.router, prefix="/api/v1/ai", tags=["Advanced AI"])


@app.get("/", summary="Root endpoint", tags=["Root"])
async def read_root():
    """
    Root endpoint for the AI service.
    """
    return {"message": "Welcome to the Adaptive BI AI Service!", "version": settings.APP_VERSION}

@app.get("/status", summary="Service status", tags=["Status"])
async def get_service_status(manager: ModelManager = Depends(get_model_manager)):
    """
    Provides a quick status overview of the AI service, including model readiness.
    """
    status_response = {
        "status": "running",
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG,
        "database_connected": manager.db_connected,
        "phase3_models": {
            "overall_loaded": manager.models_loaded,
            "forecasting_model_trained": manager.forecasting_model.is_trained if manager.forecasting_model else False,
            "anomaly_model_trained": manager.anomaly_model.is_trained if manager.anomaly_model else False,
            "recommendation_model_trained": manager.recommendation_model.is_trained if manager.recommendation_model else False,
            "last_retrain_time": manager.last_retrain_time.isoformat() if manager.last_retrain_time else "N/A",
            "retrain_interval_minutes": settings.MODEL_RETRAIN_INTERVAL_MINUTES
        },
        "phase4_services": {
            "pricing_service_ready": pricing_service_instance._model_trained if pricing_service_instance else False,
            "churn_service_ready": churn_service_instance._model_trained if churn_service_instance else False,
            "reasoning_service_ready": reasoning_service_instance._graph_built if reasoning_service_instance else False,
            "feedback_service_ready": feedback_service_instance._initialized if feedback_service_instance else False,
        },
        "overall_readiness": "initializing"
    }

    all_models_ready = (
        manager.models_loaded and
        (pricing_service_instance and pricing_service_instance._model_trained) and
        (churn_service_instance and churn_service_instance._model_trained) and
        (reasoning_service_instance and reasoning_service_instance._graph_built) and
        (feedback_service_instance and feedback_service_instance._initialized)
    )

    if all_models_ready:
        status_response["overall_readiness"] = "ready"
    else:
        status_response["overall_readiness"] = "partial_readiness"

    return status_response


if __name__ == "__main__":
    host = getattr(settings, 'HOST', "0.0.0.0")
    port = getattr(settings, 'PORT', 8001)
    debug = getattr(settings, 'DEBUG', False)

    uvicorn.run(app, host=host, port=port, reload=debug)

