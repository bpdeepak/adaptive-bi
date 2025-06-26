## Project Directory Structure
```
./
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── anomaly.py
│   │   │   ├── forecast.py
│   │   │   ├── health.py
│   │   │   ├── __init__.py
│   │   │   └── recommend.py
│   │   ├── dependencies.py
│   │   └── __init__.py
│   ├── services/
│   │   ├── data_processor.py
│   │   ├── feature_engineering.py
│   │   └── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logger.py
│   ├── config.py
│   ├── database.py
│   ├── __init__.py
│   └── main.py
├── data/
│   └── processed/
├── logs/
│   └── ai_service_2025-06-26.log
├── tests/
│   └── __init__.py
├── ai_service-Codebase-Dump-2025-06-26.md
├── ai_service-Frontend-Codebase-Dump-2025-06-26.md
├── Dockerfile
├── gen_cb.sh*
├── requirements.txt
└── sys.stdout

10 directories, 24 files
```



### `./ai_service-Frontend-Codebase-Dump-2025-06-26.md`
```md
## Project Directory Structure
```
./
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── anomaly.py
│   │   │   ├── forecast.py
│   │   │   ├── health.py
│   │   │   ├── __init__.py
│   │   │   └── recommend.py
│   │   ├── dependencies.py
│   │   └── __init__.py
│   ├── services/
│   │   ├── data_processor.py
│   │   ├── feature_engineering.py
│   │   └── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logger.py
│   ├── config.py
│   ├── database.py
│   ├── __init__.py
│   └── main.py
├── data/
│   └── processed/
├── logs/
│   └── ai_service_2025-06-26.log
├── tests/
│   └── __init__.py
├── ai_service-Frontend-Codebase-Dump-2025-06-26.md
├── Dockerfile
├── gen_cb.sh*
├── requirements.txt
└── sys.stdout

10 directories, 23 files
```



### `./app/api/dependencies.py`
```py
from app.database import get_database
from app.models.model_manager import ModelManager
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from app.utils.logger import logger

def get_db() -> AsyncIOMotorDatabase:
    """
    Dependency to get the MongoDB database instance.
    """
    db = get_database()
    if not db:
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
```

### `./app/api/__init__.py`
```py

```

### `./app/api/routes/anomaly.py`
```py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.models.model_manager import ModelManager
from app.services.data_processor import DataProcessor
from app.utils.logger import logger
from app.api.dependencies import get_db, get_model_manager
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta

router = APIRouter()

class AnomalyDetectionRequest(BaseModel):
    data_points: List[Dict[str, Any]] = Field(
        ...,
        description="List of data points to check for anomalies. Each dict should contain features used for training (e.g., 'totalAmount', 'quantity')."
    )
    # You might want to allow specifying features dynamically or assume they are pre-defined
    # For now, let's assume they are predefined in the model's training process
    features: List[str] = Field(
        ["totalAmount", "quantity"], # Default example features
        description="List of features to use for anomaly detection. Must match features used during training."
    )

class AnomalyResponse(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    data: Dict[str, Any]
    details: Dict[str, Any]

@router.post("/train", summary="Trigger training for the anomaly detection model")
async def train_anomaly_model(
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually triggers the training process for the anomaly detection model.
    It uses recent transaction data to train the model.
    """
    logger.info("API call: /anomaly/train received.")
    try:
        data_processor = DataProcessor(db=db)
        transactions_df = await data_processor.get_transactions_data()

        if transactions_df.empty:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sufficient data available for anomaly detection model training.")

        # Prepare features for anomaly detection (example: totalAmount, quantity)
        # Ensure numerical columns
        transactions_df['totalAmount'] = pd.to_numeric(transactions_df['totalAmount'], errors='coerce').fillna(0)
        transactions_df['quantity'] = pd.to_numeric(transactions_df['quantity'], errors='coerce').fillna(0)
        
        # Define features. These should align with what the model expects.
        anomaly_features = ["totalAmount", "quantity"]
        valid_anomaly_features = [f for f in anomaly_features if f in transactions_df.columns and pd.api.types.is_numeric_dtype(transactions_df[f])]

        if not valid_anomaly_features:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid numerical features found for anomaly detection training.")

        result = model_manager.anomaly_model.train(transactions_df, features=valid_anomaly_features)
        if result.get("status") == "success":
            return {"message": "Anomaly detection model training initiated successfully.", "metrics": result.get("metrics")}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Anomaly detection model training failed."))
    except Exception as e:
        logger.error(f"Error during anomaly model training API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during training: {e}")


@router.post("/detect", summary="Detect anomalies in provided data points", response_model=List[AnomalyResponse])
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Detects anomalies in a list of incoming data points.
    Each data point should be a dictionary containing the features used to train the anomaly model.
    """
    logger.info(f"API call: /anomaly/detect received for {len(request.data_points)} data points.")
    if not model_manager.anomaly_model.is_trained:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Anomaly detection model is not trained yet. Please train it first.")

    if not request.data_points:
        return []

    try:
        df = pd.DataFrame(request.data_points)
        # Ensure numerical columns for detection
        for col in request.features:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                logger.warning(f"Feature '{col}' not found in input data points for anomaly detection.")
                # You might want to raise an error or fill with a default value
                df[col] = 0 # Add missing feature with default 0


        detected_df = model_manager.anomaly_model.detect_anomalies(df.copy(), features=request.features)
        
        results = []
        for index, row in detected_df.iterrows():
            result = AnomalyResponse(
                is_anomaly=bool(row['is_anomaly']),
                anomaly_score=float(row['anomaly_score']),
                data={k: v for k, v in row.items() if k not in ['is_anomaly', 'anomaly_score']}, # All other fields
                details={feat: row[feat] for feat in request.features if feat in row} # Only anomaly features
            )
            results.append(result)
        
        return results

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error during anomaly detection API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during detection: {e}")


@router.get("/status", summary="Get anomaly detection model status")
async def get_anomaly_model_status(model_manager: ModelManager = Depends(get_model_manager)):
    """
    Returns the current training status and metrics of the anomaly detection model.
    """
    status_info = {
        "is_trained": model_manager.anomaly_model.is_trained,
        "model_type": model_manager.anomaly_model.model_type,
        "contamination_threshold": model_manager.anomaly_model.contamination,
        "metrics": model_manager.anomaly_model.metrics,
        "last_retrain_time": model_manager.last_retrain_time.isoformat() if model_manager.last_retrain_time else "N/A"
    }
    return status_info
```

### `./app/api/routes/forecast.py`
```py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.model_manager import ModelManager
from app.services.data_processor import DataProcessor
from app.utils.logger import logger
from app.api.dependencies import get_db, get_model_manager
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/train", summary="Trigger training for the forecasting model")
async def train_forecasting_model(
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually triggers the training process for the sales forecasting model.
    """
    logger.info("API call: /forecast/train received.")
    try:
        data_processor = DataProcessor(db=db)
        transactions_df = await data_processor.get_transactions_data()
        daily_sales_df = data_processor.prepare_time_series_data(transactions_df, 'totalAmount', freq='D')

        if daily_sales_df.empty:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sufficient data available for forecasting model training.")

        result = model_manager.forecasting_model.train(daily_sales_df, target_col='totalAmount')
        if result.get("status") == "success":
            return {"message": "Forecasting model training initiated successfully.", "metrics": result.get("metrics")}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Forecasting model training failed."))
    except Exception as e:
        logger.error(f"Error during forecasting model training API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during training: {e}")

@router.get("/predict", summary="Get sales forecast for the next N days")
async def get_sales_forecast(
    horizon: int = Query(7, ge=1, le=30, description="Number of days to forecast into the future"),
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Retrieves the sales forecast for the specified number of days.
    The model must be trained before predictions can be made.
    """
    logger.info(f"API call: /forecast/predict for {horizon} days received.")
    if not model_manager.forecasting_model.is_trained:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Forecasting model is not trained yet. Please train it first.")

    try:
        data_processor = DataProcessor(db=db)
        # Fetch recent historical data to generate features for forecasting
        historical_transactions_df = await data_processor.get_transactions_data(days=model_manager.forecasting_model.feature_engineer.create_lag_features.__defaults__[1][-1] + 30) # Enough days for lags + some buffer
        historical_daily_sales_df = data_processor.prepare_time_series_data(historical_transactions_df, 'totalAmount', freq='D')

        if historical_daily_sales_df.empty:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enough historical data to generate forecast.")

        forecast_df = model_manager.forecasting_model.forecast_future(
            historical_daily_sales_df,
            horizon=horizon,
            target_col='totalAmount'
        )
        
        if forecast_df.empty:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate forecast, resulting DataFrame is empty.")

        # Format output
        forecast_data = forecast_df.rename(columns={'timestamp': 'date', 'totalAmount': 'predicted_sales'}).to_dict(orient='records')
        # Convert datetime objects to ISO format strings
        for item in forecast_data:
            item['date'] = item['date'].isoformat().split('T')[0] # Get only date part

        return {"message": "Sales forecast generated successfully", "forecast": forecast_data}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error during sales forecast prediction API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during prediction: {e}")

@router.get("/status", summary="Get forecasting model status")
async def get_forecasting_model_status(model_manager: ModelManager = Depends(get_model_manager)):
    """
    Returns the current training status and metrics of the forecasting model.
    """
    status_info = {
        "is_trained": model_manager.forecasting_model.is_trained,
        "model_type": model_manager.forecasting_model.model_type,
        "metrics": model_manager.forecasting_model.metrics,
        "last_retrain_time": model_manager.last_retrain_time.isoformat() if model_manager.last_retrain_time else "N/A"
    }
    return status_info
```

### `./app/api/routes/health.py`
```py
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
```

### `./app/api/routes/__init__.py`
```py

```

### `./app/api/routes/recommend.py`
```py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any
from app.models.model_manager import ModelManager
from app.services.data_processor import DataProcessor
from app.utils.logger import logger
from app.api.dependencies import get_db, get_model_manager
from motor.motor_asyncio import AsyncIOMotorDatabase
import pandas as pd # Import pandas for DataFrame handling if needed

router = APIRouter()

@router.post("/train", summary="Trigger training for the recommendation model")
async def train_recommendation_model(
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually triggers the training process for the recommendation model.
    It uses transaction data to build the user-item interaction matrix.
    """
    logger.info("API call: /recommend/train received.")
    try:
        data_processor = DataProcessor(db=db)
        result = await model_manager.recommendation_model.train(data_processor)
        if result.get("status") == "success":
            return {"message": "Recommendation model training initiated successfully."}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Recommendation model training failed."))
    except Exception as e:
        logger.error(f"Error during recommendation model training API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during training: {e}")


@router.get("/user/{user_id}", summary="Get personalized product recommendations for a user")
async def get_user_recommendations(
    user_id: str,
    num_recommendations: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Retrieves personalized product recommendations for a specific user.
    If the user is new (cold-start) or model is not trained, returns popular products.
    """
    logger.info(f"API call: /recommend/user/{user_id} received for {num_recommendations} recommendations.")
    
    # Check if model is trained, if not, it will default to popular items
    if not model_manager.recommendation_model.is_trained:
        logger.warning("Recommendation model is not trained. Providing popular recommendations.")
        data_processor = DataProcessor(db=db)
        product_df = await data_processor.get_product_data()
        popular_recommendations = model_manager.recommendation_model._get_popular_recommendations(num_recommendations, product_data=product_df)
        return {"message": "Recommendation model not trained, returned popular items.", "recommendations": popular_recommendations}

    try:
        data_processor = DataProcessor(db=db)
        product_df = await data_processor.get_product_data() # Fetch product details for richer recommendations
        
        recommendations = await model_manager.recommendation_model.get_user_recommendations(
            user_id, num_recommendations, product_data=product_df
        )
        
        if not recommendations:
            # If personalized recommendations fail, fall back to popular
            popular_recommendations = model_manager.recommendation_model._get_popular_recommendations(num_recommendations, product_data=product_df)
            return {"message": f"No personalized recommendations found for user {user_id}. Returning popular items.", "recommendations": popular_recommendations}

        return {"message": f"Recommendations for user {user_id} generated successfully.", "recommendations": recommendations}
    except Exception as e:
        logger.error(f"Error during recommendation API call for user {user_id}: {e}", exc_info=True)
        # Fallback to popular recommendations in case of critical error
        try:
            data_processor = DataProcessor(db=db)
            product_df = await data_processor.get_product_data()
            popular_recommendations = model_manager.recommendation_model._get_popular_recommendations(num_recommendations, product_data=product_df)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"message": f"Internal server error, falling back to popular recommendations: {e}", "recommendations": popular_recommendations})
        except Exception as fallback_e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during recommendation: {e}. Fallback also failed: {fallback_e}")


@router.get("/status", summary="Get recommendation model status")
async def get_recommendation_model_status(model_manager: ModelManager = Depends(get_model_manager)):
    """
    Returns the current training status of the recommendation model.
    """
    status_info = {
        "is_trained": model_manager.recommendation_model.is_trained,
        "model_type": model_manager.recommendation_model.model_type,
        "n_components": model_manager.recommendation_model.n_components,
        "last_retrain_time": model_manager.last_retrain_time.isoformat() if model_manager.last_retrain_time else "N/A"
    }
    return status_info
```

### `./app/config.py`
```py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration class for the AI microservice.
    Loads settings from environment variables.
    """
    APP_NAME: str = "Adaptive BI AI Service"
    APP_VERSION: str = "1.0.0"

    # Server settings
    HOST: str = os.getenv("AI_SERVICE_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("AI_SERVICE_PORT", 8000))
    DEBUG: bool = os.getenv("AI_SERVICE_DEBUG", "False").lower() == "true"

    # MongoDB settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/adaptive_bi")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "adaptive_bi")

    # JWT settings (if used for internal service communication)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your_strong_jwt_secret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # Model settings
    MODEL_SAVE_PATH: str = os.getenv("MODEL_SAVE_PATH", "/app/models/saved_models")
    RETRAIN_INTERVAL_HOURS: int = int(os.getenv("RETRAIN_INTERVAL_HOURS", 24))

    # Forecasting Model Parameters
    FORECAST_HORIZON: int = int(os.getenv("FORECAST_HORIZON", 7)) # Days to forecast
    FORECAST_MODEL_TYPE: str = os.getenv("FORECAST_MODEL_TYPE", "RandomForestRegressor") # RandomForestRegressor or LinearRegression

    # Anomaly Detection Model Parameters
    ANOMALY_THRESHOLD: float = float(os.getenv("ANOMALY_THRESHOLD", 0.05)) # For IsolationForest, contamination
    ANOMALY_MODEL_TYPE: str = os.getenv("ANOMALY_MODEL_TYPE", "IsolationForest") # IsolationForest or OneClassSVM

    # Recommendation Model Parameters
    MIN_INTERACTIONS_FOR_RECOMMENDATION: int = int(os.getenv("MIN_INTERACTIONS_FOR_RECOMMENDATION", 5))
    RECOMMENDER_MODEL_TYPE: str = os.getenv("RECOMMENDER_MODEL_TYPE", "SVD") # SVD or KNNWithMeans

    # Data collection window for training
    DATA_COLLECTION_DAYS: int = int(os.getenv("DATA_COLLECTION_DAYS", 90)) # Data from last 90 days for training

    # CORS settings
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",") # Allows all origins for development

    def __init__(self):
        # Ensure model save path exists
        if not os.path.exists(self.MODEL_SAVE_PATH):
            os.makedirs(self.MODEL_SAVE_PATH)

    def display_config(self):
        """Prints the current configuration (excluding sensitive info)."""
        print("\n--- AI Service Configuration ---")
        print(f"App Name: {self.APP_NAME}")
        print(f"Version: {self.APP_VERSION}")
        print(f"Host: {self.HOST}, Port: {self.PORT}")
        print(f"Debug Mode: {self.DEBUG}")
        print(f"MongoDB URL: {self.MONGODB_URL.split('@')[-1] if '@' in self.MONGODB_URL else self.MONGODB_URL}") # Mask password
        print(f"Database Name: {self.DATABASE_NAME}")
        print(f"Model Save Path: {self.MODEL_SAVE_PATH}")
        print(f"Retrain Interval (Hours): {self.RETRAIN_INTERVAL_HOURS}")
        print(f"Forecast Horizon (Days): {self.FORECAST_HORIZON}")
        print(f"Anomaly Threshold: {self.ANOMALY_THRESHOLD}")
        print(f"Data Collection Days: {self.DATA_COLLECTION_DAYS}")
        print(f"CORS Origins: {self.CORS_ORIGINS}")
        print("--------------------------------\n")

# Instantiate config
settings = Config()

if __name__ == "__main__":
    settings.display_config()
```

### `./app/database.py`
```py
import motor.motor_asyncio
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import settings
from app.utils.logger import logger

# Async MongoDB client for FastAPI
client = None
db = None

# Synchronous MongoDB client for model training scripts (if needed outside FastAPI context)
sync_client = None
sync_db = None

async def connect_to_database():
    """
    Establishes an asynchronous connection to MongoDB.
    """
    global client, db
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        # The ping command is cheap and does not require auth.
        await db.command('ping')
        logger.info(f"Successfully connected to MongoDB at {settings.MONGODB_URL.split('@')[-1]}")
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed (ConnectionFailure): {e}")
        # Optionally re-raise or exit if DB is critical for startup
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during MongoDB connection: {e}")
        raise

async def close_database_connection():
    """
    Closes the asynchronous MongoDB connection.
    """
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    """
    Returns the asynchronous MongoDB database instance.
    """
    return db

def connect_to_sync_database():
    """
    Establishes a synchronous connection to MongoDB.
    Used for scripts that might not run within an async context directly.
    """
    global sync_client, sync_db
    try:
        sync_client = MongoClient(settings.MONGODB_URL)
        sync_db = sync_client[settings.DATABASE_NAME]
        sync_db.command('ping') # Test connection
        logger.info(f"Successfully connected to synchronous MongoDB at {settings.MONGODB_URL.split('@')[-1]}")
    except ConnectionFailure as e:
        logger.error(f"Synchronous MongoDB connection failed (ConnectionFailure): {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during synchronous MongoDB connection: {e}")
        raise

def close_sync_database_connection():
    """
    Closes the synchronous MongoDB connection.
    """
    global sync_client
    if sync_client:
        sync_client.close()
        logger.info("Synchronous MongoDB connection closed.")

def get_sync_database():
    """
    Returns the synchronous MongoDB database instance.
    """
    return sync_db

if __name__ == "__main__":
    import asyncio

    # Test async connection
    async def test_async_db():
        try:
            await connect_to_database()
            if db is not None:
                logger.info("Async DB connection test successful.")
                collections = await db.list_collection_names()
                logger.info(f"Collections: {collections}")
            else:
                logger.error("Async DB connection test failed: db object is None.")
        except Exception as e:
            logger.error(f"Async DB connection test encountered an error: {e}")
        finally:
            await close_database_connection()

    asyncio.run(test_async_db())

    # Test sync connection
    try:
        connect_to_sync_database()
        if sync_db:
            logger.info("Sync DB connection test successful.")
            collections = sync_db.list_collection_names()
            logger.info(f"Collections: {collections}")
        else:
            logger.error("Sync DB connection test failed: sync_db object is None.")
    except Exception as e:
        logger.error(f"Sync DB connection test encountered an error: {e}")
    finally:
        close_sync_database_connection()
```

### `./app/__init__.py`
```py

```

### `./app/main.py`
```py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_to_database, close_database_connection
from app.utils.logger import logger
from app.api.routes import forecast, anomaly, recommend, health # Import routers
from app.models.model_manager import model_manager, ModelManager
import asyncio

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
        # Load models at startup, or train if not found/retrain needed
        # We'll use a separate task for retraining if needed after startup
        await model_manager.initialize_models()
        logger.info("AI models initialized successfully.")

        # Schedule periodic retraining in the background
        if settings.RETRAIN_INTERVAL_HOURS > 0:
            logger.info(f"Scheduling model retraining every {settings.RETRAIN_INTERVAL_HOURS} hours.")
            asyncio.create_task(model_manager.schedule_retraining())

    except Exception as e:
        logger.error(f"Failed to initialize AI models: {e}", exc_info=True)
        # Depending on criticality, you might want to exit or just log error
        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI model initialization failed: {e}")


    yield # Application runs

    # Shutdown events
    logger.info("AI Service shutting down...")
    await close_database_connection()
    logger.info("AI Service shut down complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
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
        "last_retrain_time": manager.last_retrain_time.isoformat() if manager.last_retrain_time else "N/A"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

### `./app/models/anomaly_detection.py`
```py
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
import joblib
import os
from app.config import settings
from app.utils.logger import logger
from app.services.feature_engineering import FeatureEngineer

class AnomalyDetectionModel:
    """
    Implements a machine learning model for anomaly detection.
    Supports IsolationForest and OneClassSVM.
    """
    def __init__(self, model_type: str = settings.ANOMALY_MODEL_TYPE, contamination: float = settings.ANOMALY_THRESHOLD):
        self.model = None
        self.model_type = model_type
        self.contamination = contamination
        self.feature_engineer = FeatureEngineer() # Feature engineer for scaling etc.
        self.model_path = os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_model_{model_type}.joblib")
        self.is_trained = False
        self.metrics = {}

    def _initialize_model(self):
        """Initializes the ML model based on model_type."""
        if self.model_type == "IsolationForest":
            self.model = IsolationForest(contamination=self.contamination, random_state=42, n_estimators=100)
            logger.info(f"Initialized IsolationForest for anomaly detection with contamination={self.contamination}.")
        elif self.model_type == "OneClassSVM":
            # nu is an upper bound on the fraction of training errors and a lower bound of the fraction of support vectors.
            # It's similar to contamination. A common value is 0.1 for typical anomaly rates.
            self.model = OneClassSVM(kernel='rbf', nu=self.contamination)
            logger.info(f"Initialized OneClassSVM for anomaly detection with nu={self.contamination}.")
        else:
            raise ValueError(f"Unsupported anomaly detection model type: {self.model_type}")

    def train(self, df: pd.DataFrame, features: list) -> dict:
        """
        Trains the anomaly detection model.
        :param df: DataFrame containing features for anomaly detection.
        :param features: List of columns to be used as features.
        """
        if df.empty or not features or not all(col in df.columns for col in features):
            logger.warning("No data or invalid features for anomaly detection training.")
            return {"status": "failed", "message": "No data or invalid features."}

        # Select features
        X = df[features]

        # Scale features (important for distance-based algorithms like SVM)
        # Scale features (important for distance-based algorithms like SVM)
        X_scaled = self.feature_engineer.scale_features(X, features, scaler_type='MinMaxScaler', fit=True)
        # Store original feature names for prediction consistency
        self._trained_features = X_scaled.columns.tolist()

        self._initialize_model()
        logger.info(f"Starting training for {self.model_type} model with {len(X_scaled)} samples and {len(features)} features.")
        if self.model is None:
            logger.error("Model is not initialized. Cannot fit.")
            return {"status": "failed", "message": "Model initialization failed."}
        self.model.fit(X_scaled)
        # No traditional "metrics" for unsupervised anomaly detection,
        if self.model_type == "IsolationForest":
            if self.model is not None:
                predictions = self.model.predict(X_scaled)
                n_outliers = list(predictions).count(-1)
                outlier_percentage = (n_outliers / len(predictions)) * 100 if len(predictions) > 0 else 0
                self.metrics = {"outliers_in_training_data": n_outliers, "outlier_percentage": f"{outlier_percentage:.2f}%"}
            else:
                logger.error("Model is None during prediction.")
                self.metrics = {}
        elif self.model_type == "OneClassSVM":
            if self.model is not None:
                predictions = self.model.predict(X_scaled)
                n_outliers = list(predictions).count(-1)
                outlier_percentage = (n_outliers / len(predictions)) * 100 if len(predictions) > 0 else 0
                self.metrics = {"outliers_in_training_data": n_outliers, "outlier_percentage": f"{outlier_percentage:.2f}%"}
            else:
                logger.error("Model is None during prediction.")
                self.metrics = {}
            outlier_percentage = (n_outliers / len(predictions)) * 100 if len(predictions) > 0 else 0
            self.metrics = {"outliers_in_training_data": n_outliers, "outlier_percentage": f"{outlier_percentage:.2f}%"}

        self.is_trained = True
        logger.info(f"Anomaly detection model training complete. Metrics: {self.metrics}")
        self.save_model()
        return {"status": "success", "metrics": self.metrics}

    def detect_anomalies(self, df: pd.DataFrame, features: list) -> pd.DataFrame:
        """
        Detects anomalies in the input DataFrame.
        Returns the DataFrame with an 'is_anomaly' column and anomaly scores.
        """
        if not self.is_trained or self.model is None:
            logger.error("Anomaly detection model not trained. Cannot detect anomalies.")
            raise ValueError("Model not trained.")
        if df.empty or not features or not all(col in df.columns for col in features):
            logger.warning("No data or invalid features for anomaly detection.")
            return df.assign(is_anomaly=False, anomaly_score=0.0) # Return with default columns

        X = df[features]
        # Use existing scaler for transformation
        X_scaled = self.feature_engineer.scale_features(X, features, scaler_type='MinMaxScaler', fit=False)

        # Ensure prediction features match trained features
        # This is a critical step. If `_trained_features` is None or not matching, it's an error.
        if not hasattr(self, '_trained_features') or not self._trained_features:
            logger.error("Trained features not available. Model might not have been trained or loaded correctly.")
            raise RuntimeError("Trained features not found for anomaly detection.")
        
        # Align columns of X_scaled with self._trained_features, filling missing ones with 0 or appropriate default
        X_scaled = X_scaled.reindex(columns=self._trained_features, fill_value=0)

        # Predict raw scores or decisions
        if self.model_type == "IsolationForest":
            # decision_function gives anomaly scores: lower is more anomalous
            df['anomaly_score'] = self.model.decision_function(X_scaled)
            # predict returns -1 for outliers, 1 for inliers
            df['is_anomaly'] = (self.model.predict(X_scaled) == -1)
        elif self.model_type == "OneClassSVM":
            # decision_function gives distance to hyperplane: negative for outliers
            df['anomaly_score'] = self.model.decision_function(X_scaled)
            df['is_anomaly'] = (self.model.predict(X_scaled) == -1)
        else:
            raise ValueError(f"Unsupported model type {self.model_type} for anomaly detection logic.")

        logger.info(f"Detected anomalies for {len(df)} samples.")
        return df
        for _, row in anomalies_df.iterrows():
            timestamp_value = row.get('timestamp')
            detail = {
                "id": str(row.get('_id')), # Assuming _id exists and can be converted to str
                "timestamp": timestamp_value.isoformat() if timestamp_value is not None and hasattr(timestamp_value, "isoformat") else None,
                "anomaly_score": float(row['anomaly_score']),
                "features": {feat: row[feat] for feat in anomaly_features if feat in row}
            }
            details.append(detail)
        return details
        details = []
        for index, row in anomalies_df.iterrows():
            detail = {
                "id": str(row.get('_id')), # Assuming _id exists and can be converted to str
                "timestamp": row.get('timestamp').isoformat() if 'timestamp' in row else None,
                "anomaly_score": float(row['anomaly_score']),
                "features": {feat: row[feat] for feat in anomaly_features if feat in row}
            }
            details.append(detail)
        return details

    def save_model(self):
        """Saves the trained model and its feature engineer."""
        if self.model:
            os.makedirs(settings.MODEL_SAVE_PATH, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.feature_engineer, os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_feature_engineer_{self.model_type}.joblib"))
            # Also save the list of trained features
            if hasattr(self, '_trained_features'):
                joblib.dump(self._trained_features, os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_trained_features_{self.model_type}.joblib"))
            logger.info(f"Anomaly detection model and feature engineer saved to {self.model_path}")
        else:
            logger.warning("No anomaly detection model to save.")

    def load_model(self):
        """Loads the trained model and its feature engineer."""
        try:
            self.model = joblib.load(self.model_path)
            self.feature_engineer = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_feature_engineer_{self.model_type}.joblib"))
            # Load trained features
            trained_features_path = os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_trained_features_{self.model_type}.joblib")
            if os.path.exists(trained_features_path):
                self._trained_features = joblib.load(trained_features_path)
            else:
                logger.warning("Trained features not found for anomaly model. This might cause issues during prediction if feature set changes.")
                self._trained_features = None # Or raise error
            
            self.is_trained = True
            logger.info(f"Anomaly detection model and feature engineer loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Anomaly detection model not found at {self.model_path}. Model needs to be trained.")
            self.is_trained = False
            return False
        except Exception as e:
            logger.error(f"Error loading anomaly detection model: {e}", exc_info=True)
            self.is_trained = False
            return False
```

### `./app/models/forecasting.py`
```py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
# from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
from app.config import settings
from app.utils.logger import logger
from app.services.feature_engineering import FeatureEngineer

class ForecastingModel:
    """
    Implements a machine learning model for sales forecasting.
    Supports RandomForestRegressor and LinearRegression.
    """
    def __init__(self, model_type: str = settings.FORECAST_MODEL_TYPE):
        self.model = None
        self.model_type = model_type
        self.feature_engineer = FeatureEngineer()
        self.model_path = os.path.join(settings.MODEL_SAVE_PATH, f"forecasting_model_{model_type}.joblib")
        self.is_trained = False
        self.metrics = {} # To store training metrics

    def _initialize_model(self):
        """Initializes the ML model based on model_type."""
        if self.model_type == "RandomForestRegressor":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            logger.info("Initialized RandomForestRegressor for forecasting.")
        elif self.model_type == "LinearRegression":
            self.model = LinearRegression()
            logger.info("Initialized LinearRegression for forecasting.")
        else:
            raise ValueError(f"Unsupported forecasting model type: {self.model_type}")

    def train(self, df: pd.DataFrame, target_col: str = 'daily_revenue') -> dict:
        """
        Trains the forecasting model.
        Expects df to be prepared with time series and feature engineering.
        """
        if df.empty:
            logger.warning("No data to train forecasting model.")
            return {"status": "failed", "message": "No data for training."}

        # Ensure 'timestamp' is datetime and sort
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Create time features
        df = self.feature_engineer.create_time_features(df, 'timestamp')

        # Create lag features for the target column
        # Lags are important for time series forecasting
        df = self.feature_engineer.create_lag_features(df, cols=[target_col], lags=[1, 2, 3, 7, 14])

        # Create rolling features
        df = self.feature_engineer.create_rolling_features(df, cols=[target_col], windows=[7, 14], agg_funcs=['mean', 'std'])

        # Drop rows with NaN values that result from lag/rolling features (typically at the beginning)
        df = df.dropna().reset_index(drop=True)
        if df.empty:
            logger.warning("DataFrame became empty after feature engineering and dropping NaNs.")
            return {"status": "failed", "message": "DataFrame empty after feature engineering."}

        # Define features and target
        features = [col for col in df.columns if col not in [target_col, 'timestamp', '_id']]
        X, y = self.feature_engineer.get_features_and_target(df, target_col, feature_cols=features)

        if X.empty or y.empty:
            logger.error("Features or target are empty after preparation for forecasting model training.")
            return {"status": "failed", "message": "Empty features or target after preparation."}

        # Split data (time-based split is crucial for time series)
        split_point = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_point], X.iloc[split_point:]
        y_train, y_test = y.iloc[:split_point], y.iloc[split_point:]

        if X_train.empty or y_train.empty:
            logger.warning("Training data is empty for forecasting model.")
            return {"status": "failed", "message": "Empty training data."}

        # Always initialize the model before training to avoid 'NoneType' errors
        self._initialize_model()

        logger.info(f"Starting training for {self.model_type} model with {len(X_train)} samples.")
        self.model.fit(X_train, y_train) # type: ignore

        # Evaluate
        y_pred = self.model.predict(X_test) # type: ignore
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        self.metrics = {"rmse": rmse, "r2_score": r2, "trained_on_samples": len(X_train)}
        self.is_trained = True
        logger.info(f"Forecasting model training complete. Metrics: {self.metrics}")

        self.save_model()
        return {"status": "success", "metrics": self.metrics}

    def predict(self, df: pd.DataFrame, target_col: str = 'daily_revenue') -> np.ndarray:
        """
        Makes predictions using the trained model.
        Expects df to be prepared with the same feature engineering steps as training.
        """
        if not self.is_trained or self.model is None:
            logger.error("Forecasting model not trained. Cannot make predictions.")
            raise ValueError("Model not trained.")
        if df.empty:
            logger.warning("No data provided for prediction.")
            return np.array([])

        # Ensure 'timestamp' is datetime and sort
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Apply same feature engineering as training
        df = self.feature_engineer.create_time_features(df, 'timestamp')
        df = self.feature_engineer.create_lag_features(df, cols=[target_col], lags=[1, 2, 3, 7, 14])
        df = self.feature_engineer.create_rolling_features(df, cols=[target_col], windows=[7, 14], agg_funcs=['mean', 'std'])
        df = df.dropna().reset_index(drop=True) # Drop rows with NaN from lag/rolling features

        if df.empty:
            logger.warning("DataFrame became empty after feature engineering for prediction.")
            return np.array([])

        features = [col for col in df.columns if col not in [target_col, 'timestamp', '_id']]
        # Ensure features match what the model was trained on
        # This is a critical step for deployment: ensure consistency in feature columns
        # For simplicity, we assume the input df has all necessary features or can be engineered.
        # In a real system, you'd save feature names during training and validate here.
        # For now, let's just make sure we only select features that exist in the test data
        X = df[features]
        # Align columns if necessary (e.g., if some features are missing in prediction data)
        # For a robust solution, store trained features and reindex X here.
        # Example: X = X.reindex(columns=self.trained_features, fill_value=0)

        predictions = self.model.predict(X)
        logger.info(f"Generated {len(predictions)} predictions.")
        return predictions

    def forecast_future(self, historical_df: pd.DataFrame, horizon: int = settings.FORECAST_HORIZON, target_col: str = 'daily_revenue'):
        """
        Forecasts future values for a given horizon using the trained model.
        Requires enough historical data for lag and rolling features.
        """
        if not self.is_trained or self.model is None:
            logger.error("Forecasting model not trained. Cannot forecast future values.")
            raise ValueError("Model not trained.")
        if historical_df.empty:
            logger.warning("No historical data provided for forecasting.")
            return pd.DataFrame()

        # Ensure 'timestamp' is datetime and sort
        historical_df['timestamp'] = pd.to_datetime(historical_df['timestamp'])
        historical_df = historical_df.sort_values('timestamp').reset_index(drop=True)
        # Get the last known values for starting the forecast
        last_date = historical_df['timestamp'].max()
        last_target_value = historical_df[target_col].iloc[-1]

        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, horizon + 1)]
        forecast_df = pd.DataFrame({'timestamp': future_dates, target_col: 0.0}) # Placeholder target

        # Combine historical and future to create features for future predictions
        combined_df = pd.concat([historical_df, forecast_df], ignore_index=True)
        combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)

        # Apply same feature engineering as training
        combined_df = self.feature_engineer.create_time_features(combined_df, 'timestamp')
        combined_df = self.feature_engineer.create_lag_features(combined_df, cols=[target_col], lags=[1, 2, 3, 7, 14])
        combined_df = self.feature_engineer.create_rolling_features(combined_df, cols=[target_col], windows=[7, 14], agg_funcs=['mean', 'std'])

        # Replace NaN from lags with appropriate values for prediction (e.g., last known value)
        # For the very first rows, fill with 0 or a sensible default.
        combined_df = combined_df.fillna(0) # Or more sophisticated imputation

        # Identify rows for actual forecasting (the future dates)
        future_X = combined_df[combined_df['timestamp'].isin(future_dates)]
        
        if future_X.empty:
            logger.warning("Future data frame is empty after feature engineering for forecasting.")
            return pd.DataFrame()

        # Select features for prediction, ensuring they match training
        features = [col for col in future_X.columns if col not in [target_col, 'timestamp', '_id']]
        
        # This is where a more robust feature management would be needed.
        # For now, let's filter X to only contain features present in the original historical_df training set (minus target, timestamp, _id).
        # We need to ensure that the features array passed to predict contains *all* columns the model was trained on, in the correct order.
        # A common practice is to store the list of features used during training and reindex prediction data.
        
        # For this example, let's extract the feature columns from the future_X dataframe:
        X_predict = future_X[features] # This assumes `features` list contains all needed columns.
        
        # Make predictions
        future_predictions = self.model.predict(X_predict)

        # Assign predictions to the target column in the forecast_df
        forecast_df[target_col] = future_predictions

        logger.info(f"Generated {horizon} day forecast for '{target_col}'.")
        return forecast_df[['timestamp', target_col]]


    def save_model(self):
        """Saves the trained model and feature engineer (scalers/encoders)."""
        if self.model:
            os.makedirs(settings.MODEL_SAVE_PATH, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.feature_engineer, os.path.join(settings.MODEL_SAVE_PATH, f"forecasting_feature_engineer_{self.model_type}.joblib"))
            logger.info(f"Forecasting model and feature engineer saved to {self.model_path}")
        else:
            logger.warning("No forecasting model to save.")

    def load_model(self):
        """Loads the trained model and feature engineer."""
        try:
            self.model = joblib.load(self.model_path)
            self.feature_engineer = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, f"forecasting_feature_engineer_{self.model_type}.joblib"))
            self.is_trained = True
            logger.info(f"Forecasting model and feature engineer loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Forecasting model not found at {self.model_path}. Model needs to be trained.")
            self.is_trained = False
            return False
        except Exception as e:
            logger.error(f"Error loading forecasting model: {e}", exc_info=True)
            self.is_trained = False
            return False
```

### `./app/models/__init__.py`
```py

```

### `./app/models/model_manager.py`
```py
# ai_service/app/models/model_manager.py
import asyncio
from datetime import datetime
import pandas as pd
from app.config import settings
from app.utils.logger import logger
from app.database import get_database
from app.services.data_processor import DataProcessor
from app.models.forecasting import ForecastingModel
from app.models.anomaly_detection import AnomalyDetectionModel
from app.models.recommendation import RecommendationModel

class ModelManager:
    """
    Manages the lifecycle (initialization, training, loading, retraining) of all ML models.
    """
    _instance = None # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.forecasting_model = None
        self.anomaly_model = None
        self.recommendation_model = None
        self.db_connected = False
        self.models_loaded = False
        self.last_retrain_time = None
        self._initialized = True # Mark as initialized

    async def initialize_models(self):
        """
        Initializes and loads/trains all models. Called once at application startup.
        """
        logger.info("Initializing AI models...")
        # CORRECTED LINE: Check if async db object is not None
        self.db_connected = get_database() is not None

        # Initialize model instances
        self.forecasting_model = ForecastingModel()
        self.anomaly_model = AnomalyDetectionModel()
        self.recommendation_model = RecommendationModel()

        # Try to load models, if not found or training is forced, train them
        load_success_forecasting = self.forecasting_model.load_model()
        load_success_anomaly = self.anomaly_model.load_model()
        load_success_recommendation = self.recommendation_model.load_model()

        if load_success_forecasting and load_success_anomaly and load_success_recommendation:
            self.models_loaded = True
            logger.info("All models loaded successfully from disk.")
        else:
            logger.warning("One or more models not found or failed to load. Initiating initial training.")
            await self.train_all_models() # Perform initial training

        self.models_loaded = (getattr(self.forecasting_model, "is_trained", False) and
                              getattr(self.anomaly_model, "is_trained", False) and
                              getattr(self.recommendation_model, "is_trained", False))
        if not self.models_loaded:
            logger.error("Not all models are trained/ready after initialization phase.")

    async def train_all_models(self):
        """
        Orchestrates the training of all machine learning models.
        """
        if not self.db_connected:
            logger.error("Cannot train models: MongoDB connection not established.")
            return

        logger.info("Starting full model retraining process...")

        # Ensure model instances are initialized before training
        if self.forecasting_model is None:
            self.forecasting_model = ForecastingModel()
        if self.anomaly_model is None:
            self.anomaly_model = AnomalyDetectionModel()
        if self.recommendation_model is None:
            self.recommendation_model = RecommendationModel()

        try:
            # Use async db for data processor within FastAPI context
            data_processor = DataProcessor(db=get_database())

            # Train Forecasting Model
            logger.info("Training Forecasting Model...")
            transactions_df = await data_processor.get_transactions_data()
            daily_sales_df = data_processor.prepare_time_series_data(transactions_df, 'totalAmount', freq='D')
            if not daily_sales_df.empty:
                forecast_result = self.forecasting_model.train(daily_sales_df, target_col='totalAmount')
                logger.info(f"Forecasting Model training result: {forecast_result}")
            else:
                logger.warning("Skipping forecasting model training: No daily sales data.")

            # Train Anomaly Detection Model
            logger.info("Training Anomaly Detection Model...")
            anomaly_df = await data_processor.get_transactions_data()
            if not anomaly_df.empty:
                anomaly_features = ['totalAmount', 'quantity']
                anomaly_df['totalAmount'] = pd.to_numeric(anomaly_df['totalAmount'], errors='coerce').fillna(0)
                anomaly_df['quantity'] = pd.to_numeric(anomaly_df['quantity'], errors='coerce').fillna(0)
                valid_anomaly_features = [f for f in anomaly_features if f in anomaly_df.columns and pd.api.types.is_numeric_dtype(anomaly_df[f])]
                if not valid_anomaly_features:
                    logger.warning(f"No valid numeric features for anomaly detection training. Available numeric features: {[c for c in anomaly_df.columns if pd.api.types.is_numeric_dtype(anomaly_df[c])]}")
                else:
                    anomaly_result = self.anomaly_model.train(anomaly_df, features=valid_anomaly_features)
                    logger.info(f"Anomaly Detection Model training result: {anomaly_result}")
            else:
                logger.warning("Skipping anomaly detection model training: No transaction data for anomalies.")

            # Train Recommendation Model
            logger.info("Training Recommendation Model...")
            recommendation_result = await self.recommendation_model.train(data_processor)
            logger.info(f"Recommendation Model training result: {recommendation_result}")

            self.last_retrain_time = datetime.now()
            self.models_loaded = (getattr(self.forecasting_model, "is_trained", False) and
                                  getattr(self.anomaly_model, "is_trained", False) and
                                  getattr(self.recommendation_model, "is_trained", False))
            logger.info("Full model retraining process completed.")

        except Exception as e:
            logger.error(f"Error during full model retraining: {e}", exc_info=True)
            self.models_loaded = False # Mark models as not fully loaded on error

    async def schedule_retraining(self):
        """
        Schedules periodic retraining of all models.
        """
        while True:
            await asyncio.sleep(settings.RETRAIN_INTERVAL_HOURS * 3600) # Convert hours to seconds
            logger.info(f"Initiating scheduled retraining (every {settings.RETRAIN_INTERVAL_HOURS} hours)...")
            await self.train_all_models()
            if self.models_loaded:
                logger.info("Scheduled retraining completed successfully.")
            else:
                logger.error("Scheduled retraining encountered issues.")

# Create a singleton instance of ModelManager
model_manager = ModelManager()
```

### `./app/models/recommendation.py`
```py
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
import joblib
import os
from typing import Optional
from app.config import settings
from app.utils.logger import logger
from app.services.data_processor import DataProcessor

class RecommendationModel:
    """
    Implements a recommendation system using collaborative filtering (SVD).
    """
    def __init__(self, model_type: str = settings.RECOMMENDER_MODEL_TYPE, n_components: int = 50):
        self.model = None
        self.model_type = model_type
        self.n_components = n_components
        self.user_item_matrix = None # Stores the user-item interaction matrix
        self.user_mapper = {} # Map original user IDs to matrix indices
        self.item_mapper = {} # Map original item IDs to matrix indices
        self.user_inverse_mapper = {} # Map matrix indices back to original user IDs
        self.item_inverse_mapper = {} # Map matrix indices back to original item IDs
        self.model_path = os.path.join(settings.MODEL_SAVE_PATH, f"recommendation_model_{model_type}.joblib")
        self.is_trained = False

    async def train(self, data_processor: DataProcessor) -> dict:
        """
        Trains the recommendation model.
        Expects a DataProcessor instance to fetch user-item interaction data.
        """
        logger.info("Starting training for recommendation model...")
        self.user_item_matrix = await data_processor.get_user_item_matrix()

        if self.user_item_matrix.empty:
            logger.warning("No user-item interaction data to train recommendation model.")
            return {"status": "failed", "message": "No data for training."}

        # Create mappers for user and item IDs
        self.user_mapper = {user_id: idx for idx, user_id in enumerate(self.user_item_matrix.index)}
        self.item_mapper = {item_id: idx for idx, item_id in enumerate(self.user_item_matrix.columns)}
        self.user_inverse_mapper = {idx: user_id for user_id, idx in self.user_mapper.items()}
        self.item_inverse_mapper = {idx: item_id for item_id, idx in self.item_mapper.items()}

        # Convert to sparse matrix for SVD
        sparse_user_item = csr_matrix(self.user_item_matrix.values)

        if self.model_type == "SVD":
            self.model = TruncatedSVD(n_components=self.n_components, random_state=42)
            logger.info(f"Initialized TruncatedSVD with {self.n_components} components.")
        # elif self.model_type == "KNNWithMeans":
            # For KNN based models, you'd typically use surprise library or custom implementation
            # self.model = ...
        else:
            raise ValueError(f"Unsupported recommendation model type: {self.model_type}")

        self.model.fit(sparse_user_item)
        self.is_trained = True
        logger.info("Recommendation model training complete.")
        self.save_model()
        return {"status": "success", "message": "Recommendation model trained successfully."}

    def _get_popular_recommendations(self, num_recommendations: int = 10, product_data: Optional[pd.DataFrame] = None):
        """
        Provides general popular recommendations (e.g., for cold-start users).
        """
        logger.info("Providing popular recommendations (cold-start strategy).")
        if self.user_item_matrix is not None and not self.user_item_matrix.empty:
            # Sum interactions for each item
            item_popularity = self.user_item_matrix.sum(axis=0).sort_values(ascending=False)
            popular_item_ids = item_popularity.index.tolist()[:num_recommendations]
            
            # If product_data is available, try to get names
            if product_data is not None and not product_data.empty:
                popular_products_info = product_data[product_data['productId'].isin(popular_item_ids)]
                return popular_products_info[['productId', 'productName']].to_dict(orient='records')
            return [{"productId": pid} for pid in popular_item_ids]
        
        logger.warning("No user-item matrix available to determine popularity. Returning empty list.")
        return []

    async def get_user_recommendations(self, user_id: str, num_recommendations: int = 10, product_data: Optional[pd.DataFrame] = None):
        """
        Generates personalized product recommendations for a given user.
        """
        if not self.is_trained or self.model is None or self.user_item_matrix is None:
            logger.warning("Recommendation model not trained or data not loaded. Providing popular recommendations.")
            return self._get_popular_recommendations(num_recommendations, product_data)

        if user_id not in self.user_mapper:
            logger.warning(f"User {user_id} not found in training data. Providing popular recommendations.")
            return self._get_popular_recommendations(num_recommendations, product_data)

        user_idx = self.user_mapper[user_id]
        user_vector = self.user_item_matrix.iloc[user_idx]

        # Reconstruct the original matrix from SVD components (approximation)
        if self.model_type == "SVD":
            reconstructed_matrix = np.dot(self.model.transform(csr_matrix(self.user_item_matrix.values)), self.model.components_)
            # Convert back to DataFrame for easy indexing
            reconstructed_df = pd.DataFrame(reconstructed_matrix, index=self.user_item_matrix.index, columns=self.user_item_matrix.columns)
            
            # Get predicted ratings for the user
            user_predicted_ratings = reconstructed_df.loc[user_id]

            # Filter out items the user has already interacted with
            user_interacted_items = user_vector[user_vector > 0].index
            recommendations_series = user_predicted_ratings.drop(user_interacted_items, errors='ignore')

            # Sort and get top N recommendations
            if isinstance(recommendations_series, pd.Series):
                top_recommendations = recommendations_series.sort_values(ascending=False).head(num_recommendations).index.tolist()
            else:
                # Convert to Series if not already
                # If recommendations_series is a DataFrame, select the first row as a Series
                if isinstance(recommendations_series, pd.DataFrame):
                    recommendations_series = recommendations_series.iloc[0]
                top_recommendations = recommendations_series.sort_values(ascending=False).head(num_recommendations).index.tolist()
        else:
            logger.warning(f"Recommendation type {self.model_type} not fully implemented for prediction logic. Returning popular.")
            return self._get_popular_recommendations(num_recommendations, product_data)

        logger.info(f"Generated {len(top_recommendations)} recommendations for user {user_id}.")
        
        # Fetch product details if product_data is available
        if product_data is not None and not product_data.empty:
            recommended_products_info = product_data[product_data['productId'].isin(top_recommendations)]
            # Ensure order based on ranking
            product_dict = recommended_products_info.set_index('productId').T.to_dict('list')
            ordered_recommendations = []
            for prod_id in top_recommendations:
                if prod_id in product_dict:
                    ordered_recommendations.append({"productId": prod_id, "productName": product_dict[prod_id][0]}) # Assuming productName is first item
            return ordered_recommendations
        
        return [{"productId": pid} for pid in top_recommendations]


    def save_model(self):
        """Saves the trained model, user-item matrix, and mappers."""
        if self.model:
            os.makedirs(settings.MODEL_SAVE_PATH, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.user_item_matrix, os.path.join(settings.MODEL_SAVE_PATH, "user_item_matrix.joblib"))
            joblib.dump(self.user_mapper, os.path.join(settings.MODEL_SAVE_PATH, "user_mapper.joblib"))
            joblib.dump(self.item_mapper, os.path.join(settings.MODEL_SAVE_PATH, "item_mapper.joblib"))
            joblib.dump(self.user_inverse_mapper, os.path.join(settings.MODEL_SAVE_PATH, "user_inverse_mapper.joblib"))
            joblib.dump(self.item_inverse_mapper, os.path.join(settings.MODEL_SAVE_PATH, "item_inverse_mapper.joblib"))
            logger.info(f"Recommendation model and associated data saved to {self.model_path}")
        else:
            logger.warning("No recommendation model to save.")

    def load_model(self):
        """Loads the trained model, user-item matrix, and mappers."""
        try:
            self.model = joblib.load(self.model_path)
            self.user_item_matrix = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "user_item_matrix.joblib"))
            self.user_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "user_mapper.joblib"))
            self.item_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "item_mapper.joblib"))
            self.user_inverse_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "user_inverse_mapper.joblib"))
            self.item_inverse_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "item_inverse_mapper.joblib"))
            self.is_trained = True
            logger.info(f"Recommendation model and associated data loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Recommendation model not found at {self.model_path}. Model needs to be trained.")
            self.is_trained = False
            return False
        except Exception as e:
            logger.error(f"Error loading recommendation model: {e}", exc_info=True)
            self.is_trained = False
            return False
```

### `./app/services/data_processor.py`
```py
from datetime import datetime, timedelta
import pandas as pd
from app.config import settings
from app.utils.logger import logger
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.mongo_client import MongoClient

class DataProcessor:
    """
    Handles fetching and initial processing of raw data from MongoDB.
    """
    def __init__(self, db: AsyncIOMotorDatabase = None, sync_db: MongoClient = None): # type: ignore
        self._db = db
        self._sync_db = sync_db # For synchronous operations if needed

        if not self._db and not self._sync_db:
            raise ValueError("Either an async or a sync database connection must be provided.")

    def _get_db_client(self):
        """Returns the appropriate database client based on context."""
        if self._db:
            return self._db
        elif self._sync_db:
            return self._sync_db
        else:
            raise RuntimeError("No database client available.")

    async def get_transactions_data(self, days: int = settings.DATA_COLLECTION_DAYS) -> pd.DataFrame:
        """
        Fetches transaction data for a specified number of past days.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Fetching transaction data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        try:
            # Use async db client
            transactions_cursor = self._get_db_client().transactions.find(
                {"timestamp": {"$gte": start_date, "$lte": end_date}}
            )
            transactions_list = await transactions_cursor.to_list(length=None) # Fetch all documents

            if not transactions_list:
                logger.warning(f"No transaction data found for the last {days} days.")
                return pd.DataFrame()

            df = pd.DataFrame(transactions_list)

            # Convert timestamp to datetime and sort
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)

            logger.info(f"Fetched {len(df)} transactions.")
            return df

        except Exception as e:
            logger.error(f"Error fetching transaction data: {e}", exc_info=True)
            return pd.DataFrame()

    async def get_user_behavior_data(self, days: int = settings.DATA_COLLECTION_DAYS) -> pd.DataFrame:
        """
        Fetches user activity and feedback data for a specified number of past days.
        Combines user_activities and feedback collections.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Fetching user behavior data (activities and feedback) from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        try:
            # Fetch user activities (using correct collection name 'user_activities')
            activities_cursor = self._get_db_client().user_activities.find(
                {"timestamp": {"$gte": start_date, "$lte": end_date}}
            )
            activities_list = await activities_cursor.to_list(length=None)
            activities_df = pd.DataFrame(activities_list)

            # Fetch feedback (using correct collection name 'feedback')
            feedback_cursor = self._get_db_client().feedback.find(
                {"timestamp": {"$gte": start_date, "$lte": end_date}}
            )
            feedback_list = await feedback_cursor.to_list(length=None)
            feedback_df = pd.DataFrame(feedback_list)

            if not activities_list and not feedback_list:
                logger.warning(f"No user activity or feedback data found for the last {days} days.")
                return pd.DataFrame()

            # Combine and process
            combined_df = pd.concat([activities_df, feedback_df], ignore_index=True)
            if not combined_df.empty:
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
            else:
                return pd.DataFrame()

            logger.info(f"Fetched {len(activities_df)} activities and {len(feedback_df)} feedback entries.")
            return combined_df

        except Exception as e:
            logger.error(f"Error fetching user behavior data: {e}", exc_info=True)
            return pd.DataFrame()


    async def get_product_data(self) -> pd.DataFrame:
        """
        Fetches product data.
        """
        logger.info("Fetching product data.")
        try:
            products_cursor = self._get_db_client().products.find({})
            products_list = await products_cursor.to_list(length=None)

            if not products_list:
                logger.warning("No product data found.")
                return pd.DataFrame()

            df = pd.DataFrame(products_list)
            logger.info(f"Fetched {len(df)} products.")
            return df
        except Exception as e:
            logger.error(f"Error fetching product data: {e}", exc_info=True)
            return pd.DataFrame()

    def prepare_time_series_data(self, df: pd.DataFrame, value_col: str, freq: str = 'D') -> pd.DataFrame:
        """
        Prepares time series data (e.g., daily sales) from a DataFrame.
        Assumes 'timestamp' column exists.
        """
        if df.empty:
            logger.warning("Input DataFrame is empty for time series preparation.")
            return pd.DataFrame()

        df_ts = df.set_index('timestamp').resample(freq)[value_col].sum().fillna(0).to_frame()
        df_ts.columns = [value_col]
        df_ts = df_ts.reset_index()
        logger.info(f"Prepared time series data with frequency '{freq}' for '{value_col}'. Rows: {len(df_ts)}")
        return df_ts

    async def get_user_item_matrix(self, min_interactions: int = settings.MIN_INTERACTIONS_FOR_RECOMMENDATION) -> pd.DataFrame:
        """
        Generates a user-item interaction matrix from transaction data.
        Filters out users/items with too few interactions.
        """
        logger.info("Generating user-item interaction matrix...")
        try:
            transactions_df = await self.get_transactions_data(days=settings.DATA_COLLECTION_DAYS)
            if transactions_df.empty:
                logger.warning("No transactions data to build user-item matrix.")
                return pd.DataFrame()

            # Ensure correct data types
            transactions_df['userId'] = transactions_df['userId'].astype(str)
            transactions_df['productId'] = transactions_df['productId'].astype(str)
            transactions_df['quantity'] = transactions_df['quantity'].astype(int)

            # Aggregate quantity per user-product pair (implicit rating)
            user_item_interactions = transactions_df.groupby(['userId', 'productId'])['quantity'].sum().reset_index()
            user_item_interactions.rename(columns={'quantity': 'interaction_count'}, inplace=True)

            # Filter out users with too few interactions (optional, for cold-start or noise)
            user_counts = user_item_interactions.groupby('userId').size()
            valid_users = user_counts[user_counts >= min_interactions].index
            user_item_interactions = user_item_interactions[user_item_interactions['userId'].isin(valid_users)]

            if user_item_interactions.empty:
                logger.warning(f"No sufficient user-item interactions after filtering for min_interactions={min_interactions}.")
                return pd.DataFrame()

            # Create pivot table (user-item matrix)
            user_item_matrix = user_item_interactions.pivot_table(
                index='userId',
                columns='productId',
                values='interaction_count'
            ).fillna(0) # Fill NaN with 0 for no interaction

            logger.info(f"Generated user-item matrix with shape: {user_item_matrix.shape}")
            return user_item_matrix

        except Exception as e:
            logger.error(f"Error generating user-item matrix: {e}", exc_info=True)
            return pd.DataFrame()
```

### `./app/services/feature_engineering.py`
```py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from app.utils.logger import logger

class FeatureEngineer:
    """
    Handles feature engineering for machine learning models.
    """
    def __init__(self):
        self.scalers = {} # To store scalers for different features
        self.encoders = {} # To store encoders for categorical features

    def create_time_features(self, df: pd.DataFrame, timestamp_col: str = 'timestamp') -> pd.DataFrame:
        """
        Creates time-based features from a timestamp column.
        Expects timestamp_col to be datetime objects.
        """
        if df.empty or timestamp_col not in df.columns:
            logger.warning("DataFrame is empty or timestamp_col not found for time features.")
            return df

        df['year'] = df[timestamp_col].dt.year
        df['month'] = df[timestamp_col].dt.month
        df['day'] = df[timestamp_col].dt.day
        df['day_of_week'] = df[timestamp_col].dt.dayofweek
        df['day_of_year'] = df[timestamp_col].dt.dayofyear
        df['week_of_year'] = df[timestamp_col].dt.isocalendar().week.astype(int)
        df['hour'] = df[timestamp_col].dt.hour
        df['quarter'] = df[timestamp_col].dt.quarter
        df['is_weekend'] = ((df[timestamp_col].dt.dayofweek == 5) | (df[timestamp_col].dt.dayofweek == 6)).astype(int)
        df['is_month_start'] = df[timestamp_col].dt.is_month_start.astype(int)
        df['is_month_end'] = df[timestamp_col].dt.is_month_end.astype(int)

        logger.info(f"Created time features for DataFrame with {len(df)} rows.")
        return df

    def create_lag_features(self, df: pd.DataFrame, cols: list, lags: list) -> pd.DataFrame:
        """
        Creates lag features for specified columns.
        Expects df to be sorted by time.
        """
        if df.empty:
            logger.warning("DataFrame is empty for lag feature creation.")
            return df
        if not all(col in df.columns for col in cols):
            logger.error(f"One or more columns {cols} not found for lag features.")
            return df

        for col in cols:
            for lag in lags:
                df[f'{col}_lag_{lag}'] = df[col].shift(lag)
        df = df.fillna(0) # Fill NaN from shifting
        logger.info(f"Created lag features for columns {cols} with lags {lags}.")
        return df

    def create_rolling_features(self, df: pd.DataFrame, cols: list, windows: list, agg_funcs: list) -> pd.DataFrame:
        """
        Creates rolling window features for specified columns.
        Expects df to be sorted by time.
        """
        if df.empty:
            logger.warning("DataFrame is empty for rolling feature creation.")
            return df
        if not all(col in df.columns for col in cols):
            logger.error(f"One or more columns {cols} not found for rolling features.")
            return df

        for col in cols:
            for window in windows:
                for agg_func in agg_funcs:
                    if agg_func == 'mean':
                        df[f'{col}_roll_mean_{window}'] = df[col].rolling(window=window).mean()
                    elif agg_func == 'std':
                        df[f'{col}_roll_std_{window}'] = df[col].rolling(window=window).std()
                    elif agg_func == 'min':
                        df[f'{col}_roll_min_{window}'] = df[col].rolling(window=window).min()
                    elif agg_func == 'max':
                        df[f'{col}_roll_max_{window}'] = df[col].rolling(window=window).max()
        df = df.fillna(0) # Fill NaN from rolling
        logger.info(f"Created rolling features for columns {cols} with windows {windows} and funcs {agg_funcs}.")
        return df

    def create_anomaly_features(self, df: pd.DataFrame, value_col: str) -> pd.DataFrame:
        """
        Creates simple anomaly-related features (e.g., deviation from mean).
        """
        if df.empty or value_col not in df.columns:
            logger.warning("DataFrame is empty or value_col not found for anomaly features.")
            return df

        df[f'{value_col}_daily_mean'] = df[value_col].rolling(window=7, min_periods=1).mean()
        df[f'{value_col}_daily_std'] = df[value_col].rolling(window=7, min_periods=1).std()
        df[f'{value_col}_deviation'] = df[value_col] - df[f'{value_col}_daily_mean']
        df[f'{value_col}_zscore'] = df[f'{value_col}_deviation'] / df[f'{value_col}_daily_std'].replace(0, 1) # Avoid div by zero
        df = df.fillna(0)
        logger.info(f"Created anomaly features for '{value_col}'.")
        return df

    def scale_features(self, df: pd.DataFrame, cols: list, scaler_type: str = 'StandardScaler', fit: bool = True) -> pd.DataFrame:
        """
        Scales numerical features.
        :param df: DataFrame to scale.
        :param cols: List of columns to scale.
        :param scaler_type: Type of scaler ('StandardScaler' or 'MinMaxScaler').
        :param fit: If True, fit the scaler; if False, transform using existing scaler.
        """
        if df.empty or not cols or not all(col in df.columns for col in cols):
            logger.warning(f"DataFrame empty or columns missing for scaling: {cols}.")
            return df

        for col in cols:
            if fit:
                if scaler_type == 'StandardScaler':
                    scaler = StandardScaler()
                elif scaler_type == 'MinMaxScaler':
                    scaler = MinMaxScaler()
                else:
                    raise ValueError("scaler_type must be 'StandardScaler' or 'MinMaxScaler'")
                df[col] = scaler.fit_transform(df[[col]])
                self.scalers[col] = scaler
                logger.info(f"Fitted and scaled '{col}' with {scaler_type}.")
            else:
                if col in self.scalers:
                    df[col] = self.scalers[col].transform(df[[col]])
                    logger.info(f"Transformed '{col}' with existing {scaler_type}.")
                else:
                    logger.warning(f"No scaler found for '{col}', skipping transformation.")
        return df

    def encode_categorical_features(self, df: pd.DataFrame, cols: list, encoder_type: str = 'LabelEncoder', fit: bool = True) -> pd.DataFrame:
        """
        Encodes categorical features. Supports LabelEncoder for simplicity.
        :param df: DataFrame to encode.
        :param cols: List of columns to encode.
        :param encoder_type: Type of encoder ('LabelEncoder').
        :param fit: If True, fit the encoder; if False, transform using existing encoder.
        """
        if df.empty or not cols or not all(col in df.columns for col in cols):
            logger.warning(f"DataFrame empty or columns missing for encoding: {cols}.")
            return df

        for col in cols:
            if encoder_type == 'LabelEncoder':
                if fit:
                    encoder = LabelEncoder()
                    df[col] = encoder.fit_transform(df[col])
                    self.encoders[col] = encoder
                    logger.info(f"Fitted and encoded '{col}' with LabelEncoder.")
                else:
                    if col in self.encoders:
                        # Handle unseen labels during transformation
                        # Replace unseen labels with a placeholder (e.g., -1) or the most frequent label
                        # Here, we'll assign -1 for simplicity
                        unseen_labels = set(df[col].unique()) - set(self.encoders[col].classes_)
                        if unseen_labels:
                            logger.warning(f"Unseen labels detected in column '{col}': {unseen_labels}. Assigning -1.")
                            df[col] = df[col].apply(lambda x: self.encoders[col].transform([x])[0] if x in self.encoders[col].classes_ else -1)
                        else:
                            df[col] = self.encoders[col].transform(df[col])
                        logger.info(f"Transformed '{col}' with existing LabelEncoder.")
                    else:
                        logger.warning(f"No encoder found for '{col}', skipping transformation.")
            else:
                raise ValueError("encoder_type must be 'LabelEncoder'")
        return df

    def get_features_and_target(self, df: pd.DataFrame, target_col: str, feature_cols: list = None):
        """
        Separates features (X) and target (y) from a DataFrame.
        """
        if df.empty or target_col not in df.columns:
            logger.error(f"DataFrame empty or target column '{target_col}' not found for feature/target split.")
            return pd.DataFrame(), pd.Series()

        if feature_cols:
            X = df[feature_cols]
        else:
            X = df.drop(columns=[target_col], errors='ignore')
        y = df[target_col]

        logger.info(f"Separated features (X shape: {X.shape}) and target (y shape: {y.shape}).")
        return X, y
```

### `./app/services/__init__.py`
```py

```

### `./app/utils/__init__.py`
```py

```

### `./app/utils/logger.py`
```py
import os
from loguru import logger as loguru_logger
from datetime import datetime

# Remove default handler to avoid duplicate logs
loguru_logger.remove()

# Configure logger for console output
loguru_logger.add(
    sink="sys.stdout",
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
    diagnose=True
)

# Configure logger for file output
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file_path = os.path.join(LOG_DIR, f"ai_service_{datetime.now().strftime('%Y-%m-%d')}.log")

loguru_logger.add(
    sink=log_file_path,
    rotation="1 day",  # New log file every day
    retention="7 days", # Keep logs for 7 days
    compression="zip",  # Compress old log files
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    diagnose=True
)

# Expose loguru_logger as 'logger' for easy import
logger = loguru_logger
```

### `./Dockerfile`
```Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `./tests/__init__.py`
```py

```


```

### `./app/api/dependencies.py`
```py
from app.database import get_database
from app.models.model_manager import ModelManager
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from app.utils.logger import logger

def get_db() -> AsyncIOMotorDatabase:
    """
    Dependency to get the MongoDB database instance.
    """
    db = get_database()
    if not db:
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
```

### `./app/api/__init__.py`
```py

```

### `./app/api/routes/anomaly.py`
```py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.models.model_manager import ModelManager
from app.services.data_processor import DataProcessor
from app.utils.logger import logger
from app.api.dependencies import get_db, get_model_manager
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta

router = APIRouter()

class AnomalyDetectionRequest(BaseModel):
    data_points: List[Dict[str, Any]] = Field(
        ...,
        description="List of data points to check for anomalies. Each dict should contain features used for training (e.g., 'totalAmount', 'quantity')."
    )
    # You might want to allow specifying features dynamically or assume they are pre-defined
    # For now, let's assume they are predefined in the model's training process
    features: List[str] = Field(
        ["totalAmount", "quantity"], # Default example features
        description="List of features to use for anomaly detection. Must match features used during training."
    )

class AnomalyResponse(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    data: Dict[str, Any]
    details: Dict[str, Any]

@router.post("/train", summary="Trigger training for the anomaly detection model")
async def train_anomaly_model(
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually triggers the training process for the anomaly detection model.
    It uses recent transaction data to train the model.
    """
    logger.info("API call: /anomaly/train received.")
    try:
        data_processor = DataProcessor(db=db)
        transactions_df = await data_processor.get_transactions_data()

        if transactions_df.empty:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sufficient data available for anomaly detection model training.")

        # Prepare features for anomaly detection (example: totalAmount, quantity)
        # Ensure numerical columns
        transactions_df['totalAmount'] = pd.to_numeric(transactions_df['totalAmount'], errors='coerce').fillna(0)
        transactions_df['quantity'] = pd.to_numeric(transactions_df['quantity'], errors='coerce').fillna(0)
        
        # Define features. These should align with what the model expects.
        anomaly_features = ["totalAmount", "quantity"]
        valid_anomaly_features = [f for f in anomaly_features if f in transactions_df.columns and pd.api.types.is_numeric_dtype(transactions_df[f])]

        if not valid_anomaly_features:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid numerical features found for anomaly detection training.")

        result = model_manager.anomaly_model.train(transactions_df, features=valid_anomaly_features)
        if result.get("status") == "success":
            return {"message": "Anomaly detection model training initiated successfully.", "metrics": result.get("metrics")}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Anomaly detection model training failed."))
    except Exception as e:
        logger.error(f"Error during anomaly model training API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during training: {e}")


@router.post("/detect", summary="Detect anomalies in provided data points", response_model=List[AnomalyResponse])
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Detects anomalies in a list of incoming data points.
    Each data point should be a dictionary containing the features used to train the anomaly model.
    """
    logger.info(f"API call: /anomaly/detect received for {len(request.data_points)} data points.")
    if not model_manager.anomaly_model.is_trained:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Anomaly detection model is not trained yet. Please train it first.")

    if not request.data_points:
        return []

    try:
        df = pd.DataFrame(request.data_points)
        # Ensure numerical columns for detection
        for col in request.features:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                logger.warning(f"Feature '{col}' not found in input data points for anomaly detection.")
                # You might want to raise an error or fill with a default value
                df[col] = 0 # Add missing feature with default 0


        detected_df = model_manager.anomaly_model.detect_anomalies(df.copy(), features=request.features)
        
        results = []
        for index, row in detected_df.iterrows():
            result = AnomalyResponse(
                is_anomaly=bool(row['is_anomaly']),
                anomaly_score=float(row['anomaly_score']),
                data={k: v for k, v in row.items() if k not in ['is_anomaly', 'anomaly_score']}, # All other fields
                details={feat: row[feat] for feat in request.features if feat in row} # Only anomaly features
            )
            results.append(result)
        
        return results

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error during anomaly detection API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during detection: {e}")


@router.get("/status", summary="Get anomaly detection model status")
async def get_anomaly_model_status(model_manager: ModelManager = Depends(get_model_manager)):
    """
    Returns the current training status and metrics of the anomaly detection model.
    """
    status_info = {
        "is_trained": model_manager.anomaly_model.is_trained,
        "model_type": model_manager.anomaly_model.model_type,
        "contamination_threshold": model_manager.anomaly_model.contamination,
        "metrics": model_manager.anomaly_model.metrics,
        "last_retrain_time": model_manager.last_retrain_time.isoformat() if model_manager.last_retrain_time else "N/A"
    }
    return status_info
```

### `./app/api/routes/forecast.py`
```py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.model_manager import ModelManager
from app.services.data_processor import DataProcessor
from app.utils.logger import logger
from app.api.dependencies import get_db, get_model_manager
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/train", summary="Trigger training for the forecasting model")
async def train_forecasting_model(
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually triggers the training process for the sales forecasting model.
    """
    logger.info("API call: /forecast/train received.")
    try:
        data_processor = DataProcessor(db=db)
        transactions_df = await data_processor.get_transactions_data()
        daily_sales_df = data_processor.prepare_time_series_data(transactions_df, 'totalAmount', freq='D')

        if daily_sales_df.empty:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sufficient data available for forecasting model training.")

        result = model_manager.forecasting_model.train(daily_sales_df, target_col='totalAmount')
        if result.get("status") == "success":
            return {"message": "Forecasting model training initiated successfully.", "metrics": result.get("metrics")}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Forecasting model training failed."))
    except Exception as e:
        logger.error(f"Error during forecasting model training API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during training: {e}")

@router.get("/predict", summary="Get sales forecast for the next N days")
async def get_sales_forecast(
    horizon: int = Query(7, ge=1, le=30, description="Number of days to forecast into the future"),
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Retrieves the sales forecast for the specified number of days.
    The model must be trained before predictions can be made.
    """
    logger.info(f"API call: /forecast/predict for {horizon} days received.")
    if not model_manager.forecasting_model.is_trained:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Forecasting model is not trained yet. Please train it first.")

    try:
        data_processor = DataProcessor(db=db)
        # Fetch recent historical data to generate features for forecasting
        historical_transactions_df = await data_processor.get_transactions_data(days=model_manager.forecasting_model.feature_engineer.create_lag_features.__defaults__[1][-1] + 30) # Enough days for lags + some buffer
        historical_daily_sales_df = data_processor.prepare_time_series_data(historical_transactions_df, 'totalAmount', freq='D')

        if historical_daily_sales_df.empty:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enough historical data to generate forecast.")

        forecast_df = model_manager.forecasting_model.forecast_future(
            historical_daily_sales_df,
            horizon=horizon,
            target_col='totalAmount'
        )
        
        if forecast_df.empty:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate forecast, resulting DataFrame is empty.")

        # Format output
        forecast_data = forecast_df.rename(columns={'timestamp': 'date', 'totalAmount': 'predicted_sales'}).to_dict(orient='records')
        # Convert datetime objects to ISO format strings
        for item in forecast_data:
            item['date'] = item['date'].isoformat().split('T')[0] # Get only date part

        return {"message": "Sales forecast generated successfully", "forecast": forecast_data}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error during sales forecast prediction API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during prediction: {e}")

@router.get("/status", summary="Get forecasting model status")
async def get_forecasting_model_status(model_manager: ModelManager = Depends(get_model_manager)):
    """
    Returns the current training status and metrics of the forecasting model.
    """
    status_info = {
        "is_trained": model_manager.forecasting_model.is_trained,
        "model_type": model_manager.forecasting_model.model_type,
        "metrics": model_manager.forecasting_model.metrics,
        "last_retrain_time": model_manager.last_retrain_time.isoformat() if model_manager.last_retrain_time else "N/A"
    }
    return status_info
```

### `./app/api/routes/health.py`
```py
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
```

### `./app/api/routes/__init__.py`
```py

```

### `./app/api/routes/recommend.py`
```py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any
from app.models.model_manager import ModelManager
from app.services.data_processor import DataProcessor
from app.utils.logger import logger
from app.api.dependencies import get_db, get_model_manager
from motor.motor_asyncio import AsyncIOMotorDatabase
import pandas as pd # Import pandas for DataFrame handling if needed

router = APIRouter()

@router.post("/train", summary="Trigger training for the recommendation model")
async def train_recommendation_model(
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually triggers the training process for the recommendation model.
    It uses transaction data to build the user-item interaction matrix.
    """
    logger.info("API call: /recommend/train received.")
    try:
        data_processor = DataProcessor(db=db)
        result = await model_manager.recommendation_model.train(data_processor)
        if result.get("status") == "success":
            return {"message": "Recommendation model training initiated successfully."}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Recommendation model training failed."))
    except Exception as e:
        logger.error(f"Error during recommendation model training API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during training: {e}")


@router.get("/user/{user_id}", summary="Get personalized product recommendations for a user")
async def get_user_recommendations(
    user_id: str,
    num_recommendations: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Retrieves personalized product recommendations for a specific user.
    If the user is new (cold-start) or model is not trained, returns popular products.
    """
    logger.info(f"API call: /recommend/user/{user_id} received for {num_recommendations} recommendations.")
    
    # Check if model is trained, if not, it will default to popular items
    if not model_manager.recommendation_model.is_trained:
        logger.warning("Recommendation model is not trained. Providing popular recommendations.")
        data_processor = DataProcessor(db=db)
        product_df = await data_processor.get_product_data()
        popular_recommendations = model_manager.recommendation_model._get_popular_recommendations(num_recommendations, product_data=product_df)
        return {"message": "Recommendation model not trained, returned popular items.", "recommendations": popular_recommendations}

    try:
        data_processor = DataProcessor(db=db)
        product_df = await data_processor.get_product_data() # Fetch product details for richer recommendations
        
        recommendations = await model_manager.recommendation_model.get_user_recommendations(
            user_id, num_recommendations, product_data=product_df
        )
        
        if not recommendations:
            # If personalized recommendations fail, fall back to popular
            popular_recommendations = model_manager.recommendation_model._get_popular_recommendations(num_recommendations, product_data=product_df)
            return {"message": f"No personalized recommendations found for user {user_id}. Returning popular items.", "recommendations": popular_recommendations}

        return {"message": f"Recommendations for user {user_id} generated successfully.", "recommendations": recommendations}
    except Exception as e:
        logger.error(f"Error during recommendation API call for user {user_id}: {e}", exc_info=True)
        # Fallback to popular recommendations in case of critical error
        try:
            data_processor = DataProcessor(db=db)
            product_df = await data_processor.get_product_data()
            popular_recommendations = model_manager.recommendation_model._get_popular_recommendations(num_recommendations, product_data=product_df)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"message": f"Internal server error, falling back to popular recommendations: {e}", "recommendations": popular_recommendations})
        except Exception as fallback_e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during recommendation: {e}. Fallback also failed: {fallback_e}")


@router.get("/status", summary="Get recommendation model status")
async def get_recommendation_model_status(model_manager: ModelManager = Depends(get_model_manager)):
    """
    Returns the current training status of the recommendation model.
    """
    status_info = {
        "is_trained": model_manager.recommendation_model.is_trained,
        "model_type": model_manager.recommendation_model.model_type,
        "n_components": model_manager.recommendation_model.n_components,
        "last_retrain_time": model_manager.last_retrain_time.isoformat() if model_manager.last_retrain_time else "N/A"
    }
    return status_info
```

### `./app/config.py`
```py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration class for the AI microservice.
    Loads settings from environment variables.
    """
    APP_NAME: str = "Adaptive BI AI Service"
    APP_VERSION: str = "1.0.0"

    # Server settings
    HOST: str = os.getenv("AI_SERVICE_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("AI_SERVICE_PORT", 8000))
    DEBUG: bool = os.getenv("AI_SERVICE_DEBUG", "False").lower() == "true"

    # MongoDB settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/adaptive_bi")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "adaptive_bi")

    # JWT settings (if used for internal service communication)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your_strong_jwt_secret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # Model settings
    MODEL_SAVE_PATH: str = os.getenv("MODEL_SAVE_PATH", "/app/models/saved_models")
    RETRAIN_INTERVAL_HOURS: int = int(os.getenv("RETRAIN_INTERVAL_HOURS", 24))

    # Forecasting Model Parameters
    FORECAST_HORIZON: int = int(os.getenv("FORECAST_HORIZON", 7)) # Days to forecast
    FORECAST_MODEL_TYPE: str = os.getenv("FORECAST_MODEL_TYPE", "RandomForestRegressor") # RandomForestRegressor or LinearRegression

    # Anomaly Detection Model Parameters
    ANOMALY_THRESHOLD: float = float(os.getenv("ANOMALY_THRESHOLD", 0.05)) # For IsolationForest, contamination
    ANOMALY_MODEL_TYPE: str = os.getenv("ANOMALY_MODEL_TYPE", "IsolationForest") # IsolationForest or OneClassSVM

    # Recommendation Model Parameters
    MIN_INTERACTIONS_FOR_RECOMMENDATION: int = int(os.getenv("MIN_INTERACTIONS_FOR_RECOMMENDATION", 5))
    RECOMMENDER_MODEL_TYPE: str = os.getenv("RECOMMENDER_MODEL_TYPE", "SVD") # SVD or KNNWithMeans

    # Data collection window for training
    DATA_COLLECTION_DAYS: int = int(os.getenv("DATA_COLLECTION_DAYS", 90)) # Data from last 90 days for training

    # CORS settings
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",") # Allows all origins for development

    def __init__(self):
        # Ensure model save path exists
        if not os.path.exists(self.MODEL_SAVE_PATH):
            os.makedirs(self.MODEL_SAVE_PATH)

    def display_config(self):
        """Prints the current configuration (excluding sensitive info)."""
        print("\n--- AI Service Configuration ---")
        print(f"App Name: {self.APP_NAME}")
        print(f"Version: {self.APP_VERSION}")
        print(f"Host: {self.HOST}, Port: {self.PORT}")
        print(f"Debug Mode: {self.DEBUG}")
        print(f"MongoDB URL: {self.MONGODB_URL.split('@')[-1] if '@' in self.MONGODB_URL else self.MONGODB_URL}") # Mask password
        print(f"Database Name: {self.DATABASE_NAME}")
        print(f"Model Save Path: {self.MODEL_SAVE_PATH}")
        print(f"Retrain Interval (Hours): {self.RETRAIN_INTERVAL_HOURS}")
        print(f"Forecast Horizon (Days): {self.FORECAST_HORIZON}")
        print(f"Anomaly Threshold: {self.ANOMALY_THRESHOLD}")
        print(f"Data Collection Days: {self.DATA_COLLECTION_DAYS}")
        print(f"CORS Origins: {self.CORS_ORIGINS}")
        print("--------------------------------\n")

# Instantiate config
settings = Config()

if __name__ == "__main__":
    settings.display_config()
```

### `./app/database.py`
```py
import motor.motor_asyncio
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import settings
from app.utils.logger import logger

# Async MongoDB client for FastAPI
client = None
db = None

# Synchronous MongoDB client for model training scripts (if needed outside FastAPI context)
sync_client = None
sync_db = None

async def connect_to_database():
    """
    Establishes an asynchronous connection to MongoDB.
    """
    global client, db
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        # The ping command is cheap and does not require auth.
        await db.command('ping')
        logger.info(f"Successfully connected to MongoDB at {settings.MONGODB_URL.split('@')[-1]}")
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed (ConnectionFailure): {e}")
        # Optionally re-raise or exit if DB is critical for startup
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during MongoDB connection: {e}")
        raise

async def close_database_connection():
    """
    Closes the asynchronous MongoDB connection.
    """
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    """
    Returns the asynchronous MongoDB database instance.
    """
    return db

def connect_to_sync_database():
    """
    Establishes a synchronous connection to MongoDB.
    Used for scripts that might not run within an async context directly.
    """
    global sync_client, sync_db
    try:
        sync_client = MongoClient(settings.MONGODB_URL)
        sync_db = sync_client[settings.DATABASE_NAME]
        sync_db.command('ping') # Test connection
        logger.info(f"Successfully connected to synchronous MongoDB at {settings.MONGODB_URL.split('@')[-1]}")
    except ConnectionFailure as e:
        logger.error(f"Synchronous MongoDB connection failed (ConnectionFailure): {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during synchronous MongoDB connection: {e}")
        raise

def close_sync_database_connection():
    """
    Closes the synchronous MongoDB connection.
    """
    global sync_client
    if sync_client:
        sync_client.close()
        logger.info("Synchronous MongoDB connection closed.")

def get_sync_database():
    """
    Returns the synchronous MongoDB database instance.
    """
    return sync_db

if __name__ == "__main__":
    import asyncio

    # Test async connection
    async def test_async_db():
        try:
            await connect_to_database()
            if db is not None:
                logger.info("Async DB connection test successful.")
                collections = await db.list_collection_names()
                logger.info(f"Collections: {collections}")
            else:
                logger.error("Async DB connection test failed: db object is None.")
        except Exception as e:
            logger.error(f"Async DB connection test encountered an error: {e}")
        finally:
            await close_database_connection()

    asyncio.run(test_async_db())

    # Test sync connection
    try:
        connect_to_sync_database()
        if sync_db:
            logger.info("Sync DB connection test successful.")
            collections = sync_db.list_collection_names()
            logger.info(f"Collections: {collections}")
        else:
            logger.error("Sync DB connection test failed: sync_db object is None.")
    except Exception as e:
        logger.error(f"Sync DB connection test encountered an error: {e}")
    finally:
        close_sync_database_connection()
```

### `./app/__init__.py`
```py

```

### `./app/main.py`
```py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_to_database, close_database_connection
from app.utils.logger import logger
from app.api.routes import forecast, anomaly, recommend, health # Import routers
from app.models.model_manager import model_manager, ModelManager
import asyncio

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
        # Load models at startup, or train if not found/retrain needed
        # We'll use a separate task for retraining if needed after startup
        await model_manager.initialize_models()
        logger.info("AI models initialized successfully.")

        # Schedule periodic retraining in the background
        if settings.RETRAIN_INTERVAL_HOURS > 0:
            logger.info(f"Scheduling model retraining every {settings.RETRAIN_INTERVAL_HOURS} hours.")
            asyncio.create_task(model_manager.schedule_retraining())

    except Exception as e:
        logger.error(f"Failed to initialize AI models: {e}", exc_info=True)
        # Depending on criticality, you might want to exit or just log error
        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI model initialization failed: {e}")


    yield # Application runs

    # Shutdown events
    logger.info("AI Service shutting down...")
    await close_database_connection()
    logger.info("AI Service shut down complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
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
        "last_retrain_time": manager.last_retrain_time.isoformat() if manager.last_retrain_time else "N/A"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

### `./app/models/anomaly_detection.py`
```py
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
import joblib
import os
from app.config import settings
from app.utils.logger import logger
from app.services.feature_engineering import FeatureEngineer

class AnomalyDetectionModel:
    """
    Implements a machine learning model for anomaly detection.
    Supports IsolationForest and OneClassSVM.
    """
    def __init__(self, model_type: str = settings.ANOMALY_MODEL_TYPE, contamination: float = settings.ANOMALY_THRESHOLD):
        self.model = None
        self.model_type = model_type
        self.contamination = contamination
        self.feature_engineer = FeatureEngineer() # Feature engineer for scaling etc.
        self.model_path = os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_model_{model_type}.joblib")
        self.is_trained = False
        self.metrics = {}

    def _initialize_model(self):
        """Initializes the ML model based on model_type."""
        if self.model_type == "IsolationForest":
            self.model = IsolationForest(contamination=self.contamination, random_state=42, n_estimators=100)
            logger.info(f"Initialized IsolationForest for anomaly detection with contamination={self.contamination}.")
        elif self.model_type == "OneClassSVM":
            # nu is an upper bound on the fraction of training errors and a lower bound of the fraction of support vectors.
            # It's similar to contamination. A common value is 0.1 for typical anomaly rates.
            self.model = OneClassSVM(kernel='rbf', nu=self.contamination)
            logger.info(f"Initialized OneClassSVM for anomaly detection with nu={self.contamination}.")
        else:
            raise ValueError(f"Unsupported anomaly detection model type: {self.model_type}")

    def train(self, df: pd.DataFrame, features: list) -> dict:
        """
        Trains the anomaly detection model.
        :param df: DataFrame containing features for anomaly detection.
        :param features: List of columns to be used as features.
        """
        if df.empty or not features or not all(col in df.columns for col in features):
            logger.warning("No data or invalid features for anomaly detection training.")
            return {"status": "failed", "message": "No data or invalid features."}

        # Select features
        X = df[features]

        # Scale features (important for distance-based algorithms like SVM)
        # Scale features (important for distance-based algorithms like SVM)
        X_scaled = self.feature_engineer.scale_features(X, features, scaler_type='MinMaxScaler', fit=True)
        # Store original feature names for prediction consistency
        self._trained_features = X_scaled.columns.tolist()

        self._initialize_model()
        logger.info(f"Starting training for {self.model_type} model with {len(X_scaled)} samples and {len(features)} features.")
        if self.model is None:
            logger.error("Model is not initialized. Cannot fit.")
            return {"status": "failed", "message": "Model initialization failed."}
        self.model.fit(X_scaled)
        # No traditional "metrics" for unsupervised anomaly detection,
        if self.model_type == "IsolationForest":
            if self.model is not None:
                predictions = self.model.predict(X_scaled)
                n_outliers = list(predictions).count(-1)
                outlier_percentage = (n_outliers / len(predictions)) * 100 if len(predictions) > 0 else 0
                self.metrics = {"outliers_in_training_data": n_outliers, "outlier_percentage": f"{outlier_percentage:.2f}%"}
            else:
                logger.error("Model is None during prediction.")
                self.metrics = {}
        elif self.model_type == "OneClassSVM":
            if self.model is not None:
                predictions = self.model.predict(X_scaled)
                n_outliers = list(predictions).count(-1)
                outlier_percentage = (n_outliers / len(predictions)) * 100 if len(predictions) > 0 else 0
                self.metrics = {"outliers_in_training_data": n_outliers, "outlier_percentage": f"{outlier_percentage:.2f}%"}
            else:
                logger.error("Model is None during prediction.")
                self.metrics = {}
            outlier_percentage = (n_outliers / len(predictions)) * 100 if len(predictions) > 0 else 0
            self.metrics = {"outliers_in_training_data": n_outliers, "outlier_percentage": f"{outlier_percentage:.2f}%"}

        self.is_trained = True
        logger.info(f"Anomaly detection model training complete. Metrics: {self.metrics}")
        self.save_model()
        return {"status": "success", "metrics": self.metrics}

    def detect_anomalies(self, df: pd.DataFrame, features: list) -> pd.DataFrame:
        """
        Detects anomalies in the input DataFrame.
        Returns the DataFrame with an 'is_anomaly' column and anomaly scores.
        """
        if not self.is_trained or self.model is None:
            logger.error("Anomaly detection model not trained. Cannot detect anomalies.")
            raise ValueError("Model not trained.")
        if df.empty or not features or not all(col in df.columns for col in features):
            logger.warning("No data or invalid features for anomaly detection.")
            return df.assign(is_anomaly=False, anomaly_score=0.0) # Return with default columns

        X = df[features]
        # Use existing scaler for transformation
        X_scaled = self.feature_engineer.scale_features(X, features, scaler_type='MinMaxScaler', fit=False)

        # Ensure prediction features match trained features
        # This is a critical step. If `_trained_features` is None or not matching, it's an error.
        if not hasattr(self, '_trained_features') or not self._trained_features:
            logger.error("Trained features not available. Model might not have been trained or loaded correctly.")
            raise RuntimeError("Trained features not found for anomaly detection.")
        
        # Align columns of X_scaled with self._trained_features, filling missing ones with 0 or appropriate default
        X_scaled = X_scaled.reindex(columns=self._trained_features, fill_value=0)

        # Predict raw scores or decisions
        if self.model_type == "IsolationForest":
            # decision_function gives anomaly scores: lower is more anomalous
            df['anomaly_score'] = self.model.decision_function(X_scaled)
            # predict returns -1 for outliers, 1 for inliers
            df['is_anomaly'] = (self.model.predict(X_scaled) == -1)
        elif self.model_type == "OneClassSVM":
            # decision_function gives distance to hyperplane: negative for outliers
            df['anomaly_score'] = self.model.decision_function(X_scaled)
            df['is_anomaly'] = (self.model.predict(X_scaled) == -1)
        else:
            raise ValueError(f"Unsupported model type {self.model_type} for anomaly detection logic.")

        logger.info(f"Detected anomalies for {len(df)} samples.")
        return df
        for _, row in anomalies_df.iterrows():
            timestamp_value = row.get('timestamp')
            detail = {
                "id": str(row.get('_id')), # Assuming _id exists and can be converted to str
                "timestamp": timestamp_value.isoformat() if timestamp_value is not None and hasattr(timestamp_value, "isoformat") else None,
                "anomaly_score": float(row['anomaly_score']),
                "features": {feat: row[feat] for feat in anomaly_features if feat in row}
            }
            details.append(detail)
        return details
        details = []
        for index, row in anomalies_df.iterrows():
            detail = {
                "id": str(row.get('_id')), # Assuming _id exists and can be converted to str
                "timestamp": row.get('timestamp').isoformat() if 'timestamp' in row else None,
                "anomaly_score": float(row['anomaly_score']),
                "features": {feat: row[feat] for feat in anomaly_features if feat in row}
            }
            details.append(detail)
        return details

    def save_model(self):
        """Saves the trained model and its feature engineer."""
        if self.model:
            os.makedirs(settings.MODEL_SAVE_PATH, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.feature_engineer, os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_feature_engineer_{self.model_type}.joblib"))
            # Also save the list of trained features
            if hasattr(self, '_trained_features'):
                joblib.dump(self._trained_features, os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_trained_features_{self.model_type}.joblib"))
            logger.info(f"Anomaly detection model and feature engineer saved to {self.model_path}")
        else:
            logger.warning("No anomaly detection model to save.")

    def load_model(self):
        """Loads the trained model and its feature engineer."""
        try:
            self.model = joblib.load(self.model_path)
            self.feature_engineer = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_feature_engineer_{self.model_type}.joblib"))
            # Load trained features
            trained_features_path = os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_trained_features_{self.model_type}.joblib")
            if os.path.exists(trained_features_path):
                self._trained_features = joblib.load(trained_features_path)
            else:
                logger.warning("Trained features not found for anomaly model. This might cause issues during prediction if feature set changes.")
                self._trained_features = None # Or raise error
            
            self.is_trained = True
            logger.info(f"Anomaly detection model and feature engineer loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Anomaly detection model not found at {self.model_path}. Model needs to be trained.")
            self.is_trained = False
            return False
        except Exception as e:
            logger.error(f"Error loading anomaly detection model: {e}", exc_info=True)
            self.is_trained = False
            return False
```

### `./app/models/forecasting.py`
```py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
# from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
from app.config import settings
from app.utils.logger import logger
from app.services.feature_engineering import FeatureEngineer

class ForecastingModel:
    """
    Implements a machine learning model for sales forecasting.
    Supports RandomForestRegressor and LinearRegression.
    """
    def __init__(self, model_type: str = settings.FORECAST_MODEL_TYPE):
        self.model = None
        self.model_type = model_type
        self.feature_engineer = FeatureEngineer()
        self.model_path = os.path.join(settings.MODEL_SAVE_PATH, f"forecasting_model_{model_type}.joblib")
        self.is_trained = False
        self.metrics = {} # To store training metrics

    def _initialize_model(self):
        """Initializes the ML model based on model_type."""
        if self.model_type == "RandomForestRegressor":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            logger.info("Initialized RandomForestRegressor for forecasting.")
        elif self.model_type == "LinearRegression":
            self.model = LinearRegression()
            logger.info("Initialized LinearRegression for forecasting.")
        else:
            raise ValueError(f"Unsupported forecasting model type: {self.model_type}")

    def train(self, df: pd.DataFrame, target_col: str = 'daily_revenue') -> dict:
        """
        Trains the forecasting model.
        Expects df to be prepared with time series and feature engineering.
        """
        if df.empty:
            logger.warning("No data to train forecasting model.")
            return {"status": "failed", "message": "No data for training."}

        # Ensure 'timestamp' is datetime and sort
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Create time features
        df = self.feature_engineer.create_time_features(df, 'timestamp')

        # Create lag features for the target column
        # Lags are important for time series forecasting
        df = self.feature_engineer.create_lag_features(df, cols=[target_col], lags=[1, 2, 3, 7, 14])

        # Create rolling features
        df = self.feature_engineer.create_rolling_features(df, cols=[target_col], windows=[7, 14], agg_funcs=['mean', 'std'])

        # Drop rows with NaN values that result from lag/rolling features (typically at the beginning)
        df = df.dropna().reset_index(drop=True)
        if df.empty:
            logger.warning("DataFrame became empty after feature engineering and dropping NaNs.")
            return {"status": "failed", "message": "DataFrame empty after feature engineering."}

        # Define features and target
        features = [col for col in df.columns if col not in [target_col, 'timestamp', '_id']]
        X, y = self.feature_engineer.get_features_and_target(df, target_col, feature_cols=features)

        if X.empty or y.empty:
            logger.error("Features or target are empty after preparation for forecasting model training.")
            return {"status": "failed", "message": "Empty features or target after preparation."}

        # Split data (time-based split is crucial for time series)
        split_point = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_point], X.iloc[split_point:]
        y_train, y_test = y.iloc[:split_point], y.iloc[split_point:]

        if X_train.empty or y_train.empty:
            logger.warning("Training data is empty for forecasting model.")
            return {"status": "failed", "message": "Empty training data."}

        # Always initialize the model before training to avoid 'NoneType' errors
        self._initialize_model()

        logger.info(f"Starting training for {self.model_type} model with {len(X_train)} samples.")
        self.model.fit(X_train, y_train) # type: ignore

        # Evaluate
        y_pred = self.model.predict(X_test) # type: ignore
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        self.metrics = {"rmse": rmse, "r2_score": r2, "trained_on_samples": len(X_train)}
        self.is_trained = True
        logger.info(f"Forecasting model training complete. Metrics: {self.metrics}")

        self.save_model()
        return {"status": "success", "metrics": self.metrics}

    def predict(self, df: pd.DataFrame, target_col: str = 'daily_revenue') -> np.ndarray:
        """
        Makes predictions using the trained model.
        Expects df to be prepared with the same feature engineering steps as training.
        """
        if not self.is_trained or self.model is None:
            logger.error("Forecasting model not trained. Cannot make predictions.")
            raise ValueError("Model not trained.")
        if df.empty:
            logger.warning("No data provided for prediction.")
            return np.array([])

        # Ensure 'timestamp' is datetime and sort
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Apply same feature engineering as training
        df = self.feature_engineer.create_time_features(df, 'timestamp')
        df = self.feature_engineer.create_lag_features(df, cols=[target_col], lags=[1, 2, 3, 7, 14])
        df = self.feature_engineer.create_rolling_features(df, cols=[target_col], windows=[7, 14], agg_funcs=['mean', 'std'])
        df = df.dropna().reset_index(drop=True) # Drop rows with NaN from lag/rolling features

        if df.empty:
            logger.warning("DataFrame became empty after feature engineering for prediction.")
            return np.array([])

        features = [col for col in df.columns if col not in [target_col, 'timestamp', '_id']]
        # Ensure features match what the model was trained on
        # This is a critical step for deployment: ensure consistency in feature columns
        # For simplicity, we assume the input df has all necessary features or can be engineered.
        # In a real system, you'd save feature names during training and validate here.
        # For now, let's just make sure we only select features that exist in the test data
        X = df[features]
        # Align columns if necessary (e.g., if some features are missing in prediction data)
        # For a robust solution, store trained features and reindex X here.
        # Example: X = X.reindex(columns=self.trained_features, fill_value=0)

        predictions = self.model.predict(X)
        logger.info(f"Generated {len(predictions)} predictions.")
        return predictions

    def forecast_future(self, historical_df: pd.DataFrame, horizon: int = settings.FORECAST_HORIZON, target_col: str = 'daily_revenue'):
        """
        Forecasts future values for a given horizon using the trained model.
        Requires enough historical data for lag and rolling features.
        """
        if not self.is_trained or self.model is None:
            logger.error("Forecasting model not trained. Cannot forecast future values.")
            raise ValueError("Model not trained.")
        if historical_df.empty:
            logger.warning("No historical data provided for forecasting.")
            return pd.DataFrame()

        # Ensure 'timestamp' is datetime and sort
        historical_df['timestamp'] = pd.to_datetime(historical_df['timestamp'])
        historical_df = historical_df.sort_values('timestamp').reset_index(drop=True)
        # Get the last known values for starting the forecast
        last_date = historical_df['timestamp'].max()
        last_target_value = historical_df[target_col].iloc[-1]

        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, horizon + 1)]
        forecast_df = pd.DataFrame({'timestamp': future_dates, target_col: 0.0}) # Placeholder target

        # Combine historical and future to create features for future predictions
        combined_df = pd.concat([historical_df, forecast_df], ignore_index=True)
        combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)

        # Apply same feature engineering as training
        combined_df = self.feature_engineer.create_time_features(combined_df, 'timestamp')
        combined_df = self.feature_engineer.create_lag_features(combined_df, cols=[target_col], lags=[1, 2, 3, 7, 14])
        combined_df = self.feature_engineer.create_rolling_features(combined_df, cols=[target_col], windows=[7, 14], agg_funcs=['mean', 'std'])

        # Replace NaN from lags with appropriate values for prediction (e.g., last known value)
        # For the very first rows, fill with 0 or a sensible default.
        combined_df = combined_df.fillna(0) # Or more sophisticated imputation

        # Identify rows for actual forecasting (the future dates)
        future_X = combined_df[combined_df['timestamp'].isin(future_dates)]
        
        if future_X.empty:
            logger.warning("Future data frame is empty after feature engineering for forecasting.")
            return pd.DataFrame()

        # Select features for prediction, ensuring they match training
        features = [col for col in future_X.columns if col not in [target_col, 'timestamp', '_id']]
        
        # This is where a more robust feature management would be needed.
        # For now, let's filter X to only contain features present in the original historical_df training set (minus target, timestamp, _id).
        # We need to ensure that the features array passed to predict contains *all* columns the model was trained on, in the correct order.
        # A common practice is to store the list of features used during training and reindex prediction data.
        
        # For this example, let's extract the feature columns from the future_X dataframe:
        X_predict = future_X[features] # This assumes `features` list contains all needed columns.
        
        # Make predictions
        future_predictions = self.model.predict(X_predict)

        # Assign predictions to the target column in the forecast_df
        forecast_df[target_col] = future_predictions

        logger.info(f"Generated {horizon} day forecast for '{target_col}'.")
        return forecast_df[['timestamp', target_col]]


    def save_model(self):
        """Saves the trained model and feature engineer (scalers/encoders)."""
        if self.model:
            os.makedirs(settings.MODEL_SAVE_PATH, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.feature_engineer, os.path.join(settings.MODEL_SAVE_PATH, f"forecasting_feature_engineer_{self.model_type}.joblib"))
            logger.info(f"Forecasting model and feature engineer saved to {self.model_path}")
        else:
            logger.warning("No forecasting model to save.")

    def load_model(self):
        """Loads the trained model and feature engineer."""
        try:
            self.model = joblib.load(self.model_path)
            self.feature_engineer = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, f"forecasting_feature_engineer_{self.model_type}.joblib"))
            self.is_trained = True
            logger.info(f"Forecasting model and feature engineer loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Forecasting model not found at {self.model_path}. Model needs to be trained.")
            self.is_trained = False
            return False
        except Exception as e:
            logger.error(f"Error loading forecasting model: {e}", exc_info=True)
            self.is_trained = False
            return False
```

### `./app/models/__init__.py`
```py

```

### `./app/models/model_manager.py`
```py
# ai_service/app/models/model_manager.py
import asyncio
from datetime import datetime
import pandas as pd
from app.config import settings
from app.utils.logger import logger
from app.database import get_database
from app.services.data_processor import DataProcessor
from app.models.forecasting import ForecastingModel
from app.models.anomaly_detection import AnomalyDetectionModel
from app.models.recommendation import RecommendationModel

class ModelManager:
    """
    Manages the lifecycle (initialization, training, loading, retraining) of all ML models.
    """
    _instance = None # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.forecasting_model = None
        self.anomaly_model = None
        self.recommendation_model = None
        self.db_connected = False
        self.models_loaded = False
        self.last_retrain_time = None
        self._initialized = True # Mark as initialized

    async def initialize_models(self):
        """
        Initializes and loads/trains all models. Called once at application startup.
        """
        logger.info("Initializing AI models...")
        # CORRECTED LINE: Check if async db object is not None
        self.db_connected = get_database() is not None

        # Initialize model instances
        self.forecasting_model = ForecastingModel()
        self.anomaly_model = AnomalyDetectionModel()
        self.recommendation_model = RecommendationModel()

        # Try to load models, if not found or training is forced, train them
        load_success_forecasting = self.forecasting_model.load_model()
        load_success_anomaly = self.anomaly_model.load_model()
        load_success_recommendation = self.recommendation_model.load_model()

        if load_success_forecasting and load_success_anomaly and load_success_recommendation:
            self.models_loaded = True
            logger.info("All models loaded successfully from disk.")
        else:
            logger.warning("One or more models not found or failed to load. Initiating initial training.")
            await self.train_all_models() # Perform initial training

        self.models_loaded = (getattr(self.forecasting_model, "is_trained", False) and
                              getattr(self.anomaly_model, "is_trained", False) and
                              getattr(self.recommendation_model, "is_trained", False))
        if not self.models_loaded:
            logger.error("Not all models are trained/ready after initialization phase.")

    async def train_all_models(self):
        """
        Orchestrates the training of all machine learning models.
        """
        if not self.db_connected:
            logger.error("Cannot train models: MongoDB connection not established.")
            return

        logger.info("Starting full model retraining process...")

        # Ensure model instances are initialized before training
        if self.forecasting_model is None:
            self.forecasting_model = ForecastingModel()
        if self.anomaly_model is None:
            self.anomaly_model = AnomalyDetectionModel()
        if self.recommendation_model is None:
            self.recommendation_model = RecommendationModel()

        try:
            # Use async db for data processor within FastAPI context
            data_processor = DataProcessor(db=get_database())

            # Train Forecasting Model
            logger.info("Training Forecasting Model...")
            transactions_df = await data_processor.get_transactions_data()
            daily_sales_df = data_processor.prepare_time_series_data(transactions_df, 'totalAmount', freq='D')
            if not daily_sales_df.empty:
                forecast_result = self.forecasting_model.train(daily_sales_df, target_col='totalAmount')
                logger.info(f"Forecasting Model training result: {forecast_result}")
            else:
                logger.warning("Skipping forecasting model training: No daily sales data.")

            # Train Anomaly Detection Model
            logger.info("Training Anomaly Detection Model...")
            anomaly_df = await data_processor.get_transactions_data()
            if not anomaly_df.empty:
                anomaly_features = ['totalAmount', 'quantity']
                anomaly_df['totalAmount'] = pd.to_numeric(anomaly_df['totalAmount'], errors='coerce').fillna(0)
                anomaly_df['quantity'] = pd.to_numeric(anomaly_df['quantity'], errors='coerce').fillna(0)
                valid_anomaly_features = [f for f in anomaly_features if f in anomaly_df.columns and pd.api.types.is_numeric_dtype(anomaly_df[f])]
                if not valid_anomaly_features:
                    logger.warning(f"No valid numeric features for anomaly detection training. Available numeric features: {[c for c in anomaly_df.columns if pd.api.types.is_numeric_dtype(anomaly_df[c])]}")
                else:
                    anomaly_result = self.anomaly_model.train(anomaly_df, features=valid_anomaly_features)
                    logger.info(f"Anomaly Detection Model training result: {anomaly_result}")
            else:
                logger.warning("Skipping anomaly detection model training: No transaction data for anomalies.")

            # Train Recommendation Model
            logger.info("Training Recommendation Model...")
            recommendation_result = await self.recommendation_model.train(data_processor)
            logger.info(f"Recommendation Model training result: {recommendation_result}")

            self.last_retrain_time = datetime.now()
            self.models_loaded = (getattr(self.forecasting_model, "is_trained", False) and
                                  getattr(self.anomaly_model, "is_trained", False) and
                                  getattr(self.recommendation_model, "is_trained", False))
            logger.info("Full model retraining process completed.")

        except Exception as e:
            logger.error(f"Error during full model retraining: {e}", exc_info=True)
            self.models_loaded = False # Mark models as not fully loaded on error

    async def schedule_retraining(self):
        """
        Schedules periodic retraining of all models.
        """
        while True:
            await asyncio.sleep(settings.RETRAIN_INTERVAL_HOURS * 3600) # Convert hours to seconds
            logger.info(f"Initiating scheduled retraining (every {settings.RETRAIN_INTERVAL_HOURS} hours)...")
            await self.train_all_models()
            if self.models_loaded:
                logger.info("Scheduled retraining completed successfully.")
            else:
                logger.error("Scheduled retraining encountered issues.")

# Create a singleton instance of ModelManager
model_manager = ModelManager()
```

### `./app/models/recommendation.py`
```py
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
import joblib
import os
from typing import Optional
from app.config import settings
from app.utils.logger import logger
from app.services.data_processor import DataProcessor

class RecommendationModel:
    """
    Implements a recommendation system using collaborative filtering (SVD).
    """
    def __init__(self, model_type: str = settings.RECOMMENDER_MODEL_TYPE, n_components: int = 50):
        self.model = None
        self.model_type = model_type
        self.n_components = n_components
        self.user_item_matrix = None # Stores the user-item interaction matrix
        self.user_mapper = {} # Map original user IDs to matrix indices
        self.item_mapper = {} # Map original item IDs to matrix indices
        self.user_inverse_mapper = {} # Map matrix indices back to original user IDs
        self.item_inverse_mapper = {} # Map matrix indices back to original item IDs
        self.model_path = os.path.join(settings.MODEL_SAVE_PATH, f"recommendation_model_{model_type}.joblib")
        self.is_trained = False

    async def train(self, data_processor: DataProcessor) -> dict:
        """
        Trains the recommendation model.
        Expects a DataProcessor instance to fetch user-item interaction data.
        """
        logger.info("Starting training for recommendation model...")
        self.user_item_matrix = await data_processor.get_user_item_matrix()

        if self.user_item_matrix.empty:
            logger.warning("No user-item interaction data to train recommendation model.")
            return {"status": "failed", "message": "No data for training."}

        # Create mappers for user and item IDs
        self.user_mapper = {user_id: idx for idx, user_id in enumerate(self.user_item_matrix.index)}
        self.item_mapper = {item_id: idx for idx, item_id in enumerate(self.user_item_matrix.columns)}
        self.user_inverse_mapper = {idx: user_id for user_id, idx in self.user_mapper.items()}
        self.item_inverse_mapper = {idx: item_id for item_id, idx in self.item_mapper.items()}

        # Convert to sparse matrix for SVD
        sparse_user_item = csr_matrix(self.user_item_matrix.values)

        if self.model_type == "SVD":
            self.model = TruncatedSVD(n_components=self.n_components, random_state=42)
            logger.info(f"Initialized TruncatedSVD with {self.n_components} components.")
        # elif self.model_type == "KNNWithMeans":
            # For KNN based models, you'd typically use surprise library or custom implementation
            # self.model = ...
        else:
            raise ValueError(f"Unsupported recommendation model type: {self.model_type}")

        self.model.fit(sparse_user_item)
        self.is_trained = True
        logger.info("Recommendation model training complete.")
        self.save_model()
        return {"status": "success", "message": "Recommendation model trained successfully."}

    def _get_popular_recommendations(self, num_recommendations: int = 10, product_data: Optional[pd.DataFrame] = None):
        """
        Provides general popular recommendations (e.g., for cold-start users).
        """
        logger.info("Providing popular recommendations (cold-start strategy).")
        if self.user_item_matrix is not None and not self.user_item_matrix.empty:
            # Sum interactions for each item
            item_popularity = self.user_item_matrix.sum(axis=0).sort_values(ascending=False)
            popular_item_ids = item_popularity.index.tolist()[:num_recommendations]
            
            # If product_data is available, try to get names
            if product_data is not None and not product_data.empty:
                popular_products_info = product_data[product_data['productId'].isin(popular_item_ids)]
                return popular_products_info[['productId', 'productName']].to_dict(orient='records')
            return [{"productId": pid} for pid in popular_item_ids]
        
        logger.warning("No user-item matrix available to determine popularity. Returning empty list.")
        return []

    async def get_user_recommendations(self, user_id: str, num_recommendations: int = 10, product_data: Optional[pd.DataFrame] = None):
        """
        Generates personalized product recommendations for a given user.
        """
        if not self.is_trained or self.model is None or self.user_item_matrix is None:
            logger.warning("Recommendation model not trained or data not loaded. Providing popular recommendations.")
            return self._get_popular_recommendations(num_recommendations, product_data)

        if user_id not in self.user_mapper:
            logger.warning(f"User {user_id} not found in training data. Providing popular recommendations.")
            return self._get_popular_recommendations(num_recommendations, product_data)

        user_idx = self.user_mapper[user_id]
        user_vector = self.user_item_matrix.iloc[user_idx]

        # Reconstruct the original matrix from SVD components (approximation)
        if self.model_type == "SVD":
            reconstructed_matrix = np.dot(self.model.transform(csr_matrix(self.user_item_matrix.values)), self.model.components_)
            # Convert back to DataFrame for easy indexing
            reconstructed_df = pd.DataFrame(reconstructed_matrix, index=self.user_item_matrix.index, columns=self.user_item_matrix.columns)
            
            # Get predicted ratings for the user
            user_predicted_ratings = reconstructed_df.loc[user_id]

            # Filter out items the user has already interacted with
            user_interacted_items = user_vector[user_vector > 0].index
            recommendations_series = user_predicted_ratings.drop(user_interacted_items, errors='ignore')

            # Sort and get top N recommendations
            if isinstance(recommendations_series, pd.Series):
                top_recommendations = recommendations_series.sort_values(ascending=False).head(num_recommendations).index.tolist()
            else:
                # Convert to Series if not already
                # If recommendations_series is a DataFrame, select the first row as a Series
                if isinstance(recommendations_series, pd.DataFrame):
                    recommendations_series = recommendations_series.iloc[0]
                top_recommendations = recommendations_series.sort_values(ascending=False).head(num_recommendations).index.tolist()
        else:
            logger.warning(f"Recommendation type {self.model_type} not fully implemented for prediction logic. Returning popular.")
            return self._get_popular_recommendations(num_recommendations, product_data)

        logger.info(f"Generated {len(top_recommendations)} recommendations for user {user_id}.")
        
        # Fetch product details if product_data is available
        if product_data is not None and not product_data.empty:
            recommended_products_info = product_data[product_data['productId'].isin(top_recommendations)]
            # Ensure order based on ranking
            product_dict = recommended_products_info.set_index('productId').T.to_dict('list')
            ordered_recommendations = []
            for prod_id in top_recommendations:
                if prod_id in product_dict:
                    ordered_recommendations.append({"productId": prod_id, "productName": product_dict[prod_id][0]}) # Assuming productName is first item
            return ordered_recommendations
        
        return [{"productId": pid} for pid in top_recommendations]


    def save_model(self):
        """Saves the trained model, user-item matrix, and mappers."""
        if self.model:
            os.makedirs(settings.MODEL_SAVE_PATH, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.user_item_matrix, os.path.join(settings.MODEL_SAVE_PATH, "user_item_matrix.joblib"))
            joblib.dump(self.user_mapper, os.path.join(settings.MODEL_SAVE_PATH, "user_mapper.joblib"))
            joblib.dump(self.item_mapper, os.path.join(settings.MODEL_SAVE_PATH, "item_mapper.joblib"))
            joblib.dump(self.user_inverse_mapper, os.path.join(settings.MODEL_SAVE_PATH, "user_inverse_mapper.joblib"))
            joblib.dump(self.item_inverse_mapper, os.path.join(settings.MODEL_SAVE_PATH, "item_inverse_mapper.joblib"))
            logger.info(f"Recommendation model and associated data saved to {self.model_path}")
        else:
            logger.warning("No recommendation model to save.")

    def load_model(self):
        """Loads the trained model, user-item matrix, and mappers."""
        try:
            self.model = joblib.load(self.model_path)
            self.user_item_matrix = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "user_item_matrix.joblib"))
            self.user_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "user_mapper.joblib"))
            self.item_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "item_mapper.joblib"))
            self.user_inverse_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "user_inverse_mapper.joblib"))
            self.item_inverse_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "item_inverse_mapper.joblib"))
            self.is_trained = True
            logger.info(f"Recommendation model and associated data loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Recommendation model not found at {self.model_path}. Model needs to be trained.")
            self.is_trained = False
            return False
        except Exception as e:
            logger.error(f"Error loading recommendation model: {e}", exc_info=True)
            self.is_trained = False
            return False
```

### `./app/services/data_processor.py`
```py
from datetime import datetime, timedelta
import pandas as pd
from app.config import settings
from app.utils.logger import logger
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.mongo_client import MongoClient

class DataProcessor:
    """
    Handles fetching and initial processing of raw data from MongoDB.
    """
    def __init__(self, db: AsyncIOMotorDatabase = None, sync_db: MongoClient = None): # type: ignore
        self._db = db
        self._sync_db = sync_db # For synchronous operations if needed

        if not self._db and not self._sync_db:
            raise ValueError("Either an async or a sync database connection must be provided.")

    def _get_db_client(self):
        """Returns the appropriate database client based on context."""
        if self._db:
            return self._db
        elif self._sync_db:
            return self._sync_db
        else:
            raise RuntimeError("No database client available.")

    async def get_transactions_data(self, days: int = settings.DATA_COLLECTION_DAYS) -> pd.DataFrame:
        """
        Fetches transaction data for a specified number of past days.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Fetching transaction data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        try:
            # Use async db client
            transactions_cursor = self._get_db_client().transactions.find(
                {"timestamp": {"$gte": start_date, "$lte": end_date}}
            )
            transactions_list = await transactions_cursor.to_list(length=None) # Fetch all documents

            if not transactions_list:
                logger.warning(f"No transaction data found for the last {days} days.")
                return pd.DataFrame()

            df = pd.DataFrame(transactions_list)

            # Convert timestamp to datetime and sort
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)

            logger.info(f"Fetched {len(df)} transactions.")
            return df

        except Exception as e:
            logger.error(f"Error fetching transaction data: {e}", exc_info=True)
            return pd.DataFrame()

    async def get_user_behavior_data(self, days: int = settings.DATA_COLLECTION_DAYS) -> pd.DataFrame:
        """
        Fetches user activity and feedback data for a specified number of past days.
        Combines user_activities and feedback collections.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Fetching user behavior data (activities and feedback) from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        try:
            # Fetch user activities (using correct collection name 'user_activities')
            activities_cursor = self._get_db_client().user_activities.find(
                {"timestamp": {"$gte": start_date, "$lte": end_date}}
            )
            activities_list = await activities_cursor.to_list(length=None)
            activities_df = pd.DataFrame(activities_list)

            # Fetch feedback (using correct collection name 'feedback')
            feedback_cursor = self._get_db_client().feedback.find(
                {"timestamp": {"$gte": start_date, "$lte": end_date}}
            )
            feedback_list = await feedback_cursor.to_list(length=None)
            feedback_df = pd.DataFrame(feedback_list)

            if not activities_list and not feedback_list:
                logger.warning(f"No user activity or feedback data found for the last {days} days.")
                return pd.DataFrame()

            # Combine and process
            combined_df = pd.concat([activities_df, feedback_df], ignore_index=True)
            if not combined_df.empty:
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
            else:
                return pd.DataFrame()

            logger.info(f"Fetched {len(activities_df)} activities and {len(feedback_df)} feedback entries.")
            return combined_df

        except Exception as e:
            logger.error(f"Error fetching user behavior data: {e}", exc_info=True)
            return pd.DataFrame()


    async def get_product_data(self) -> pd.DataFrame:
        """
        Fetches product data.
        """
        logger.info("Fetching product data.")
        try:
            products_cursor = self._get_db_client().products.find({})
            products_list = await products_cursor.to_list(length=None)

            if not products_list:
                logger.warning("No product data found.")
                return pd.DataFrame()

            df = pd.DataFrame(products_list)
            logger.info(f"Fetched {len(df)} products.")
            return df
        except Exception as e:
            logger.error(f"Error fetching product data: {e}", exc_info=True)
            return pd.DataFrame()

    def prepare_time_series_data(self, df: pd.DataFrame, value_col: str, freq: str = 'D') -> pd.DataFrame:
        """
        Prepares time series data (e.g., daily sales) from a DataFrame.
        Assumes 'timestamp' column exists.
        """
        if df.empty:
            logger.warning("Input DataFrame is empty for time series preparation.")
            return pd.DataFrame()

        df_ts = df.set_index('timestamp').resample(freq)[value_col].sum().fillna(0).to_frame()
        df_ts.columns = [value_col]
        df_ts = df_ts.reset_index()
        logger.info(f"Prepared time series data with frequency '{freq}' for '{value_col}'. Rows: {len(df_ts)}")
        return df_ts

    async def get_user_item_matrix(self, min_interactions: int = settings.MIN_INTERACTIONS_FOR_RECOMMENDATION) -> pd.DataFrame:
        """
        Generates a user-item interaction matrix from transaction data.
        Filters out users/items with too few interactions.
        """
        logger.info("Generating user-item interaction matrix...")
        try:
            transactions_df = await self.get_transactions_data(days=settings.DATA_COLLECTION_DAYS)
            if transactions_df.empty:
                logger.warning("No transactions data to build user-item matrix.")
                return pd.DataFrame()

            # Ensure correct data types
            transactions_df['userId'] = transactions_df['userId'].astype(str)
            transactions_df['productId'] = transactions_df['productId'].astype(str)
            transactions_df['quantity'] = transactions_df['quantity'].astype(int)

            # Aggregate quantity per user-product pair (implicit rating)
            user_item_interactions = transactions_df.groupby(['userId', 'productId'])['quantity'].sum().reset_index()
            user_item_interactions.rename(columns={'quantity': 'interaction_count'}, inplace=True)

            # Filter out users with too few interactions (optional, for cold-start or noise)
            user_counts = user_item_interactions.groupby('userId').size()
            valid_users = user_counts[user_counts >= min_interactions].index
            user_item_interactions = user_item_interactions[user_item_interactions['userId'].isin(valid_users)]

            if user_item_interactions.empty:
                logger.warning(f"No sufficient user-item interactions after filtering for min_interactions={min_interactions}.")
                return pd.DataFrame()

            # Create pivot table (user-item matrix)
            user_item_matrix = user_item_interactions.pivot_table(
                index='userId',
                columns='productId',
                values='interaction_count'
            ).fillna(0) # Fill NaN with 0 for no interaction

            logger.info(f"Generated user-item matrix with shape: {user_item_matrix.shape}")
            return user_item_matrix

        except Exception as e:
            logger.error(f"Error generating user-item matrix: {e}", exc_info=True)
            return pd.DataFrame()
```

### `./app/services/feature_engineering.py`
```py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from app.utils.logger import logger

class FeatureEngineer:
    """
    Handles feature engineering for machine learning models.
    """
    def __init__(self):
        self.scalers = {} # To store scalers for different features
        self.encoders = {} # To store encoders for categorical features

    def create_time_features(self, df: pd.DataFrame, timestamp_col: str = 'timestamp') -> pd.DataFrame:
        """
        Creates time-based features from a timestamp column.
        Expects timestamp_col to be datetime objects.
        """
        if df.empty or timestamp_col not in df.columns:
            logger.warning("DataFrame is empty or timestamp_col not found for time features.")
            return df

        df['year'] = df[timestamp_col].dt.year
        df['month'] = df[timestamp_col].dt.month
        df['day'] = df[timestamp_col].dt.day
        df['day_of_week'] = df[timestamp_col].dt.dayofweek
        df['day_of_year'] = df[timestamp_col].dt.dayofyear
        df['week_of_year'] = df[timestamp_col].dt.isocalendar().week.astype(int)
        df['hour'] = df[timestamp_col].dt.hour
        df['quarter'] = df[timestamp_col].dt.quarter
        df['is_weekend'] = ((df[timestamp_col].dt.dayofweek == 5) | (df[timestamp_col].dt.dayofweek == 6)).astype(int)
        df['is_month_start'] = df[timestamp_col].dt.is_month_start.astype(int)
        df['is_month_end'] = df[timestamp_col].dt.is_month_end.astype(int)

        logger.info(f"Created time features for DataFrame with {len(df)} rows.")
        return df

    def create_lag_features(self, df: pd.DataFrame, cols: list, lags: list) -> pd.DataFrame:
        """
        Creates lag features for specified columns.
        Expects df to be sorted by time.
        """
        if df.empty:
            logger.warning("DataFrame is empty for lag feature creation.")
            return df
        if not all(col in df.columns for col in cols):
            logger.error(f"One or more columns {cols} not found for lag features.")
            return df

        for col in cols:
            for lag in lags:
                df[f'{col}_lag_{lag}'] = df[col].shift(lag)
        df = df.fillna(0) # Fill NaN from shifting
        logger.info(f"Created lag features for columns {cols} with lags {lags}.")
        return df

    def create_rolling_features(self, df: pd.DataFrame, cols: list, windows: list, agg_funcs: list) -> pd.DataFrame:
        """
        Creates rolling window features for specified columns.
        Expects df to be sorted by time.
        """
        if df.empty:
            logger.warning("DataFrame is empty for rolling feature creation.")
            return df
        if not all(col in df.columns for col in cols):
            logger.error(f"One or more columns {cols} not found for rolling features.")
            return df

        for col in cols:
            for window in windows:
                for agg_func in agg_funcs:
                    if agg_func == 'mean':
                        df[f'{col}_roll_mean_{window}'] = df[col].rolling(window=window).mean()
                    elif agg_func == 'std':
                        df[f'{col}_roll_std_{window}'] = df[col].rolling(window=window).std()
                    elif agg_func == 'min':
                        df[f'{col}_roll_min_{window}'] = df[col].rolling(window=window).min()
                    elif agg_func == 'max':
                        df[f'{col}_roll_max_{window}'] = df[col].rolling(window=window).max()
        df = df.fillna(0) # Fill NaN from rolling
        logger.info(f"Created rolling features for columns {cols} with windows {windows} and funcs {agg_funcs}.")
        return df

    def create_anomaly_features(self, df: pd.DataFrame, value_col: str) -> pd.DataFrame:
        """
        Creates simple anomaly-related features (e.g., deviation from mean).
        """
        if df.empty or value_col not in df.columns:
            logger.warning("DataFrame is empty or value_col not found for anomaly features.")
            return df

        df[f'{value_col}_daily_mean'] = df[value_col].rolling(window=7, min_periods=1).mean()
        df[f'{value_col}_daily_std'] = df[value_col].rolling(window=7, min_periods=1).std()
        df[f'{value_col}_deviation'] = df[value_col] - df[f'{value_col}_daily_mean']
        df[f'{value_col}_zscore'] = df[f'{value_col}_deviation'] / df[f'{value_col}_daily_std'].replace(0, 1) # Avoid div by zero
        df = df.fillna(0)
        logger.info(f"Created anomaly features for '{value_col}'.")
        return df

    def scale_features(self, df: pd.DataFrame, cols: list, scaler_type: str = 'StandardScaler', fit: bool = True) -> pd.DataFrame:
        """
        Scales numerical features.
        :param df: DataFrame to scale.
        :param cols: List of columns to scale.
        :param scaler_type: Type of scaler ('StandardScaler' or 'MinMaxScaler').
        :param fit: If True, fit the scaler; if False, transform using existing scaler.
        """
        if df.empty or not cols or not all(col in df.columns for col in cols):
            logger.warning(f"DataFrame empty or columns missing for scaling: {cols}.")
            return df

        for col in cols:
            if fit:
                if scaler_type == 'StandardScaler':
                    scaler = StandardScaler()
                elif scaler_type == 'MinMaxScaler':
                    scaler = MinMaxScaler()
                else:
                    raise ValueError("scaler_type must be 'StandardScaler' or 'MinMaxScaler'")
                df[col] = scaler.fit_transform(df[[col]])
                self.scalers[col] = scaler
                logger.info(f"Fitted and scaled '{col}' with {scaler_type}.")
            else:
                if col in self.scalers:
                    df[col] = self.scalers[col].transform(df[[col]])
                    logger.info(f"Transformed '{col}' with existing {scaler_type}.")
                else:
                    logger.warning(f"No scaler found for '{col}', skipping transformation.")
        return df

    def encode_categorical_features(self, df: pd.DataFrame, cols: list, encoder_type: str = 'LabelEncoder', fit: bool = True) -> pd.DataFrame:
        """
        Encodes categorical features. Supports LabelEncoder for simplicity.
        :param df: DataFrame to encode.
        :param cols: List of columns to encode.
        :param encoder_type: Type of encoder ('LabelEncoder').
        :param fit: If True, fit the encoder; if False, transform using existing encoder.
        """
        if df.empty or not cols or not all(col in df.columns for col in cols):
            logger.warning(f"DataFrame empty or columns missing for encoding: {cols}.")
            return df

        for col in cols:
            if encoder_type == 'LabelEncoder':
                if fit:
                    encoder = LabelEncoder()
                    df[col] = encoder.fit_transform(df[col])
                    self.encoders[col] = encoder
                    logger.info(f"Fitted and encoded '{col}' with LabelEncoder.")
                else:
                    if col in self.encoders:
                        # Handle unseen labels during transformation
                        # Replace unseen labels with a placeholder (e.g., -1) or the most frequent label
                        # Here, we'll assign -1 for simplicity
                        unseen_labels = set(df[col].unique()) - set(self.encoders[col].classes_)
                        if unseen_labels:
                            logger.warning(f"Unseen labels detected in column '{col}': {unseen_labels}. Assigning -1.")
                            df[col] = df[col].apply(lambda x: self.encoders[col].transform([x])[0] if x in self.encoders[col].classes_ else -1)
                        else:
                            df[col] = self.encoders[col].transform(df[col])
                        logger.info(f"Transformed '{col}' with existing LabelEncoder.")
                    else:
                        logger.warning(f"No encoder found for '{col}', skipping transformation.")
            else:
                raise ValueError("encoder_type must be 'LabelEncoder'")
        return df

    def get_features_and_target(self, df: pd.DataFrame, target_col: str, feature_cols: list = None):
        """
        Separates features (X) and target (y) from a DataFrame.
        """
        if df.empty or target_col not in df.columns:
            logger.error(f"DataFrame empty or target column '{target_col}' not found for feature/target split.")
            return pd.DataFrame(), pd.Series()

        if feature_cols:
            X = df[feature_cols]
        else:
            X = df.drop(columns=[target_col], errors='ignore')
        y = df[target_col]

        logger.info(f"Separated features (X shape: {X.shape}) and target (y shape: {y.shape}).")
        return X, y
```

### `./app/services/__init__.py`
```py

```

### `./app/utils/__init__.py`
```py

```

### `./app/utils/logger.py`
```py
import os
from loguru import logger as loguru_logger
from datetime import datetime

# Remove default handler to avoid duplicate logs
loguru_logger.remove()

# Configure logger for console output
loguru_logger.add(
    sink="sys.stdout",
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
    diagnose=True
)

# Configure logger for file output
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file_path = os.path.join(LOG_DIR, f"ai_service_{datetime.now().strftime('%Y-%m-%d')}.log")

loguru_logger.add(
    sink=log_file_path,
    rotation="1 day",  # New log file every day
    retention="7 days", # Keep logs for 7 days
    compression="zip",  # Compress old log files
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    diagnose=True
)

# Expose loguru_logger as 'logger' for easy import
logger = loguru_logger
```

### `./Dockerfile`
```Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `./tests/__init__.py`
```py

```

