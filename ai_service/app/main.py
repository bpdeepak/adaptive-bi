# ai_service/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_to_database, close_database_connection
from app.utils.logger import logger
from app.api.routes import forecast, anomaly, recommend, health # Import routers
from app.models.model_manager import model_manager, ModelManager
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler # Import APScheduler
from apscheduler.triggers.interval import IntervalTrigger # Import IntervalTrigger

# Define the periodic task function
async def periodic_model_retraining():
    logger.info("Starting scheduled model retraining...")
    try:
        await model_manager.train_all_models()
        logger.info("Scheduled model retraining completed successfully.")
    except Exception as e:
        logger.error(f"Error during scheduled model retraining: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the startup and shutdown events for the FastAPI application.
    """
    logger.info("AI Service starting up...")
    settings.display_config() # Display configuration on startup

    # Connect to MongoDB
    await connect_to_database()

    # Initialize and potentially train models
    try:
        await model_manager.initialize_models()
        logger.info("AI models initialized successfully.")

        # Schedule periodic retraining using APScheduler
        if settings.MODEL_RETRAIN_INTERVAL_MINUTES > 0:
            scheduler = AsyncIOScheduler()
            
            # Convert minutes to seconds for IntervalTrigger
            retrain_interval_seconds = settings.MODEL_RETRAIN_INTERVAL_MINUTES * 60
            
            scheduler.add_job(
                periodic_model_retraining,
                IntervalTrigger(seconds=retrain_interval_seconds),
                id='model_retraining_job',
                name='Model Retraining Task',
                replace_existing=True # Ensures only one job runs if lifespan is called multiple times
            )
            scheduler.start()
            logger.info(f"Model retraining scheduled every {settings.MODEL_RETRAIN_INTERVAL_MINUTES} minutes.")
            
            # Store scheduler in app state for graceful shutdown
            app.state.scheduler = scheduler

    except Exception as e:
        logger.error(f"Failed to initialize AI models: {e}", exc_info=True)
        # Depending on criticality, you might want to exit or just log error
        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI model initialization failed: {e}")


    yield # Application runs

    # Shutdown events
    logger.info("AI Service shutting down...")
    
    # Shut down APScheduler gracefully
    if hasattr(app.state, 'scheduler') and app.state.scheduler.running:
        logger.info("Shutting down APScheduler...")
        app.state.scheduler.shutdown()
        logger.info("APScheduler shut down.")
        
    await close_database_connection()
    logger.info("AI Service shut down complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan, # Assign the lifespan context manager
    description="FastAPI based AI microservice for Adaptive Business Intelligence. Provides forecasting, anomaly detection, and recommendation capabilities."
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS, # Use configured origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(forecast.router, prefix="/api/v1/forecast", tags=["Forecasting"])
app.include_router(anomaly.router, prefix="/api/v1/anomaly", tags=["Anomaly Detection"])
app.include_router(recommend.router, prefix="/api/v1/recommend", tags=["Recommendation"])


@app.get("/", summary="Root endpoint", tags=["Root"])
async def read_root():
    """
    Root endpoint for the AI service.
    """
    return {"message": "Welcome to the Adaptive BI AI Service!", "version": settings.APP_VERSION}

# Dependency to get model manager instance
def get_model_manager() -> ModelManager:
    return model_manager

# Example route that uses a dependency (can be used for models later)
@app.get("/status", summary="Service status", tags=["Status"])
async def get_service_status(manager: ModelManager = Depends(get_model_manager)):
    """
    Provides a quick status overview of the AI service, including model readiness.
    """
    return {
        "status": "running",
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG,
        "database_connected": manager.db_connected,
        "models_loaded": manager.models_loaded,
        "forecasting_model_trained": manager.forecasting_model.is_trained if manager.forecasting_model else False,
        "anomaly_model_trained": manager.anomaly_model.is_trained if manager.anomaly_model else False,
        "recommendation_model_trained": manager.recommendation_model.is_trained if manager.recommendation_model else False,
        "last_retrain_time": manager.last_retrain_time.isoformat() if manager.last_retrain_time else "N/A",
        "retrain_interval_minutes": settings.MODEL_RETRAIN_INTERVAL_MINUTES
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)