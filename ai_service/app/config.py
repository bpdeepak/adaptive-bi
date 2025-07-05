# ai_service/app/config.py
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
    # Ensure this matches the format expected by pymongo and the docker-compose setup
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/adaptive_bi")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "adaptive_bi")

    # JWT settings (if used for internal service communication)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your_strong_jwt_secret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # Model settings
    MODEL_SAVE_PATH: str = os.getenv("MODEL_SAVE_PATH", "models/saved_models")
    
    # NEW: Model retraining interval in MINUTES
    # Default is 0 (COMPLETELY DISABLED) to prevent memory crashes.
    MODEL_RETRAIN_INTERVAL_MINUTES: int = int(os.getenv("MODEL_RETRAIN_INTERVAL_MINUTES", 0)) 

    # Forecasting Model Parameters
    FORECAST_HORIZON: int = int(os.getenv("FORECAST_HORIZON", 7)) # Days to forecast
    FORECAST_MODEL_TYPE: str = os.getenv("FORECAST_MODEL_TYPE", "RandomForestRegressor") # RandomForestRegressor or LinearRegression

    # Anomaly Detection Model Parameters
    ANOMALY_THRESHOLD: float = float(os.getenv("ANOMALY_THRESHOLD", 0.05)) # For IsolationForest, contamination
    ANOMALY_MODEL_TYPE: str = os.getenv("ANOMALY_MODEL_TYPE", "IsolationForest") # IsolationForest or OneClassSVM

    # Recommendation Model Parameters
    MIN_INTERACTIONS_FOR_RECOMMENDATION: int = int(os.getenv("MIN_INTERACTIONS_FOR_RECOMMENDATION", 2))
    RECOMMENDER_MODEL_TYPE: str = os.getenv("RECOMMENDER_MODEL_TYPE", "SVD") # SVD or KNNWithMeans

    # Data collection window for training - DRASTICALLY REDUCED for memory conservation
    DATA_COLLECTION_DAYS: int = int(os.getenv("DATA_COLLECTION_DAYS", 3)) # Data from last 3 days for training (reduced from 90)

    # CORS settings
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",") # Allows all origins for development

    # Memory-efficient model training configuration - ULTRA AGGRESSIVE
    MEMORY_SAFE_MODE: bool = os.getenv("MEMORY_SAFE_MODE", "True").lower() == "true"
    MAX_PARALLEL_MODELS: int = int(os.getenv("MAX_PARALLEL_MODELS", 1))  # Train only one model at a time to save memory
    MAX_USERS_FOR_SIMILARITY: int = int(os.getenv("MAX_USERS_FOR_SIMILARITY", 100))  # Limit users for knowledge graph similarity (reduced from 1000)
    MAX_TRANSACTIONS_CHUNK: int = int(os.getenv("MAX_TRANSACTIONS_CHUNK", 2000))  # Chunk size for large datasets (reduced from 50000)
    MAX_ACTIVITIES_CHUNK: int = int(os.getenv("MAX_ACTIVITIES_CHUNK", 5000))  # Chunk size for activities (reduced from 100000)
    ENABLE_MEMORY_MONITORING: bool = os.getenv("ENABLE_MEMORY_MONITORING", "True").lower() == "true"
    FORCE_GC_AFTER_TRAINING: bool = os.getenv("FORCE_GC_AFTER_TRAINING", "True").lower() == "true"

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
        # Mask password in URL for display
        print(f"MongoDB URL: {self.MONGODB_URL.split('@')[-1] if '@' in self.MONGODB_URL and len(self.MONGODB_URL.split('@')) > 1 else self.MONGODB_URL}") 
        print(f"Database Name: {self.DATABASE_NAME}")
        print(f"Model Save Path: {self.MODEL_SAVE_PATH}")
        print(f"Retrain Interval (Minutes): {self.MODEL_RETRAIN_INTERVAL_MINUTES}") # Changed to minutes
        print(f"Forecast Horizon (Days): {self.FORECAST_HORIZON}")
        print(f"Anomaly Threshold: {self.ANOMALY_THRESHOLD}")
        print(f"Data Collection Days: {self.DATA_COLLECTION_DAYS}")
        print(f"CORS Origins: {self.CORS_ORIGINS}")
        print(f"Memory Safe Mode: {self.MEMORY_SAFE_MODE}")
        print(f"Max Parallel Models: {self.MAX_PARALLEL_MODELS}")
        print(f"Max Users for Similarity: {self.MAX_USERS_FOR_SIMILARITY}")
        print(f"Max Transactions Chunk: {self.MAX_TRANSACTIONS_CHUNK}")
        print(f"Max Activities Chunk: {self.MAX_ACTIVITIES_CHUNK}")
        print(f"Enable Memory Monitoring: {self.ENABLE_MEMORY_MONITORING}")
        print(f"Force GC After Training: {self.FORCE_GC_AFTER_TRAINING}")
        print("--------------------------------\n")

# Instantiate config
settings = Config()

if __name__ == "__main__":
    settings.display_config()