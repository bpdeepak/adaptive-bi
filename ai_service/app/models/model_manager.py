# ai_service/app/models/model_manager.py
import asyncio
import gc
from datetime import datetime
from typing import Dict, Any
import pandas as pd
import numpy as np
from app.config import settings
from app.utils.logger import logger
from app.database import get_database, get_sync_database, connect_to_sync_database, close_sync_database_connection
from app.services.data_processor import DataProcessor
from app.services.performance_tracker import performance_tracker
from app.models.forecasting import ForecastingModel
from app.models.anomaly_detection import AnomalyDetectionModel
from app.models.recommendation import RecommendationModel
from app.models.advanced_models import DynamicPricingModel, ChurnPredictionModel
from app.models.knowledge_graph import CustomerBehaviorGraph, MemoryMonitor
from app.models.explainable_ai import ExplainableAI

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
        # Phase 3 models
        self.forecasting_model = None
        self.anomaly_model = None
        self.recommendation_model = None
        
        # Phase 4 advanced models
        self.pricing_model = None
        self.churn_model = None
        self.knowledge_graph = None
        self.explainable_ai = None
        self.performance_tracker = performance_tracker  # Add performance tracker
        
        self.db_connected = False
        self.models_loaded = False
        self.phase4_models_loaded = False
        self.last_retrain_time = None
        self.memory_monitor = MemoryMonitor()  # Initialize memory monitor
        self._initialized = True # Mark as initialized

    async def initialize_models(self):
        """
        Initializes and loads/trains all models. Called once at application startup.
        """
        logger.info("Initializing AI models...")
        # Check database connection using the proper sync method
        try:
            db = get_database()
            self.db_connected = db is not None
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            self.db_connected = False

        # Initialize model instances
        self.forecasting_model = ForecastingModel()
        self.anomaly_model = AnomalyDetectionModel()
        self.recommendation_model = RecommendationModel()
        
        # Initialize Phase 4 models
        try:
            self.pricing_model = DynamicPricingModel()
            self.churn_model = ChurnPredictionModel()
            self.knowledge_graph = CustomerBehaviorGraph()
            self.explainable_ai = ExplainableAI()
            # Try to load existing explainer metadata
            try:
                explainer_load_path = f"{settings.MODEL_SAVE_PATH}/explainable_ai.pkl"
                self.explainable_ai.load_explainers(explainer_load_path)
            except Exception as e:
                logger.debug(f"Could not load explainer metadata: {e}")
                
            logger.info("Phase 4 advanced models initialized.")
        except ImportError as e:
            logger.warning(f"Phase 4 dependencies not available: {e}. Install requirements_phase4.txt")
            self.pricing_model = None
            self.churn_model = None
            self.knowledge_graph = None
            self.explainable_ai = None

        # Try to load models, if not found or training is forced, train them
        load_success_forecasting = self.forecasting_model.load_model()
        load_success_anomaly = self.anomaly_model.load_model()
        load_success_recommendation = self.recommendation_model.load_model()
        
        # Try to load Phase 4 models
        phase4_loaded = False
        if self.pricing_model and self.churn_model and self.knowledge_graph:
            try:
                # Try to load Phase 4 models from disk with correct paths
                pricing_path = f"{settings.MODEL_SAVE_PATH}/dynamic_pricing_model.pkl"
                churn_path = f"{settings.MODEL_SAVE_PATH}/churn_model.pkl"
                kg_path = f"{settings.MODEL_SAVE_PATH}/knowledge_graph.gml"
                
                pricing_loaded = getattr(self.pricing_model, 'load_model', lambda x: False)(pricing_path)
                churn_loaded = getattr(self.churn_model, 'load_model', lambda x: False)(churn_path)
                kg_loaded = getattr(self.knowledge_graph, 'load_graph', lambda x: False)(kg_path)
                
                phase4_loaded = pricing_loaded and churn_loaded and kg_loaded
                if phase4_loaded:
                    logger.info("Phase 4 models loaded successfully from disk.")
                    # Update loaded status if all models are loaded
                    self.phase4_models_loaded = True
                else:
                    logger.info("Phase 4 models not found on disk or failed to load. Will train during initialization.")
            except Exception as e:
                logger.warning(f"Phase 4 models could not be loaded: {e}")
                phase4_loaded = False

        # If Phase 3 models loaded successfully, check if we need to train Phase 4 models
        if load_success_forecasting and load_success_anomaly and load_success_recommendation:
            self.models_loaded = True
            logger.info("All Phase 3 models loaded successfully from disk.")
            
            # Always train Phase 4 models if they're not loaded or if forced
            if not phase4_loaded:
                logger.info("Phase 4 models not loaded. Initiating Phase 4 training...")
                await self.train_phase4_models()
                # Don't override phase4_models_loaded here - it's set by train_phase4_models()
        else:
            logger.warning("One or more Phase 3 models not found or failed to load. Initiating full training.")
            await self.train_all_models() # Perform initial training
            
        # Only set phase4_models_loaded if we didn't train (and thus it wasn't set by train_phase4_models)
        if phase4_loaded:
            self.phase4_models_loaded = phase4_loaded

        self.models_loaded = (self.forecasting_model.is_trained and
                              self.anomaly_model.is_trained and
                              self.recommendation_model.is_trained)
        
        if not self.models_loaded:
            logger.error("Not all Phase 3 models are trained/ready after initialization phase.")
        else:
            logger.info("Phase 3 models initialization completed successfully.")
            
        if self.phase4_models_loaded:
            logger.info("Phase 4 models initialization completed successfully.")
        else:
            logger.info("Phase 4 models will be trained or retrained during next training cycle.")
            
        logger.info(f"Model Manager initialization complete. Phase 3: {self.models_loaded}, Phase 4: {self.phase4_models_loaded}")

    async def train_all_models(self):
        """
        Orchestrates the training of all machine learning models.
        """
        logger.info("Starting full model retraining process...")

        try:
            db = get_database()
            if db is None:
                logger.error("Cannot train models: MongoDB connection not available.")
                return
                
            data_processor = DataProcessor(db=db)

            # Train Forecasting Model
            logger.info("Training Forecasting Model...")
            # For forecasting, we need more historical data to create sufficient daily time series
            # Use special method that gets distributed data across time rather than just recent data
            transactions_df = await data_processor.get_transactions_data_for_forecasting(days=180, limit=5000)
            daily_sales_df = data_processor.prepare_time_series_data(transactions_df, 'totalAmount', freq='D')
            if not daily_sales_df.empty and self.forecasting_model is not None:
                forecast_result = self.forecasting_model.train(daily_sales_df, target_col='totalAmount')
                logger.info(f"Forecasting Model training result: {forecast_result}")
                
                # Track performance and compare with previous training
                if forecast_result and forecast_result.get('status') == 'success' and 'metrics' in forecast_result:
                    metrics = forecast_result['metrics']
                    additional_info = {
                        'trained_on_samples': metrics.get('trained_on_samples'),
                        'evaluated_on_samples': metrics.get('evaluated_on_samples'),
                        'data_days': len(daily_sales_df) if not daily_sales_df.empty else 0,
                        'model_type': 'RandomForestRegressor'
                    }
                    
                    # Save current performance
                    performance_tracker.save_model_performance('forecasting', metrics, additional_info)
                    
                    # Compare with previous performance
                    comparison = performance_tracker.compare_with_previous_performance('forecasting', metrics)
                    performance_tracker.log_performance_comparison('forecasting', comparison)
            else:
                logger.warning("Skipping forecasting model training: No daily sales data or model not initialized.")

            # Train Anomaly Detection Model
            logger.info("Training Anomaly Detection Model...")
            anomaly_df = await data_processor.get_transactions_data(limit=500)  # Memory-safe limit
            if not anomaly_df.empty:
                # Use 'totalAmount' here
                anomaly_features = ['totalAmount', 'quantity']
                # Ensure numerical columns for anomaly detection
                anomaly_df['totalAmount'] = pd.to_numeric(anomaly_df['totalAmount'], errors='coerce').fillna(0)
                anomaly_df['quantity'] = pd.to_numeric(anomaly_df['quantity'], errors='coerce').fillna(0)
                
                valid_anomaly_features = [f for f in anomaly_features if f in anomaly_df.columns and pd.api.types.is_numeric_dtype(anomaly_df[f])]
                if not valid_anomaly_features:
                    logger.warning(f"No valid numeric features for anomaly detection training. Available numeric features: {[c for c in anomaly_df.columns if pd.api.types.is_numeric_dtype(anomaly_df[c])]}")
                elif self.anomaly_model is not None:
                    anomaly_result = self.anomaly_model.train(anomaly_df, features=valid_anomaly_features)
                    logger.info(f"Anomaly Detection Model training result: {anomaly_result}")
                    
                    # Track performance and compare with previous training
                    if anomaly_result and anomaly_result.get('status') == 'success' and 'metrics' in anomaly_result:
                        metrics = anomaly_result['metrics']
                        additional_info = {
                            'training_samples': len(anomaly_df),
                            'features_used': valid_anomaly_features,
                            'contamination': 0.01,  # Default contamination rate
                            'model_type': 'IsolationForest'
                        }
                        
                        # Save current performance
                        performance_tracker.save_model_performance('anomaly_detection', metrics, additional_info)
                        
                        # Compare with previous performance
                        comparison = performance_tracker.compare_with_previous_performance('anomaly_detection', metrics)
                        performance_tracker.log_performance_comparison('anomaly_detection', comparison)
                else:
                    logger.warning("Skipping anomaly detection model training: Model not initialized.")
            else:
                logger.warning("Skipping anomaly detection model training: No transaction data for anomalies.")

            # Train Recommendation Model
            logger.info("Training Recommendation Model...")
            if self.recommendation_model is not None:
                recommendation_result = await self.recommendation_model.train(data_processor)
                logger.info(f"Recommendation Model training result: {recommendation_result}")
                
                # Save performance metrics if training was successful
                if recommendation_result.get("status") == "success" and "metrics" in recommendation_result:
                    metrics = recommendation_result["metrics"]
                    performance_tracker.save_model_performance('recommendation', metrics)
                    comparison = performance_tracker.compare_with_previous_performance('recommendation', metrics)
                    performance_tracker.log_performance_comparison('recommendation', comparison)
                else:
                    logger.warning(f"Recommendation model training failed: {recommendation_result.get('message', 'Unknown error')}")
            else:
                logger.warning("Skipping recommendation model training: Model not initialized.")

            # Train Phase 4 Advanced Models
            logger.info("Training Phase 4 Advanced Models...")
            
            # Train Dynamic Pricing Model
            if self.pricing_model is not None:
                logger.info("Training Dynamic Pricing Model...")
                transactions_df = await data_processor.get_transactions_data()
                products_df = await data_processor.get_product_data()
                
                if not transactions_df.empty and not products_df.empty:
                    # Merge transaction and product data for pricing model
                    pricing_data = transactions_df.merge(
                        products_df[['productId', 'category', 'price']], 
                        on='productId', 
                        how='left'
                    )
                    
                    # Transform column names to match DynamicPricingModel expectations
                    # Note: DataProcessor already transforms totalPrice->totalAmount and transactionDate->timestamp
                    pricing_data = pricing_data.rename(columns={
                        'productId': 'product_id',
                        'userId': 'user_id',
                        'transactionId': 'transaction_id',
                        'timestamp': 'timestamp',  # Already transformed by DataProcessor
                        'totalAmount': 'amount'    # Already transformed by DataProcessor
                    })
                    
                    # Ensure timestamp is datetime (should already be done by DataProcessor)
                    if 'timestamp' in pricing_data.columns:
                        pricing_data['timestamp'] = pd.to_datetime(pricing_data['timestamp'])
                    
                    # Add missing columns that DynamicPricingModel expects
                    if 'stock_level' not in pricing_data.columns:
                        pricing_data['stock_level'] = 100  # Default stock level
                    
                    # Create optimal_price target (simplified approach)
                    if 'price' in pricing_data.columns:
                        # Use current price with small optimization factor as target
                        pricing_data['optimal_price'] = pricing_data['price'] * 1.05  # 5% optimization target
                    
                    # Verify all required columns are present
                    required_cols = ['product_id', 'timestamp', 'quantity', 'price', 'category']
                    missing_cols = [col for col in required_cols if col not in pricing_data.columns]
                    
                    if not missing_cols and len(pricing_data) > 10:
                        pricing_result = self.pricing_model.train(pricing_data, target_col='optimal_price')
                        if pricing_result['status'] == 'success':
                            # Save the model
                            save_path = f"{settings.MODEL_SAVE_PATH}/dynamic_pricing_model.pkl"
                            self.pricing_model.save_model(save_path)
                            logger.info(f"Dynamic Pricing Model training successful: {pricing_result}")
                        else:
                            logger.warning(f"Dynamic Pricing Model training failed: {pricing_result}")
                    else:
                        if missing_cols:
                            logger.warning(f"Missing required columns for pricing model: {missing_cols}")
                        else:
                            logger.warning("Insufficient data for pricing model training")
                else:
                    logger.warning("Skipping pricing model training: Missing transaction or product data")
            
            # Train Churn Prediction Model
            if self.churn_model is not None:
                logger.info("Training Churn Prediction Model...")
                
                try:
                    # Fetch data directly from database
                    db = get_database()
                    users_cursor = db.users.find({})
                    users_list = await users_cursor.to_list(length=None)
                    users_df = pd.DataFrame(users_list) if users_list else pd.DataFrame()
                    
                    transactions_df = await data_processor.get_transactions_data()
                    
                    if not users_df.empty and not transactions_df.empty:
                        # Transform column names to match ChurnPredictionModel expectations
                        # Note: DataProcessor already transforms totalPrice->totalAmount and transactionDate->timestamp
                        transactions_df = transactions_df.rename(columns={
                            'productId': 'product_id',
                            'userId': 'user_id', 
                            'transactionId': 'transaction_id',
                            'timestamp': 'timestamp',   # Already transformed by DataProcessor
                            'totalAmount': 'amount'     # Already transformed by DataProcessor
                        })
                        
                        users_df = users_df.rename(columns={
                            'userId': 'user_id'
                        })
                        
                        # Ensure timestamp is datetime (should already be done by DataProcessor)
                        if 'timestamp' in transactions_df.columns:
                            transactions_df['timestamp'] = pd.to_datetime(transactions_df['timestamp'])
                        
                        # Simple churn logic: users who haven't transacted in 30+ days
                        if 'timestamp' in transactions_df.columns:
                            last_transaction = transactions_df.groupby('user_id')['timestamp'].max().reset_index()
                            
                            # Calculate days since last transaction  
                            current_time = pd.Timestamp.now()
                            last_transaction['days_since_last'] = last_transaction['timestamp'].apply(
                                lambda x: (current_time - x).days
                            )
                            
                            # Create churn labels
                            churn_data = users_df.merge(last_transaction, on='user_id', how='left')
                            churn_data['days_since_last'].fillna(365, inplace=True)  # Assume 365 days for users with no transactions
                            churn_data['is_churned'] = (churn_data['days_since_last'] > 30).astype(int)
                            
                            # Add RFM and behavioral features by merging transaction data
                            user_stats = transactions_df.groupby('user_id').agg({
                                'amount': ['sum', 'mean', 'count'],
                                'timestamp': 'max'
                            }).reset_index()
                            user_stats.columns = ['user_id', 'total_spent', 'avg_order_value', 'frequency', 'last_purchase']
                            
                            churn_training_data = churn_data.merge(user_stats, on='user_id', how='left')
                            churn_training_data.fillna(0, inplace=True)
                            
                            # Merge with full transaction data for features that need transaction details
                            enhanced_data = transactions_df.merge(
                                churn_training_data[['user_id', 'is_churned']], 
                                on='user_id', 
                                how='left'
                            )
                            enhanced_data['is_churned'].fillna(0, inplace=True)
                            
                            # Sample down the data if too large
                            if len(enhanced_data) > 10000:
                                enhanced_data = enhanced_data.sample(n=10000, random_state=42)
                            
                            if len(enhanced_data) > 10:
                                churn_result = self.churn_model.train(enhanced_data)
                                if churn_result['status'] == 'success':
                                    # Save the model
                                    save_path = f"{settings.MODEL_SAVE_PATH}/churn_model.pkl"
                                    self.churn_model.save_model(save_path)
                                    
                                    # Track performance improvement for train_all_models
                                    if hasattr(self, 'performance_tracker') and self.performance_tracker:
                                        self.performance_tracker.save_model_performance(
                                            model_name='churn',
                                            metrics={
                                                'auc_score': churn_result.get('auc_score', 0),
                                                'accuracy': churn_result.get('classification_report', {}).get('accuracy', 0),
                                                'churn_rate': churn_result.get('churn_rate', 0)
                                            }
                                        )
                                    
                                    logger.info(f"Churn Prediction Model training successful: {churn_result}")
                                else:
                                    logger.warning(f"Churn Prediction Model training failed: {churn_result}")
                            else:
                                logger.warning("Insufficient data for churn model training")
                        else:
                            logger.warning("Missing timestamp column for churn model training")
                    else:
                        logger.warning("Skipping churn model training: Missing user or transaction data")
                except Exception as e:
                    logger.error(f"Error in churn model training: {e}")
                    logger.warning("Skipping churn model training due to error")
            
            # Build Knowledge Graph
            if self.knowledge_graph is not None:
                logger.info("Building Knowledge Graph...")
                
                try:
                    # Fetch data directly from database
                    db = get_database()
                    
                    users_cursor = db.users.find({})
                    users_list = await users_cursor.to_list(length=None)
                    users_df = pd.DataFrame(users_list) if users_list else pd.DataFrame()
                    
                    products_df = await data_processor.get_product_data()
                    transactions_df = await data_processor.get_transactions_data()
                    
                    if not users_df.empty and not products_df.empty and not transactions_df.empty:
                        # Transform column names to match knowledge graph expectations
                        # Note: DataProcessor already transforms totalPrice->totalAmount and transactionDate->timestamp
                        transactions_df = transactions_df.rename(columns={
                            'productId': 'product_id',
                            'userId': 'user_id',
                            'transactionId': 'transaction_id', 
                            'timestamp': 'timestamp',   # Already transformed by DataProcessor
                            'totalAmount': 'amount'     # Already transformed by DataProcessor
                        })
                        
                        users_df = users_df.rename(columns={
                            'userId': 'user_id'
                        })
                        
                        products_df = products_df.rename(columns={
                            'productId': 'product_id'
                        })
                        
                        # Add category to transactions if missing
                        if 'category' not in transactions_df.columns:
                            transactions_df = transactions_df.merge(
                                products_df[['product_id', 'category']], 
                                on='product_id', 
                                how='left'
                            )
                            transactions_df['category'].fillna('unknown', inplace=True)
                        
                        # Ensure amount column exists
                        if 'amount' not in transactions_df.columns and 'totalAmount' in transactions_df.columns:
                            transactions_df['amount'] = transactions_df['totalAmount']
                        
                        kg_result = self.knowledge_graph.build_graph_from_data(transactions_df, products_df, users_df)
                        if kg_result['status'] == 'success':
                            # Save the knowledge graph
                            save_path = f"{settings.MODEL_SAVE_PATH}/knowledge_graph.gml"
                            self.knowledge_graph.save_graph(save_path)
                            logger.info(f"Knowledge Graph building successful: {kg_result}")
                        else:
                            logger.warning(f"Knowledge Graph building failed: {kg_result}")
                    else:
                        logger.warning("Skipping knowledge graph building: Missing required data")
                except Exception as e:
                    logger.error(f"Error in knowledge graph building: {e}")
                    logger.warning("Skipping knowledge graph building due to error")

            self.last_retrain_time = datetime.now()
            
            # Update loading status for both Phase 3 and Phase 4 models
            phase3_loaded = (
                self.forecasting_model is not None and self.forecasting_model.is_trained and
                self.anomaly_model is not None and self.anomaly_model.is_trained and
                self.recommendation_model is not None and self.recommendation_model.is_trained
            )
            
            # Check if Phase 4 models are trained (they may not have is_trained attribute)
            phase4_loaded = True  # Assume trained if no errors occurred
            if self.pricing_model is not None:
                phase4_loaded = phase4_loaded and hasattr(self.pricing_model, 'model') and self.pricing_model.model is not None
            if self.churn_model is not None:
                phase4_loaded = phase4_loaded and hasattr(self.churn_model, 'model') and self.churn_model.model is not None
            if self.knowledge_graph is not None:
                phase4_loaded = phase4_loaded and hasattr(self.knowledge_graph, '_is_built') and self.knowledge_graph._is_built
            
            self.models_loaded = phase3_loaded
            self.phase4_models_loaded = phase4_loaded
            
            # Setup ExplainableAI for retrained Phase 4 models
            if phase4_loaded:
                await self._setup_explainable_ai()
                
                # Log explainer status after setup
                explainer_status = self.get_explainer_status()
                if explainer_status['status'] == 'success':
                    logger.info(f"ExplainableAI setup completed during retraining: {explainer_status['total_explainers']} explainers available")
                    for explainer_name, explainer_info in explainer_status['explainers'].items():
                        if explainer_info['available']:
                            logger.info(f"  - {explainer_name}: Available ({explainer_info.get('feature_count', 'N/A')} features)")
                else:
                    logger.warning(f"ExplainableAI setup failed during retraining: {explainer_status.get('message', 'Unknown error')}")
            
            logger.info(f"Phase 3 models loaded: {phase3_loaded}")
            logger.info(f"Phase 4 models loaded: {phase4_loaded}")
            logger.info("Full model retraining process completed.")

        except Exception as e:
            logger.error(f"Error during full model retraining: {e}", exc_info=True)
            self.models_loaded = False

    async def train_phase4_models(self):
        """
        Train only Phase 4 advanced models (pricing, churn, knowledge graph).
        """
        if not self.db_connected:
            logger.error("Cannot train Phase 4 models: MongoDB connection not established.")
            return

        logger.info("Starting Phase 4 model training process...")

        try:
            db = get_database()
            data_processor = DataProcessor(db=db)
            
            # Train Dynamic Pricing Model
            if self.pricing_model is not None:
                logger.info("Training Dynamic Pricing Model...")
                transactions_df = await data_processor.get_transactions_data()
                products_df = await data_processor.get_product_data()
                
                if not transactions_df.empty and not products_df.empty:
                    # Merge transaction and product data for pricing model
                    pricing_data = transactions_df.merge(
                        products_df[['productId', 'category', 'price']], 
                        on='productId', 
                        how='left'
                    )
                    
                    # Transform column names to match DynamicPricingModel expectations
                    # Note: DataProcessor already transforms totalPrice->totalAmount and transactionDate->timestamp
                    pricing_data = pricing_data.rename(columns={
                        'productId': 'product_id',
                        'userId': 'user_id',
                        'transactionId': 'transaction_id',
                        'timestamp': 'timestamp',  # Already transformed by DataProcessor
                        'totalAmount': 'amount'    # Already transformed by DataProcessor
                    })
                    
                    # Ensure timestamp is datetime (should already be done by DataProcessor)
                    if 'timestamp' in pricing_data.columns:
                        pricing_data['timestamp'] = pd.to_datetime(pricing_data['timestamp'])
                    
                    # Add missing columns that DynamicPricingModel expects
                    if 'stock_level' not in pricing_data.columns:
                        pricing_data['stock_level'] = 100  # Default stock level
                    
                    # Create optimal_price target (simplified approach)
                    if 'price' in pricing_data.columns:
                        # Use current price with small optimization factor as target
                        pricing_data['optimal_price'] = pricing_data['price'] * 1.05  # 5% optimization target
                    
                    # Verify all required columns are present
                    required_cols = ['product_id', 'timestamp', 'quantity', 'price', 'category']
                    missing_cols = [col for col in required_cols if col not in pricing_data.columns]
                    
                    if not missing_cols and len(pricing_data) > 10:
                        pricing_result = self.pricing_model.train(pricing_data, target_col='optimal_price')
                        if pricing_result['status'] == 'success':
                            # Save the model
                            save_path = f"{settings.MODEL_SAVE_PATH}/dynamic_pricing_model.pkl"
                            self.pricing_model.save_model(save_path)
                            logger.info(f"Dynamic Pricing Model training successful: {pricing_result}")
                        else:
                            logger.warning(f"Dynamic Pricing Model training failed: {pricing_result}")
                    else:
                        if missing_cols:
                            logger.warning(f"Missing required columns for pricing model: {missing_cols}")
                        else:
                            logger.warning("Insufficient data for pricing model training")
                else:
                    logger.warning("Skipping pricing model training: Missing transaction or product data")
            
            # Train Churn Prediction Model
            if self.churn_model is not None:
                logger.info("Training Churn Prediction Model...")
                
                try:
                    # Fetch data directly from database
                    db = get_database()
                    users_cursor = db.users.find({})
                    users_list = await users_cursor.to_list(length=None)
                    users_df = pd.DataFrame(users_list) if users_list else pd.DataFrame()
                    
                    transactions_df = await data_processor.get_transactions_data()
                    
                    if not users_df.empty and not transactions_df.empty:
                        # Transform column names to match ChurnPredictionModel expectations
                        # Note: DataProcessor already transforms totalPrice->totalAmount and transactionDate->timestamp
                        transactions_df = transactions_df.rename(columns={
                            'productId': 'product_id',
                            'userId': 'user_id', 
                            'transactionId': 'transaction_id',
                            'timestamp': 'timestamp',   # Already transformed by DataProcessor
                            'totalAmount': 'amount'     # Already transformed by DataProcessor
                        })
                        
                        users_df = users_df.rename(columns={
                            'userId': 'user_id'
                        })
                        
                        # Ensure timestamp is datetime (should already be done by DataProcessor)
                        if 'timestamp' in transactions_df.columns:
                            transactions_df['timestamp'] = pd.to_datetime(transactions_df['timestamp'])
                        
                        # Simple churn logic: users who haven't transacted in 30+ days
                        if 'timestamp' in transactions_df.columns:
                            last_transaction = transactions_df.groupby('user_id')['timestamp'].max().reset_index()
                            
                            # Calculate days since last transaction  
                            current_time = pd.Timestamp.now()
                            last_transaction['days_since_last'] = last_transaction['timestamp'].apply(
                                lambda x: (current_time - x).days
                            )
                            
                            # Create churn labels
                            churn_data = users_df.merge(last_transaction, on='user_id', how='left')
                            churn_data['days_since_last'].fillna(365, inplace=True)  # Assume 365 days for users with no transactions
                            churn_data['is_churned'] = (churn_data['days_since_last'] > 30).astype(int)
                            
                            # Add RFM and behavioral features by merging transaction data
                            user_stats = transactions_df.groupby('user_id').agg({
                                'amount': ['sum', 'mean', 'count'],
                                'timestamp': 'max'
                            }).reset_index()
                            user_stats.columns = ['user_id', 'total_spent', 'avg_order_value', 'frequency', 'last_purchase']
                            
                            churn_training_data = churn_data.merge(user_stats, on='user_id', how='left')
                            churn_training_data.fillna(0, inplace=True)
                            
                            # Merge with full transaction data for features that need transaction details
                            enhanced_data = transactions_df.merge(
                                churn_training_data[['user_id', 'is_churned']], 
                                on='user_id', 
                                how='left'
                            )
                            enhanced_data['is_churned'].fillna(0, inplace=True)
                            
                            # Sample down the data if too large
                            if len(enhanced_data) > 10000:
                                enhanced_data = enhanced_data.sample(n=10000, random_state=42)
                            
                            if len(enhanced_data) > 10:
                                churn_result = self.churn_model.train(enhanced_data)
                                if churn_result['status'] == 'success':
                                    # Save the model
                                    save_path = f"{settings.MODEL_SAVE_PATH}/churn_model.pkl"
                                    self.churn_model.save_model(save_path)
                                    
                                    # Track performance improvement for train_all_models
                                    if hasattr(self, 'performance_tracker') and self.performance_tracker:
                                        self.performance_tracker.save_model_performance(
                                            model_name='churn',
                                            metrics={
                                                'auc_score': churn_result.get('auc_score', 0),
                                                'accuracy': churn_result.get('classification_report', {}).get('accuracy', 0),
                                                'churn_rate': churn_result.get('churn_rate', 0)
                                            }
                                        )
                                    
                                    logger.info(f"Churn Prediction Model training successful: {churn_result}")
                                else:
                                    logger.warning(f"Churn Prediction Model training failed: {churn_result}")
                            else:
                                logger.warning("Insufficient data for churn model training")
                        else:
                            logger.warning("Missing timestamp column for churn model training")
                    else:
                        logger.warning("Skipping churn model training: Missing user or transaction data")
                except Exception as e:
                    logger.error(f"Error in churn model training: {e}")
                    logger.warning("Skipping churn model training due to error")
            
            # Build Knowledge Graph
            if self.knowledge_graph is not None:
                logger.info("Building Knowledge Graph...")
                
                try:
                    # Fetch data directly from database
                    db = get_database()
                    
                    users_cursor = db.users.find({})
                    users_list = await users_cursor.to_list(length=None)
                    users_df = pd.DataFrame(users_list) if users_list else pd.DataFrame()
                    
                    products_df = await data_processor.get_product_data()
                    transactions_df = await data_processor.get_transactions_data()
                    
                    if not users_df.empty and not products_df.empty and not transactions_df.empty:
                        # Transform column names to match knowledge graph expectations
                        # Note: DataProcessor already transforms totalPrice->totalAmount and transactionDate->timestamp
                        transactions_df = transactions_df.rename(columns={
                            'productId': 'product_id',
                            'userId': 'user_id',
                            'transactionId': 'transaction_id', 
                            'timestamp': 'timestamp',   # Already transformed by DataProcessor
                            'totalAmount': 'amount'     # Already transformed by DataProcessor
                        })
                        
                        users_df = users_df.rename(columns={
                            'userId': 'user_id'
                        })
                        
                        products_df = products_df.rename(columns={
                            'productId': 'product_id'
                        })
                        
                        # Add category to transactions if missing
                        if 'category' not in transactions_df.columns:
                            transactions_df = transactions_df.merge(
                                products_df[['product_id', 'category']], 
                                on='product_id', 
                                how='left'
                            )
                            transactions_df['category'].fillna('unknown', inplace=True)
                        
                        # Ensure amount column exists
                        if 'amount' not in transactions_df.columns and 'totalAmount' in transactions_df.columns:
                            transactions_df['amount'] = transactions_df['totalAmount']
                        
                        kg_result = self.knowledge_graph.build_graph_from_data(transactions_df, products_df, users_df)
                        if kg_result['status'] == 'success':
                            # Save the knowledge graph
                            save_path = f"{settings.MODEL_SAVE_PATH}/knowledge_graph.gml"
                            self.knowledge_graph.save_graph(save_path)
                            logger.info(f"Knowledge Graph building successful: {kg_result}")
                        else:
                            logger.warning(f"Knowledge Graph building failed: {kg_result}")
                    else:
                        logger.warning("Skipping knowledge graph building: Missing required data")
                except Exception as e:
                    logger.error(f"Error in knowledge graph building: {e}")
                    logger.warning("Skipping knowledge graph building due to error")

            # Update Phase 4 loading status
            phase4_loaded = True  # Assume trained if no errors occurred
            if self.pricing_model is not None:
                phase4_loaded = phase4_loaded and hasattr(self.pricing_model, 'model') and self.pricing_model.model is not None
            if self.churn_model is not None:
                phase4_loaded = phase4_loaded and hasattr(self.churn_model, 'model') and self.churn_model.model is not None
            if self.knowledge_graph is not None:
                phase4_loaded = phase4_loaded and hasattr(self.knowledge_graph, '_is_built') and self.knowledge_graph._is_built
            
            self.phase4_models_loaded = phase4_loaded
            
            # Setup ExplainableAI for trained models
            if phase4_loaded:
                await self._setup_explainable_ai()
                
                # Log explainer status after setup
                explainer_status = self.get_explainer_status()
                if explainer_status['status'] == 'success':
                    logger.info(f"ExplainableAI setup completed: {explainer_status['total_explainers']} explainers available")
                    for explainer_name, explainer_info in explainer_status['explainers'].items():
                        if explainer_info['available']:
                            logger.info(f"  - {explainer_name}: Available ({explainer_info.get('feature_count', 'N/A')} features)")
                else:
                    logger.warning(f"ExplainableAI setup failed: {explainer_status.get('message', 'Unknown error')}")
            
            logger.info(f"Phase 4 models training completed. Loaded status: {phase4_loaded}")

        except Exception as e:
            logger.error(f"Error during Phase 4 model training: {e}", exc_info=True)
            self.phase4_models_loaded = False

    async def _setup_explainable_ai(self):
        """Set up SHAP and LIME explainers for trained Phase 4 models."""
        try:
            logger.info("Setting up ExplainableAI explainers for Phase 4 models...")
            
            if self.explainable_ai is None:
                logger.warning("ExplainableAI not initialized")
                return
            
            # Get some training data for explainer setup
            db = get_database()
            data_processor = DataProcessor(db)
            
            # Setup explainer for Dynamic Pricing Model
            if self.pricing_model is not None and hasattr(self.pricing_model, 'model') and self.pricing_model.model is not None:
                try:
                    logger.info("Setting up explainer for Dynamic Pricing Model...")
                    # Get sample pricing data for explainer setup
                    transactions_df = await data_processor.get_transactions_data()
                    products_df = await data_processor.get_product_data()
                    
                    if not transactions_df.empty and not products_df.empty:
                        # Convert ObjectIds to strings but preserve datetime columns
                        for col in transactions_df.columns:
                            if col not in ['timestamp'] and transactions_df[col].dtype == 'object':
                                try:
                                    # Check if it contains ObjectId-like strings
                                    if transactions_df[col].astype(str).str.len().eq(24).any():
                                        transactions_df[col] = transactions_df[col].astype(str)
                                except:
                                    pass
                        
                        for col in products_df.columns:
                            if products_df[col].dtype == 'object':
                                try:
                                    # Check if it contains ObjectId-like strings
                                    if products_df[col].astype(str).str.len().eq(24).any():
                                        products_df[col] = products_df[col].astype(str)
                                except:
                                    pass
                        
                        # Ensure timestamp is properly formatted
                        if 'timestamp' in transactions_df.columns:
                            transactions_df['timestamp'] = pd.to_datetime(transactions_df['timestamp'], errors='coerce')
                        
                        # Prepare data similar to training
                        pricing_data = transactions_df.merge(
                            products_df[['productId', 'category', 'price']], 
                            on='productId', 
                            how='left'
                        )
                        pricing_data = pricing_data.rename(columns={
                            'productId': 'product_id',
                            'userId': 'user_id',
                            'transactionId': 'transaction_id',
                            'timestamp': 'timestamp',
                            'totalAmount': 'amount'
                        })
                        
                        if 'stock_level' not in pricing_data.columns:
                            pricing_data['stock_level'] = 100
                        
                        # Get features that the model was trained on
                        try:
                            features_for_explainer = self.pricing_model.prepare_features(pricing_data)
                            # Select only numeric columns for explainer
                            numeric_cols = features_for_explainer.select_dtypes(include=[np.number]).columns
                            features_for_explainer = features_for_explainer[numeric_cols]
                            
                            # Remove columns that are likely IDs or have too many unique values
                            cols_to_keep = []
                            for col in features_for_explainer.columns:
                                if features_for_explainer[col].nunique() / len(features_for_explainer) < 0.9:
                                    cols_to_keep.append(col)
                            features_for_explainer = features_for_explainer[cols_to_keep]
                            
                        except Exception as prep_error:
                            logger.warning(f"Error in pricing model prepare_features: {prep_error}")
                            # Create basic numeric features
                            try:
                                features_for_explainer = pd.DataFrame({
                                    'quantity': pd.to_numeric(pricing_data['quantity'], errors='coerce'),
                                    'price': pd.to_numeric(pricing_data['price'], errors='coerce'),
                                    'hour': pd.to_datetime(pricing_data['timestamp'], errors='coerce').dt.hour,
                                    'day_of_week': pd.to_datetime(pricing_data['timestamp'], errors='coerce').dt.dayofweek
                                }).fillna(0).head(100)
                            except Exception:
                                # Fallback to minimal features
                                features_for_explainer = pd.DataFrame({
                                    'quantity': [1.0] * min(100, len(pricing_data)),
                                    'price': [10.0] * min(100, len(pricing_data))
                                })
                        if features_for_explainer is not None and not features_for_explainer.empty:
                            result = self.explainable_ai.setup_explainer(
                                model=self.pricing_model.model,
                                X_train=features_for_explainer,
                                model_name='dynamic_pricing',
                                explainer_type='both'
                            )
                            if result['status'] == 'success':
                                logger.info(f"Dynamic Pricing explainer setup successful: {result['feature_count']} features")
                            else:
                                logger.warning(f"Dynamic Pricing explainer setup failed: {result.get('message', 'Unknown error')}")
                        else:
                            logger.warning("No pricing features available for explainer setup")
                    else:
                        logger.warning("No pricing data available for explainer setup")
                except Exception as e:
                    logger.error(f"Error setting up Dynamic Pricing explainer: {e}")

            # Setup explainer for Churn Prediction Model
            if self.churn_model is not None and hasattr(self.churn_model, 'model') and self.churn_model.model is not None:
                try:
                    logger.info("Setting up explainer for Churn Prediction Model...")
                    # Get sample data for churn explainer setup
                    transactions_df = await data_processor.get_transactions_data()
                    
                    if not transactions_df.empty:
                        # Convert ObjectIds to strings but preserve datetime and numeric columns
                        for col in transactions_df.columns:
                            if col not in ['timestamp'] and transactions_df[col].dtype == 'object':
                                try:
                                    # Check if it contains ObjectId-like strings  
                                    if transactions_df[col].astype(str).str.len().eq(24).any():
                                        transactions_df[col] = transactions_df[col].astype(str)
                                except:
                                    pass
                        
                        # Ensure timestamp is properly formatted
                        if 'timestamp' in transactions_df.columns:
                            transactions_df['timestamp'] = pd.to_datetime(transactions_df['timestamp'], errors='coerce')
                        
                        # Prepare sample features for explainer setup
                        features_for_explainer = None
                        try:
                            features_for_explainer = self.churn_model.prepare_features(transactions_df)
                            if features_for_explainer is not None and not features_for_explainer.empty:
                                # Select only numeric columns for explainer
                                numeric_cols = features_for_explainer.select_dtypes(include=[np.number]).columns
                                features_for_explainer = features_for_explainer[numeric_cols]
                                
                                # Remove user_id column if present as it's an identifier
                                if 'user_id' in features_for_explainer.columns:
                                    features_for_explainer = features_for_explainer.drop(['user_id'], axis=1)
                                
                                # Keep columns that are meaningful for explaining churn
                                # (avoid removing too many based on uniqueness since churn features are aggregated)
                                cols_to_keep = []
                                for col in features_for_explainer.columns:
                                    # Keep the column if it has reasonable variance and isn't all zeros
                                    try:
                                        col_var = features_for_explainer[col].var()
                                        if (features_for_explainer[col].nunique() > 1 and 
                                            pd.notna(col_var) and isinstance(col_var, (int, float)) and col_var > 0):
                                            cols_to_keep.append(col)
                                    except (TypeError, ValueError):
                                        # Skip columns that can't have variance calculated
                                        continue
                                
                                if cols_to_keep:
                                    features_for_explainer = features_for_explainer[cols_to_keep]
                                else:
                                    # If no columns pass the filter, keep the most important churn features
                                    important_churn_cols = ['frequency', 'total_spent', 'avg_order_value', 'recency_days']
                                    available_cols = [col for col in important_churn_cols if col in features_for_explainer.columns]
                                    if available_cols:
                                        features_for_explainer = features_for_explainer[available_cols]
                                    else:
                                        features_for_explainer = None
                            else:
                                features_for_explainer = None
                                
                        except Exception as prep_error:
                            logger.warning(f"Error in churn model prepare_features: {prep_error}")
                            features_for_explainer = None
                        
                        # If primary feature preparation failed, create fallback features
                        if features_for_explainer is None or features_for_explainer.empty:
                            try:
                                # Create basic aggregated features as fallback
                                if 'user_id' in transactions_df.columns and 'amount' in transactions_df.columns:
                                    user_features = transactions_df.groupby('user_id').agg({
                                        'amount': ['sum', 'mean', 'count'],
                                        'product_id': 'nunique' if 'product_id' in transactions_df.columns else lambda x: 1
                                    }).reset_index()
                                    user_features.columns = ['user_id', 'total_spent', 'avg_order_value', 'frequency', 'product_diversity']
                                    
                                    # Keep only numeric columns and drop user_id
                                    features_for_explainer = user_features.select_dtypes(include=[np.number])
                                else:
                                    # Ultimate fallback with dummy data
                                    n_samples = min(100, len(transactions_df))
                                    features_for_explainer = pd.DataFrame({
                                        'total_spent': np.random.uniform(50, 500, n_samples),
                                        'frequency': np.random.randint(1, 20, n_samples),
                                        'avg_order_value': np.random.uniform(10, 100, n_samples),
                                        'recency_days': np.random.randint(1, 90, n_samples)
                                    })
                                    
                            except Exception as fallback_error:
                                logger.warning(f"Fallback feature creation failed: {fallback_error}")
                                # Final fallback with minimal dummy data
                                features_for_explainer = pd.DataFrame({
                                    'total_spent': [100.0, 200.0, 150.0, 300.0, 250.0],
                                    'frequency': [5.0, 10.0, 7.0, 15.0, 12.0],
                                    'avg_order_value': [20.0, 25.0, 30.0, 18.0, 22.0],
                                    'recency_days': [10.0, 5.0, 15.0, 3.0, 8.0]
                                })
                        
                        # At this point we should always have features_for_explainer with data
                        if features_for_explainer is not None and not features_for_explainer.empty:
                            result = self.explainable_ai.setup_explainer(
                                model=self.churn_model.model,
                                X_train=features_for_explainer,
                                model_name='churn_prediction',
                                explainer_type='both'
                            )
                            if result['status'] == 'success':
                                logger.info(f"Churn Prediction explainer setup successful: {result['feature_count']} features")
                            else:
                                logger.warning(f"Churn Prediction explainer setup failed: {result.get('message', 'Unknown error')}")
                        else:
                            logger.warning("Failed to create any churn features for explainer setup")
                    else:
                        logger.warning("No churn data available for explainer setup")
                except Exception as e:
                    logger.error(f"Error setting up Churn Prediction explainer: {e}")

            logger.info("ExplainableAI setup completed")
            
            # Save explainer metadata
            try:
                explainer_save_path = f"{settings.MODEL_SAVE_PATH}/explainable_ai.pkl"
                if self.explainable_ai.save_explainers(explainer_save_path):
                    logger.info("ExplainableAI metadata saved successfully")
                else:
                    logger.warning("Failed to save ExplainableAI metadata")
            except Exception as e:
                logger.error(f"Error saving ExplainableAI metadata: {e}")
            
        except Exception as e:
            logger.error(f"Error during ExplainableAI setup: {e}", exc_info=True)

    def get_explainer_status(self) -> Dict[str, Any]:
        """Get the status of all ExplainableAI explainers."""
        try:
            if self.explainable_ai is None:
                return {'status': 'error', 'message': 'ExplainableAI not initialized'}
            
            status = {
                'status': 'success',
                'explainers': {},
                'total_explainers': 0
            }
            
            # Check SHAP explainers
            if hasattr(self.explainable_ai, 'shap_explainers'):
                for model_name, explainer in self.explainable_ai.shap_explainers.items():
                    status['explainers'][f'{model_name}_shap'] = {
                        'type': 'SHAP',
                        'model': model_name,
                        'available': explainer is not None,
                        'explainer_type': type(explainer).__name__ if explainer else None
                    }
                    if explainer is not None:
                        status['total_explainers'] += 1
            
            # Check LIME explainers
            if hasattr(self.explainable_ai, 'lime_explainers'):
                for model_name, explainer in self.explainable_ai.lime_explainers.items():
                    status['explainers'][f'{model_name}_lime'] = {
                        'type': 'LIME',
                        'model': model_name,
                        'available': explainer is not None,
                        'explainer_type': type(explainer).__name__ if explainer else None
                    }
                    if explainer is not None:
                        status['total_explainers'] += 1
            
            # Check feature names
            if hasattr(self.explainable_ai, 'feature_names'):
                for model_name, features in self.explainable_ai.feature_names.items():
                    if f'{model_name}_shap' in status['explainers']:
                        status['explainers'][f'{model_name}_shap']['feature_count'] = len(features) if features else 0
                    if f'{model_name}_lime' in status['explainers']:
                        status['explainers'][f'{model_name}_lime']['feature_count'] = len(features) if features else 0
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting explainer status: {e}")
            return {'status': 'error', 'message': str(e)}

    async def test_explainers(self) -> Dict[str, Any]:
        """Test the ExplainableAI explainers with sample data."""
        try:
            logger.info("Testing ExplainableAI explainers...")
            
            if self.explainable_ai is None:
                return {'status': 'error', 'message': 'ExplainableAI not initialized'}
            
            test_results = {
                'status': 'success',
                'tests': {},
                'summary': {
                    'total_tests': 0,
                    'passed_tests': 0,
                    'failed_tests': 0
                }
            }
            
            # Get sample data
            db = get_database()
            data_processor = DataProcessor(db)
            
            # Test Dynamic Pricing explainer
            if (self.pricing_model is not None and 
                hasattr(self.pricing_model, 'model') and 
                self.pricing_model.model is not None and
                'dynamic_pricing' in self.explainable_ai.shap_explainers):
                
                try:
                    logger.info("Testing Dynamic Pricing explainer...")
                    transactions_df = await data_processor.get_transactions_data()
                    if not transactions_df.empty:
                        # Get a single sample for explanation
                        sample_features = self.pricing_model.prepare_features(transactions_df.head(1))
                        if sample_features is not None and not sample_features.empty:
                            explanation = self.explainable_ai.explain_prediction_shap(
                                model=self.pricing_model.model,
                                X_instance=sample_features,
                                model_name='dynamic_pricing'
                            )
                            test_results['tests']['dynamic_pricing_shap'] = explanation
                            test_results['summary']['total_tests'] += 1
                            if explanation['status'] == 'success':
                                test_results['summary']['passed_tests'] += 1
                                logger.info("Dynamic Pricing SHAP explanation test passed")
                            else:
                                test_results['summary']['failed_tests'] += 1
                                logger.warning(f"Dynamic Pricing SHAP explanation test failed: {explanation.get('message', 'Unknown error')}")
                        else:
                            test_results['tests']['dynamic_pricing_shap'] = {'status': 'error', 'message': 'No sample features available'}
                            test_results['summary']['total_tests'] += 1
                            test_results['summary']['failed_tests'] += 1
                    else:
                        test_results['tests']['dynamic_pricing_shap'] = {'status': 'error', 'message': 'No sample data available'}
                        test_results['summary']['total_tests'] += 1
                        test_results['summary']['failed_tests'] += 1
                except Exception as e:
                    test_results['tests']['dynamic_pricing_shap'] = {'status': 'error', 'message': str(e)}
                    test_results['summary']['total_tests'] += 1
                    test_results['summary']['failed_tests'] += 1
                    logger.error(f"Error testing Dynamic Pricing explainer: {e}")
            
            # Test Churn Prediction explainer
            if (self.churn_model is not None and 
                hasattr(self.churn_model, 'model') and 
                self.churn_model.model is not None and
                'churn_prediction' in self.explainable_ai.shap_explainers):
                
                try:
                    logger.info("Testing Churn Prediction explainer...")
                    transactions_df = await data_processor.get_transactions_data()
                    if not transactions_df.empty:
                        # Get a single sample for explanation
                        sample_features = self.churn_model.prepare_features(transactions_df.head(100))  # Need more data for churn features
                        if sample_features is not None and not sample_features.empty:
                            explanation = self.explainable_ai.explain_prediction_shap(
                                model=self.churn_model.model,
                                X_instance=sample_features.head(1),
                                model_name='churn_prediction'
                            )
                            test_results['tests']['churn_prediction_shap'] = explanation
                            test_results['summary']['total_tests'] += 1
                            if explanation['status'] == 'success':
                                test_results['summary']['passed_tests'] += 1
                                logger.info("Churn Prediction SHAP explanation test passed")
                            else:
                                test_results['summary']['failed_tests'] += 1
                                logger.warning(f"Churn Prediction SHAP explanation test failed: {explanation.get('message', 'Unknown error')}")
                        else:
                            test_results['tests']['churn_prediction_shap'] = {'status': 'error', 'message': 'No sample features available'}
                            test_results['summary']['total_tests'] += 1
                            test_results['summary']['failed_tests'] += 1
                    else:
                        test_results['tests']['churn_prediction_shap'] = {'status': 'error', 'message': 'No sample data available'}
                        test_results['summary']['total_tests'] += 1
                        test_results['summary']['failed_tests'] += 1
                except Exception as e:
                    test_results['tests']['churn_prediction_shap'] = {'status': 'error', 'message': str(e)}
                    test_results['summary']['total_tests'] += 1
                    test_results['summary']['failed_tests'] += 1
                    logger.error(f"Error testing Churn Prediction explainer: {e}")
            
            logger.info(f"ExplainableAI testing completed: {test_results['summary']['passed_tests']}/{test_results['summary']['total_tests']} tests passed")
            return test_results
            
        except Exception as e:
            logger.error(f"Error testing explainers: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    async def schedule_retraining(self):
        """
        Schedules periodic retraining of all models.
        """
        while True:
            await asyncio.sleep(settings.MODEL_RETRAIN_INTERVAL_MINUTES * 60)
            logger.info(f"Initiating scheduled retraining (every {settings.MODEL_RETRAIN_INTERVAL_MINUTES} minutes)...")
            await self.train_all_models()
            if self.models_loaded:
                logger.info("Scheduled retraining completed successfully.")
            else:
                logger.error("Scheduled retraining encountered issues.")

model_manager = ModelManager()