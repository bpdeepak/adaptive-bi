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