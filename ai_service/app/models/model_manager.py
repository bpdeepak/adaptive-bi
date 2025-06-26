# ai_service/app/models/model_manager.py
import asyncio
from datetime import datetime
import pandas as pd
from app.config import settings
from app.utils.logger import logger
from app.database import get_database, get_sync_database, connect_to_sync_database, close_sync_database_connection
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

        self.models_loaded = (self.forecasting_model.is_trained and
                              self.anomaly_model.is_trained and
                              self.recommendation_model.is_trained)
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

        # Ensure sync DB connection for DataProcessor if async is not passed directly
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
            # For anomaly detection, we can use transaction total amount or user activity features
            anomaly_df = await data_processor.get_transactions_data() # Example: using transactions for anomalies
            if not anomaly_df.empty:
                anomaly_features = ['totalAmount', 'quantity'] # Example features for anomaly
                # Ensure numerical columns for anomaly detection
                anomaly_df['totalAmount'] = pd.to_numeric(anomaly_df['totalAmount'], errors='coerce').fillna(0)
                anomaly_df['quantity'] = pd.to_numeric(anomaly_df['quantity'], errors='coerce').fillna(0)
                
                # Check if selected features are in the DataFrame and are numerical
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
            self.models_loaded = (self.forecasting_model.is_trained and
                                  self.anomaly_model.is_trained and
                                  self.recommendation_model.is_trained)
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