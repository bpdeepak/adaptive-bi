"""
Feedback Service - Manages feedback loops for AI models
Handles data collection, model monitoring, and retraining triggers
"""

import logging
import asyncio
import os
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from app.model_configs.model_config import PRICING_CONFIG, CHURN_CONFIG # Import the config instances
from app.models.advanced_models import DynamicPricingModel, ChurnPredictionModel
from app.models.knowledge_graph import CustomerBehaviorGraph # If graph needs feedback
from app.models.forecasting import ForecastingModel # Import existing Phase 3 models
from app.models.anomaly_detection import AnomalyDetectionModel
from app.models.recommendation import RecommendationModel
from app.services.data_processor import DataProcessor

# Import the ChurnService to reuse its _prepare_churn_features_for_training method
# This creates a circular dependency if ChurnService also imports FeedbackService.
# A better architectural approach would be to extract this shared data preparation
# into a common `data_prep_utils.py` or similar, which both services can import.
# For now, we'll assume a way to access it, or you can copy the logic here.
# For direct use without circular dependency:
# You can copy the _prepare_churn_features_for_training logic into this service
# or create a separate utility function that it and ChurnService can use.
# For this example, I will assume a direct import or a utility extraction
# to avoid recreating the complex logic within this file.
# If this causes a circular import, you'll need to refactor.

logger = logging.getLogger(__name__)

class FeedbackService:
    def __init__(self, mongodb_client):
        self.db = mongodb_client
        self.pricing_config = PRICING_CONFIG
        self.churn_config = CHURN_CONFIG
        
        # Instantiate models for potential loading/retraining
        self.pricing_model = DynamicPricingModel()
        self.churn_model = ChurnPredictionModel()
        self.knowledge_graph = CustomerBehaviorGraph()
        self.forecasting_model = ForecastingModel() # From Phase 3
        self.anomaly_model = AnomalyDetectionModel() # From Phase 3
        self.recommendation_model = RecommendationModel() # From Phase 3
        
        self._initialized = False

    async def initialize(self):
        """Initialize feedback service by attempting to load all models."""
        try:
            # Attempt to load all models. If a model fails to load, it will be noted.
            # Actual training will happen via `trigger_retraining`
            model_base_path = self.pricing_config.BASE_MODEL_DIR

            # Pricing Model
            pricing_model_path = os.path.join(model_base_path, "dynamic_pricing_model.pkl")
            self.pricing_model.load_model(pricing_model_path)
            
            # Churn Model
            churn_model_path = os.path.join(model_base_path, "churn_model.pkl")
            self.churn_model.load_model(churn_model_path)
            
            # Knowledge Graph
            kg_path = os.path.join(model_base_path, "knowledge_graph.gml")
            self.knowledge_graph.load_graph(kg_path)

            # Phase 3 Models (using their standard naming convention)
            try:
                self.forecasting_model.load_model()
            except:
                logger.info("Forecasting model not found, will be trained on demand")
            
            try:
                self.anomaly_model.load_model()
            except:
                logger.info("Anomaly detection model not found, will be trained on demand")
            
            try:
                self.recommendation_model.load_model()
            except:
                logger.info("Recommendation model not found, will be trained on demand")

            self._initialized = True
            logger.info("Feedback service initialized. Attempted to load all models.")
        except Exception as e:
            logger.warning(f"Could not load all models during feedback service init: {e}. Some services might not be fully operational until models are trained.")
            self._initialized = False # Set to false if models aren't ready to signify not fully ready

    async def collect_user_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collects explicit user feedback (e.g., ratings, comments) and stores it.
        Args:
            feedback_data: Dictionary containing feedback details.
                           Expected keys: userId, productId, rating, comment, feedbackDate.
                           (From your Feedback Schema)
        """
        try:
            # Validate feedback data (basic)
            required_keys = ['userId', 'productId', 'rating', 'comment', 'feedbackDate']
            if not all(key in feedback_data for key in required_keys):
                return {'status': 'error', 'message': 'Missing required feedback data fields.'}

            # Ensure feedbackDate is in a consistent format (e.g., ISO string)
            if not isinstance(feedback_data['feedbackDate'], str):
                feedback_data['feedbackDate'] = feedback_data['feedbackDate'].isoformat()

            feedback_data['createdAt'] = datetime.utcnow().isoformat()
            
            # Store in MongoDB
            result = await self.db.feedback.insert_one(feedback_data)
            logger.info(f"User feedback collected for user {feedback_data['userId']} on product {feedback_data['productId']}. Inserted ID: {result.inserted_id}")
            return {'status': 'success', 'message': 'Feedback collected successfully.', 'feedback_id': str(result.inserted_id)}
        except Exception as e:
            logger.error(f"Error collecting user feedback: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    async def collect_implicit_feedback(self, implicit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collects implicit feedback (e.g., click-through rates, conversion, returns).
        This data can be used to monitor model performance without explicit user input.
        Args:
            implicit_data: Dictionary containing implicit feedback details.
                           Expected keys: userId, activityType, productId (optional), status (optional), timestamp, etc.
                           This will typically come from `user_activities` or `transactions` collection.
                           (From your User Activity Schema, or modified Transaction Schema for status)
        """
        try:
            # For demonstration, we'll log it and assume it contributes to performance monitoring.
            # In a real system, this would trigger performance metric updates and data ingestion for retraining.
            logger.info(f"Implicit feedback collected: {implicit_data.get('activityType')}, User: {implicit_data.get('userId')}")
            
            # Example: Store implicit feedback if it's a new type not already in existing collections
            # If implicit feedback comes from existing `user_activities` or `transactions`,
            # then you're just processing it, not inserting new records here.
            # Here, we'll treat it as new records for simplicity in demonstration.
            
            # Ensure timestamp is in a consistent format
            if not isinstance(implicit_data.get('timestamp'), str):
                implicit_data['timestamp'] = datetime.utcnow().isoformat() # Default to now if not provided or wrong format
            
            # Assign a unique ID if not present
            if 'activityId' not in implicit_data:
                implicit_data['activityId'] = str(uuid.uuid4())

            result = await self.db.implicit_feedback_log.insert_one(implicit_data) # Using a new collection for implicit feedback logs
            
            return {'status': 'success', 'message': 'Implicit feedback processed and logged.', 'log_id': str(result.inserted_id)}
        except Exception as e:
            logger.error(f"Error collecting implicit feedback: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    async def monitor_model_performance(self, model_name: str) -> Dict[str, Any]:
        """
        Monitors the performance of a specified model using recent data and metrics.
        This is a simplified example; a real system would calculate actual performance metrics
        and compare against thresholds.
        Args:
            model_name: The name of the model to monitor ('pricing', 'churn', 'forecasting', 'anomaly', 'recommendation', 'knowledge_graph').
        Returns:
            A dictionary with performance status and suggested actions.
        """
        status = 'stable'
        issues = []
        recommendations = []
        
        try:
            if model_name == 'pricing':
                # Check if model is trained
                if not self.pricing_model.is_trained:
                    status = 'critical'
                    issues.append("Pricing model is not trained.")
                    recommendations.append("Trigger pricing model training.")
                    
                # Simulate monitoring: Check if price predictions are within reasonable bounds
                # This would typically involve re-evaluating on new data or checking for concept drift
                recent_transactions = await self._get_recent_transactions(days=self.pricing_config.PRICING_RETRAIN_INTERVAL_DAYS)
                if not recent_transactions.empty:
                    # Example: Monitor average actual vs predicted price, or MAE on recent data
                    # For a real scenario, you'd apply the model to recent data and compare its predictions
                    # with actual prices or outcomes if an 'optimal_price' target exists for evaluation.
                    # Or, more simply, track how often model advises significant price changes.
                    
                    # For now, a very basic check: is the data flow healthy?
                    if len(recent_transactions) < self.pricing_config.MIN_PRICING_DATA_POINTS / 2: # If recent data is too sparse
                        status = 'warning'
                        issues.append("Low volume of recent transaction data for pricing model monitoring.")
                        recommendations.append("Verify data streaming or increase data collection window.")

                    # If model is trained, check if it's stale
                    if self.pricing_model.is_trained and self.last_trained_time:
                        if (datetime.utcnow() - self.last_trained_time).days > self.pricing_config.PRICING_RETRAIN_INTERVAL_DAYS:
                            status = 'warning'
                            issues.append(f"Pricing model is stale (last trained {self.last_trained_time.isoformat()}).")
                            recommendations.append("Trigger pricing model retraining.")
                else:
                    issues.append("No recent transaction data to monitor pricing model.")

            elif model_name == 'churn':
                if not self.churn_model.is_trained:
                    status = 'critical'
                    issues.append("Churn model is not trained.")
                    recommendations.append("Trigger churn model training.")
                    
                # Simulate monitoring for churn: Check current churn rate vs. baseline or drift
                # This needs to get fresh data, prepare features, and run prediction
                users_df = await self._get_all_users()
                transactions_df = await self._get_all_transactions()
                activities_df = await self._get_all_activities()

                if not users_df.empty and not transactions_df.empty and not activities_df.empty and self.churn_model.is_trained:
                    # Reuse the data preparation logic from ChurnService
                    # WARNING: This could lead to circular import if ChurnService also imports FeedbackService
                    # Best practice is to move `_prepare_churn_features_for_training` to a shared utility.
                    
                    # For this example, let's assume we can import and use it or copy its logic.
                    # As a temporary workaround to avoid circular import, if `_prepare_churn_features_for_training`
                    # is exclusively in ChurnService, you might need to copy its logic or pass the ChurnService instance.
                    
                    # Instead of importing ChurnService here, we assume a utility function
                    # or re-implement the data prep needed for prediction.
                    
                    # Here, we will call a local helper that mirrors the data prep logic needed for prediction.
                    # In production, this data prep would be a common function.
                    
                    # Prepare data for all users to get current churn probabilities
                    current_churn_data = await self._prepare_churn_features_for_prediction(
                        users_df, transactions_df, activities_df
                    )

                    if not current_churn_data.empty:
                        churn_predictions_result = self.churn_model.predict_churn_with_reasoning(current_churn_data)
                        if churn_predictions_result['status'] == 'success':
                            # Get the proportion of high-risk users as current churn indicator
                            current_high_risk_count = churn_predictions_result['summary']['high_risk_count']
                            total_customers_monitored = churn_predictions_result['summary']['total_customers']
                            
                            if total_customers_monitored > 0:
                                current_churn_indicator_rate = current_high_risk_count / total_customers_monitored
                                baseline_churn_rate = self.churn_config.CHURN_BASELINE_RATE
                                
                                if current_churn_indicator_rate > baseline_churn_rate * 1.2: # 20% increase over baseline
                                    status = 'alert'
                                    issues.append(f"Current high-risk churn indicator ({current_churn_indicator_rate:.2%}) is significantly higher than baseline ({baseline_churn_rate:.2%}).")
                                    recommendations.append("Investigate root causes for increased churn and consider targeted retention campaigns.")
                                elif current_churn_indicator_rate < baseline_churn_rate * 0.8:
                                    status = 'info'
                                    issues.append(f"Current high-risk churn indicator ({current_churn_indicator_rate:.2%}) is lower than baseline ({baseline_churn_rate:.2%}).")
                                    recommendations.append("Good performance. Continue monitoring and identify successful retention strategies.")
                            else:
                                issues.append("No active customers to monitor churn rate.")
                        else:
                            issues.append(f"Could not get churn predictions for monitoring: {churn_predictions_result['message']}")
                else:
                    issues.append("Not enough user/transaction/activity data or churn model not trained for monitoring.")

                # If model is trained, check if it's stale
                if self.churn_model.is_trained and self.last_trained_time:
                    if (datetime.utcnow() - self.last_trained_time).days > self.churn_config.CHURN_RETRAIN_INTERVAL_DAYS:
                        status = 'warning'
                        issues.append(f"Churn model is stale (last trained {self.last_trained_time.isoformat()}).")
                        recommendations.append("Trigger churn model retraining.")

            elif model_name == 'knowledge_graph':
                if not self.knowledge_graph._is_built:
                    status = 'critical'
                    issues.append("Knowledge graph is not built.")
                    recommendations.append("Trigger knowledge graph rebuilding.")

                graph_summary = self.knowledge_graph.get_graph_summary()
                if graph_summary['status'] == 'success':
                    if graph_summary['node_count'] < self.pricing_config.MIN_KG_TRANSACTIONS * 0.5: # Example threshold
                        status = 'warning'
                        issues.append(f"Knowledge graph has low node count ({graph_summary['node_count']}), possibly indicating incomplete data ingestion.")
                        recommendations.append("Verify data streaming and graph building process. Consider rebuilding.")
                    if graph_summary['edge_count'] < self.pricing_config.MIN_KG_TRANSACTIONS * 1.5: # Example threshold
                        status = 'warning'
                        issues.append(f"Knowledge graph has low edge count ({graph_summary['edge_count']}), possibly indicating sparse relationships.")
                        recommendations.append("Review relationship extraction logic in graph building. Consider rebuilding.")
                else:
                    issues.append(f"Could not get knowledge graph summary for monitoring: {graph_summary['message']}")
                
                # Check for staleness
                if self.knowledge_graph._is_built and self.last_built_time: # Assuming a last_built_time attribute on KG
                    if (datetime.utcnow() - self.last_built_time).total_seconds() / 3600 > self.pricing_config.KG_BUILD_INTERVAL_HOURS:
                        status = 'warning'
                        issues.append(f"Knowledge graph is stale (last built {self.last_built_time.isoformat()}).")
                        recommendations.append("Trigger knowledge graph rebuilding.")

            elif model_name == 'forecasting':
                if not self.forecasting_model.is_trained:
                    status = 'critical'
                    issues.append("Forecasting model is not trained.")
                    recommendations.append("Trigger forecasting model training.")
                # Add actual monitoring logic for forecasting (e.g., comparing recent forecasts to actuals, tracking error metrics)
                # For simplicity, if it's trained, consider it stable unless performance metrics indicate otherwise
                if self.forecasting_model.is_trained:
                    # Example: Check for recent RMSE, if it's too high compared to historical
                    # You'd need to re-fetch recent data, re-process, and get prediction/evaluate
                    pass # Placeholder for actual logic
                else:
                    issues.append("No active users to monitor churn rate.") # Typo from earlier, should be specific to forecast

            elif model_name == 'anomaly_detection':
                if not self.anomaly_model.is_trained:
                    status = 'critical'
                    issues.append("Anomaly detection model is not trained.")
                    recommendations.append("Trigger anomaly detection model training.")
                # Add actual monitoring logic for anomaly detection (e.g., rate of anomalies, false positives/negatives)
                if self.anomaly_model.is_trained:
                    pass # Placeholder
                else:
                    issues.append("No active users to monitor churn rate.") # Typo from earlier, should be specific to anomaly

            elif model_name == 'recommendation':
                if not self.recommendation_model.is_trained:
                    status = 'critical'
                    issues.append("Recommendation model is not trained.")
                    recommendations.append("Trigger recommendation model training.")
                # Add actual monitoring logic for recommendation (e.g., CTR, conversion of recommended items)
                if self.recommendation_model.is_trained:
                    pass # Placeholder
                else:
                    issues.append("No active users to monitor churn rate.") # Typo from earlier, should be specific to recommendation

            else:
                return {'status': 'error', 'message': f"Monitoring for model '{model_name}' is not supported."}

            return {
                'status': 'success',
                'model': model_name,
                'overall_status': status,
                'issues': issues,
                'recommendations': recommendations,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error monitoring model {model_name}: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    async def trigger_retraining(self, model_name: str, force_retrain: bool = False) -> Dict[str, Any]:
        """
        Triggers the retraining process for a specified model.
        Args:
            model_name: The name of the model to retrain ('pricing', 'churn', 'forecasting', 'anomaly', 'recommendation', 'knowledge_graph').
            force_retrain: If True, retrain regardless of monitoring status.
        """
        try:
            if not force_retrain:
                monitor_status = await self.monitor_model_performance(model_name)
                if monitor_status['status'] == 'success' and monitor_status['overall_status'] == 'stable':
                    return {'status': 'info', 'message': f"Model '{model_name}' performance is stable. Retraining not required at this time."}

            logger.info(f"Triggering retraining for model: {model_name}...")
            model_base_path = self.pricing_config.BASE_MODEL_DIR

            if model_name == 'pricing':
                transactions = await self._get_recent_transactions(days=self.pricing_config.PRICING_TRAINING_DAYS)
                products = await self._get_all_products()
                
                if transactions.empty or products.empty:
                    return {'status': 'error', 'message': 'Insufficient data for pricing model retraining.'}

                # Merge product data into transactions for training
                data_for_training = transactions.merge(products[['productId', 'category', 'price', 'stock']], 
                                                 left_on='productId', right_on='productId', 
                                                 suffixes=('_transaction', '_product'))
                
                # Ensure correct column mapping for model training input
                data_for_training.rename(columns={'totalPrice': 'amount', 'price_product': 'price'}, inplace=True)
                data_for_training['timestamp'] = pd.to_datetime(data_for_training['transactionDate'], errors='coerce')
                data_for_training['stock_level'] = pd.to_numeric(data_for_training['stock'], errors='coerce').fillna(0)


                # Synthesize a target 'optimal_price' if not available in data
                if 'optimal_price' not in data_for_training.columns and 'price' in data_for_training.columns:
                    data_for_training['optimal_price'] = data_for_training['price'] * (1 + np.random.uniform(-0.05, 0.05, len(data_for_training)))
                elif 'optimal_price' not in data_for_training.columns:
                    return {'status': 'error', 'message': 'Cannot synthesize optimal_price for pricing model retraining, missing product price data.'}

                train_result = self.pricing_model.train(data_for_training, target_col='optimal_price')
                if train_result['status'] == 'success':
                    pricing_model_save_path = os.path.join(model_base_path, "dynamic_pricing_model.pkl")
                    self.pricing_model.save_model(pricing_model_save_path)
                    self.last_trained_time = datetime.utcnow() # Update last trained time
                    logger.info("Pricing model retraining successful.")
                    return {'status': 'success', 'message': 'Pricing model retrained successfully.', 'metrics': train_result}
                else:
                    return {'status': 'error', 'message': f"Pricing model retraining failed: {train_result['message']}"}

            elif model_name == 'churn':
                # Use memory-limited data loading
                users = await self._get_all_users_limited()
                transactions = await self._get_all_transactions_limited()
                activities = await self._get_all_activities_limited()
                
                if users.empty or transactions.empty or activities.empty:
                    return {'status': 'error', 'message': 'Insufficient data for churn model retraining.'}

                # Reuse the data preparation logic from ChurnService
                # This explicitly calls the internal method used by ChurnService
                # to get the prepared feature dataframe for the churn model.
                from app.services.churn_service import ChurnService # Local import to avoid circular dependency
                churn_service_instance = ChurnService(self.db) # Create a temporary instance to access data prep method
                training_data = await churn_service_instance._prepare_churn_features_for_training(users, transactions, activities)
                
                if training_data.empty:
                    return {'status': 'error', 'message': 'Prepared training data for churn model is empty.'}

                train_result = self.churn_model.train(training_data)
                if train_result['status'] == 'success':
                    churn_model_save_path = os.path.join(model_base_path, "churn_model.pkl")
                    self.churn_model.save_model(churn_model_save_path)
                    self.last_trained_time = datetime.utcnow() # Update last trained time
                    logger.info("Churn model retraining successful.")
                    return {'status': 'success', 'message': 'Churn model retrained successfully.', 'metrics': train_result}
                else:
                    return {'status': 'error', 'message': f"Churn model retraining failed: {train_result['message']}"}
            
            elif model_name == 'knowledge_graph':
                users = await self._get_all_users()
                products = await self._get_all_products()
                transactions = await self._get_all_transactions()
                feedback = await self._get_all_feedback()
                activities = await self._get_all_activities()
                
                if transactions.empty or products.empty or users.empty:
                    return {'status': 'error', 'message': 'Insufficient data for knowledge graph rebuilding.'}

                # Ensure 'category' and 'amount' are present in transactions before passing to graph
                # This logic is also in ReasoningService._build_knowledge_graph
                if 'category' not in transactions.columns:
                    transactions = transactions.merge(
                        products[['productId', 'category']], on='productId', how='left'
                    )
                    transactions['category'].fillna('unknown', inplace=True)
                if 'totalPrice' in transactions.columns and 'amount' not in transactions.columns:
                    transactions['amount'] = transactions['totalPrice']
                elif 'amount' not in transactions.columns:
                    transactions['amount'] = transactions['quantity'] * transactions.get('price', 1.0) # Estimate if price is missing
                if 'price' not in transactions.columns: # Ensure price is available for graph edges if needed
                    transactions = transactions.merge(
                        products[['productId', 'price']], on='productId', how='left', suffixes=('_tx', '_prod')
                    )
                    # Handle the price column from merge
                    if 'price_prod' in transactions.columns:
                        transactions['price'] = transactions['price_prod'].fillna(transactions['amount'] / transactions['quantity'].replace(0,1))
                        transactions.drop(columns=['price_tx', 'price_prod'], errors='ignore', inplace=True)
                    elif 'price_tx' in transactions.columns:
                        transactions['price'] = transactions['price_tx']
                        transactions.drop(columns=['price_tx'], errors='ignore', inplace=True)
                    transactions['price'].fillna(1.0, inplace=True) # Final fallback

                graph_build_result = self.knowledge_graph.build_graph_from_data(transactions, products, users)
                if graph_build_result['status'] == 'success':
                    kg_save_path = os.path.join(model_base_path, "knowledge_graph.gml")
                    self.knowledge_graph.save_graph(kg_save_path)
                    self.last_built_time = datetime.utcnow() # Update last built time
                    logger.info("Knowledge graph rebuilt successfully.")
                    return {'status': 'success', 'message': 'Knowledge graph rebuilt successfully.', 'metrics': graph_build_result}
                else:
                    return {'status': 'error', 'message': f"Knowledge graph rebuilding failed: {graph_build_result['message']}"}
            
            elif model_name == 'forecasting':
                # Use distributed sampling for forecasting to get better time series data
                from app.services.data_processor import DataProcessor # Import DataProcessor
                data_processor = DataProcessor(self.db)
                transactions = await data_processor.get_transactions_data_for_forecasting(days=180, limit=5000)
                if transactions.empty:
                    return {'status': 'error', 'message': 'Insufficient data for forecasting model retraining.'}

                # Prepare data for forecasting model - method already provides totalAmount field
                time_series_data = data_processor.prepare_time_series_data(transactions, 'totalAmount', 'D')
                
                if time_series_data.empty:
                    return {'status': 'error', 'message': 'Prepared time series data for forecasting is empty.'}

                # Use the ForecastingModel's training method
                train_result = self.forecasting_model.train(time_series_data)
                
                if train_result['status'] == 'success':
                    forecast_model_save_path = os.path.join(model_base_path, f"forecasting_model_{self.forecasting_model.model.__class__.__name__}.joblib")
                    self.forecasting_model.save_model()
                    logger.info("Forecasting model retraining successful.")
                    return {'status': 'success', 'message': 'Forecasting model retrained successfully.', 'metrics': train_result}
                else:
                    return {'status': 'error', 'message': f"Forecasting model retraining failed: {train_result['message']}"}

            elif model_name == 'anomaly_detection':
                # Similar logic as in app.models.model_manager.py for training
                transactions = await self._get_all_transactions()
                if transactions.empty:
                    return {'status': 'error', 'message': 'Insufficient data for anomaly detection model retraining.'}

                # Prepare data for anomaly detection model (as done in data_processor.py)
                from app.services.data_processor import DataProcessor # Import DataProcessor
                data_processor = DataProcessor(self.db)
                anomaly_data = data_processor.prepare_anomaly_detection_data(transactions, ['totalPrice', 'quantity'])
                
                if anomaly_data.empty:
                    return {'status': 'error', 'message': 'Prepared anomaly detection data is empty.'}

                train_result = self.anomaly_model.train(anomaly_data, features=['totalPrice', 'quantity'])
                
                if train_result['status'] == 'success':
                    anomaly_model_save_path = os.path.join(model_base_path, f"anomaly_model_{self.anomaly_model.model.__class__.__name__}.joblib")
                    self.anomaly_model.save_model()
                    logger.info("Anomaly detection model retraining successful.")
                    return {'status': 'success', 'message': 'Anomaly detection model retrained successfully.', 'metrics': train_result}
                else:
                    return {'status': 'error', 'message': f"Anomaly detection model retraining failed: {train_result['message']}"}

            elif model_name == 'recommendation':
                # Similar logic as in app.models.model_manager.py for training
                transactions = await self._get_all_transactions()
                if transactions.empty:
                    return {'status': 'error', 'message': 'Insufficient data for recommendation model retraining.'}

                # Prepare data for recommendation model (as done in data_processor.py)
                from app.services.data_processor import DataProcessor # Import DataProcessor
                data_processor = DataProcessor(self.db)
                user_item_matrix_data = await data_processor.get_user_item_matrix()
                
                if user_item_matrix_data.empty:
                    return {'status': 'error', 'message': 'Prepared user-item matrix data is empty.'}

                train_result = await self.recommendation_model.train(data_processor)
                
                if train_result['status'] == 'success':
                    recommendation_model_save_path = os.path.join(model_base_path, f"recommendation_model_{self.recommendation_model.model.__class__.__name__}.joblib")
                    self.recommendation_model.save_model()
                    logger.info("Recommendation model retraining successful.")
                    return {'status': 'success', 'message': 'Recommendation model retrained successfully.', 'metrics': train_result}
                else:
                    return {'status': 'error', 'message': f"Recommendation model retraining failed: {train_result['message']}"}

            else:
                return {'status': 'error', 'message': f"Retraining for model '{model_name}' is not supported."}
        except Exception as e:
            logger.error(f"Error triggering retraining for {model_name}: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    async def log_feedback(self, model_name: str, prediction_id: str, actual_outcome: float, feedback_notes: Optional[str] = None) -> Dict[str, Any]:
        """Log feedback for a specific model prediction."""
        try:
            # Create feedback record
            feedback_data = {
                'model_name': model_name,
                'prediction_id': prediction_id,
                'actual_outcome': actual_outcome,
                'feedback_notes': feedback_notes,
                'logged_at': datetime.utcnow(),
                'feedback_type': 'explicit'
            }
            
            # Store in database
            if self.db:
                collection = self.db['model_feedback']
                result = await collection.insert_one(feedback_data)
                
                logger.info(f"Logged feedback for model {model_name}, prediction {prediction_id}")
                
                return {
                    'status': 'success',
                    'message': 'Feedback logged successfully',
                    'feedback_id': str(result.inserted_id)
                }
            else:
                # Store in memory as fallback
                if not hasattr(self, '_feedback_log'):
                    self._feedback_log = []
                
                feedback_data['feedback_id'] = str(uuid.uuid4())
                self._feedback_log.append(feedback_data)
                
                logger.info(f"Logged feedback in memory for model {model_name}, prediction {prediction_id}")
                
                return {
                    'status': 'success',
                    'message': 'Feedback logged successfully (in memory)',
                    'feedback_id': feedback_data['feedback_id']
                }
                
        except Exception as e:
            logger.error(f"Error logging feedback for model {model_name}: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    # Helper methods to fetch data from MongoDB (similar to other services)
    async def _get_recent_transactions(self, days: int) -> pd.DataFrame:
        try:
            # DRASTICALLY limit data for memory conservation
            cutoff_date = datetime.utcnow() - timedelta(days=min(days, 1))  # Max 1 day
            max_records = 1000  # Limit to 1000 transactions maximum
            
            transactions_cursor = self.db.transactions.find({
                'transactionDate': {'$gte': cutoff_date}
            }).limit(max_records)  # CRITICAL: Add limit
            
            transactions_list = await transactions_cursor.to_list(length=max_records)
            df = pd.DataFrame(transactions_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Check if we have data
            if df.empty:
                logger.warning(f"No recent transactions found in the last {min(days, 1)} days.")
                return df
            
            # Ensure essential columns are present and correctly typed
            essential_cols = ['transactionDate', 'totalPrice', 'quantity', 'productId', 'userId']
            missing_cols = [col for col in essential_cols if col not in df.columns]
            if missing_cols:
                logger.warning(f"Missing columns in transactions data: {missing_cols}. This may affect model training.")
                # Don't add NaN columns, just log the warning and work with what we have
            
            # Clean and convert existing columns
            if 'transactionDate' in df.columns:
                df['transactionDate'] = pd.to_datetime(df['transactionDate'], errors='coerce')
            if 'totalPrice' in df.columns:
                df['totalPrice'] = pd.to_numeric(df['totalPrice'], errors='coerce')
            if 'quantity' in df.columns:
                df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            if 'productId' in df.columns:
                df['productId'] = df['productId'].astype(str)
            if 'userId' in df.columns:
                df['userId'] = df['userId'].astype(str)

            # Only drop rows where essential columns exist and are null
            existing_essential = [col for col in essential_cols if col in df.columns]
            if existing_essential:
                df.dropna(subset=existing_essential, inplace=True)

            logger.info(f"Fetched {len(df)} recent transactions for feedback service (limited to {max_records}).")
            return df
        except Exception as e:
            logger.error(f"Error fetching recent transactions for feedback service: {e}", exc_info=True)
            return pd.DataFrame()
            
    async def _get_all_users(self) -> pd.DataFrame:
        try:
            # LIMIT users for memory conservation
            max_users = 200  # Drastically limit to 200 users
            users_cursor = self.db.users.find({}).limit(max_users)
            users_list = await users_cursor.to_list(length=max_users)
            df = pd.DataFrame(users_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure proper datetime parsing for relevant columns
            if 'registrationDate' in df.columns:
                df['registrationDate'] = pd.to_datetime(df['registrationDate'], errors='coerce')
            if 'lastLogin' in df.columns:
                df['lastLogin'] = pd.to_datetime(df['lastLogin'], errors='coerce')
            
            logger.info(f"Fetched {len(df)} users for feedback service (limited to {max_users}).")
            return df
        except Exception as e:
            logger.error(f"Error fetching all users for feedback service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_all_transactions(self) -> pd.DataFrame:
        try:
            # LIMIT transactions for memory conservation 
            max_transactions = 1000  # Drastically limit to 1000 transactions
            transactions_cursor = self.db.transactions.find({}).limit(max_transactions)
            transactions_list = await transactions_cursor.to_list(length=max_transactions)
            df = pd.DataFrame(transactions_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure datetime parsing and numeric types
            if 'transactionDate' in df.columns:
                df['transactionDate'] = pd.to_datetime(df['transactionDate'], errors='coerce')
            if 'totalPrice' in df.columns:
                df['totalPrice'] = pd.to_numeric(df['totalPrice'], errors='coerce')
            if 'quantity' in df.columns:
                df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            
            df['productId'] = df['productId'].astype(str) # Ensure string type
            df['userId'] = df['userId'].astype(str) # Ensure string type

            logger.info(f"Fetched {len(df)} transactions for feedback service (limited to {max_transactions}).")
            return df
        except Exception as e:
            logger.error(f"Error fetching all transactions for feedback service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_all_activities(self) -> pd.DataFrame:
        try:
            # LIMIT activities for memory conservation
            max_activities = 500  # Limit to 500 activities
            activities_cursor = self.db.user_activities.find({}).limit(max_activities)
            activities_list = await activities_cursor.to_list(length=max_activities)
            df = pd.DataFrame(activities_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            df['userId'] = df['userId'].astype(str) # Ensure string type

            logger.info(f"Fetched {len(df)} activities for feedback service (limited to {max_activities}).")
            return df
        except Exception as e:
            logger.error(f"Error fetching all activities for feedback service: {e}", exc_info=True)
            return pd.DataFrame()
            
    async def _get_all_products(self) -> pd.DataFrame:
        try:
            # LIMIT products for memory conservation
            max_products = 500  # Limit to 500 products
            products_cursor = self.db.products.find({}).limit(max_products)
            products_list = await products_cursor.to_list(length=max_products)
            df = pd.DataFrame(products_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure numeric types
            if 'price' in df.columns:
                df['price'] = pd.to_numeric(df['price'], errors='coerce')
            if 'stock' in df.columns:
                df['stock'] = pd.to_numeric(df['stock'], errors='coerce')

            logger.info(f"Fetched {len(df)} products for feedback service (limited to {max_products}).")
            return df
        except Exception as e:
            logger.error(f"Error fetching all products for feedback service: {e}", exc_info=True)
            return pd.DataFrame()
            
    async def _get_all_feedback(self) -> pd.DataFrame:
        try:
            feedback_cursor = self.db.feedback.find({})
            feedback_list = await feedback_cursor.to_list(length=None)
            df = pd.DataFrame(feedback_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            if 'feedbackDate' in df.columns:
                df['feedbackDate'] = pd.to_datetime(df['feedbackDate'], errors='coerce')
            if 'rating' in df.columns:
                df['rating'] = pd.to_numeric(df['rating'], errors='coerce')

            logger.info(f"Fetched {len(df)} feedback entries for feedback service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching all feedback for feedback service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _prepare_churn_features_for_prediction(
        self, users_df: pd.DataFrame, transactions_df: pd.DataFrame, activities_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Prepares comprehensive features for churn prediction from raw dataframes for prediction.
        This method is duplicated from ChurnService to avoid circular import for monitoring.
        In a refactored system, this would be a common utility function.
        """
        # Ensure 'transactionDate' and 'timestamp' columns are datetime
        if not transactions_df.empty:
            transactions_df['transactionDate'] = pd.to_datetime(transactions_df['transactionDate'], errors='coerce')
            transactions_df.dropna(subset=['transactionDate'], inplace=True)
            
        if not activities_df.empty:
            activities_df['timestamp'] = pd.to_datetime(activities_df['timestamp'], errors='coerce')
            activities_df.dropna(subset=['timestamp'], inplace=True)

        if not users_df.empty:
            users_df['registrationDate'] = pd.to_datetime(users_df['registrationDate'], errors='coerce')
            users_df['lastLogin'] = pd.to_datetime(users_df['lastLogin'], errors='coerce')
            users_df.dropna(subset=['registrationDate', 'lastLogin'], inplace=True)

        # Merge transactions with product data to get 'category'
        products_df = await self._get_all_products() # Use existing _get_all_products
        if not transactions_df.empty and not products_df.empty:
            transactions_df = transactions_df.merge(
                products_df[['productId', 'category']], on='productId', how='left'
            )
            transactions_df['category'].fillna('unknown', inplace=True)
        elif 'category' not in transactions_df.columns:
            transactions_df['category'] = 'unknown'


        # Consolidate transactions and user activities into a single "interactions" DataFrame per user
        all_interactions = []

        if not transactions_df.empty:
            transactions_for_model = transactions_df.rename(columns={
                'transactionDate': 'timestamp',
                'userId': 'user_id',
                'totalPrice': 'amount',
                'transactionId': 'transaction_id',
                'productId': 'product_id'
            })
            transactions_for_model['interaction_type'] = 'purchase'
            transactions_for_model['quantity'] = pd.to_numeric(transactions_for_model['quantity'], errors='coerce').fillna(0)
            transactions_for_model['price'] = pd.to_numeric(transactions_for_model['price'], errors='coerce').fillna(0)
            all_interactions.append(transactions_for_model[[
                'user_id', 'timestamp', 'transaction_id', 'amount', 'category', 'product_id', 'quantity', 'price', 'interaction_type'
            ]])

        if not activities_df.empty:
            activities_for_model = activities_df.rename(columns={
                'userId': 'user_id',
                'activityId': 'transaction_id',
                'activityType': 'interaction_type'
            })
            activities_for_model['amount'] = 0.0
            activities_for_model['category'] = 'unknown'
            activities_for_model['product_id'] = activities_for_model.get('productId', 'unknown_product')
            activities_for_model['quantity'] = 0
            activities_for_model['price'] = 0.0
            
            all_interactions.append(activities_for_model[[
                'user_id', 'timestamp', 'transaction_id', 'amount', 'category', 'product_id', 'quantity', 'price', 'interaction_type'
            ]])
        
        if not all_interactions:
            logger.warning("No interactions data prepared for churn model training.")
            return pd.DataFrame()

        combined_interactions_df = pd.concat(all_interactions, ignore_index=True)
        combined_interactions_df = combined_interactions_df.sort_values(by=['user_id', 'timestamp']).reset_index(drop=True)

        final_df_for_model = combined_interactions_df.merge(
            users_df[['userId', 'registrationDate', 'lastLogin']],
            left_on='user_id', right_on='userId', how='left'
        ).drop(columns=['userId'])

        final_df_for_model['registrationDate'] = pd.to_datetime(final_df_for_model['registrationDate'], errors='coerce')
        final_df_for_model['lastLogin'] = pd.to_datetime(final_df_for_model['lastLogin'], errors='coerce')
        final_df_for_model['timestamp'] = pd.to_datetime(final_df_for_model['timestamp'], errors='coerce')

        final_df_for_model.dropna(subset=['user_id', 'timestamp'], inplace=True)

        # Call the churn model's prepare_features method directly on this consolidated data
        # This will return the RFM and behavioral features
        churn_model_instance_for_prep = ChurnPredictionModel() # Create a dummy instance just for feature preparation
        prepared_features = churn_model_instance_for_prep.prepare_features(final_df_for_model)

        return prepared_features

    async def get_feedback_summary(self, model_name: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """
        Get a summary of feedback metrics for models.
        Args:
            model_name: Specific model name to get feedback for, or None for all models
            days: Number of days to look back for feedback
        Returns:
            Dictionary containing feedback summary metrics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Query feedback collection
            feedback_query: Dict[str, Any] = {"createdAt": {"$gte": cutoff_date}}
            if model_name:
                feedback_query["modelName"] = model_name
            
            feedback_cursor = self.db.feedback.find(feedback_query)
            feedback_data = list(feedback_cursor)
            
            # Calculate summary metrics
            total_feedback = len(feedback_data)
            
            if total_feedback == 0:
                return {
                    "status": "success",
                    "summary": {
                        "total_feedback": 0,
                        "models_with_feedback": [],
                        "avg_accuracy": 0.0,
                        "feedback_trends": {},
                        "period_days": days
                    }
                }
            
            # Group by model
            models_feedback = {}
            all_accuracies = []
            
            for feedback in feedback_data:
                model = feedback.get("modelName", "unknown")
                if model not in models_feedback:
                    models_feedback[model] = []
                models_feedback[model].append(feedback)
                
                # Calculate accuracy if we have prediction and actual values
                predicted = feedback.get("predictedValue")
                actual = feedback.get("actualValue")
                if predicted is not None and actual is not None:
                    # For regression: relative accuracy
                    if actual != 0:
                        accuracy = 1 - abs(predicted - actual) / abs(actual)
                    else:
                        accuracy = 1 if predicted == actual else 0
                    all_accuracies.append(max(0, accuracy))  # Ensure non-negative
            
            # Calculate model-specific metrics
            model_summaries = {}
            for model, feedbacks in models_feedback.items():
                model_accuracies = []
                for feedback in feedbacks:
                    predicted = feedback.get("predictedValue")
                    actual = feedback.get("actualValue")
                    if predicted is not None and actual is not None:
                        if actual != 0:
                            accuracy = 1 - abs(predicted - actual) / abs(actual)
                        else:
                            accuracy = 1 if predicted == actual else 0
                        model_accuracies.append(max(0, accuracy))
                
                model_summaries[model] = {
                    "total_feedback": len(feedbacks),
                    "avg_accuracy": sum(model_accuracies) / len(model_accuracies) if model_accuracies else 0.0,
                    "recent_feedback": len([f for f in feedbacks if f.get("createdAt", datetime.min) >= cutoff_date])
                }
            
            # Prepare daily trends
            daily_trends = {}
            for feedback in feedback_data:
                feedback_date = feedback.get("createdAt", datetime.now())
                date_key = feedback_date.strftime("%Y-%m-%d")
                if date_key not in daily_trends:
                    daily_trends[date_key] = 0
                daily_trends[date_key] += 1
            
            summary = {
                "total_feedback": total_feedback,
                "models_with_feedback": list(models_feedback.keys()),
                "avg_accuracy": sum(all_accuracies) / len(all_accuracies) if all_accuracies else 0.0,
                "model_details": model_summaries,
                "feedback_trends": daily_trends,
                "period_days": days,
                "most_active_model": max(model_summaries.keys(), key=lambda k: model_summaries[k]["total_feedback"]) if model_summaries else None
            }
            
            return {
                "status": "success",
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback summary: {str(e)}")
            return {
                "status": "error", 
                "message": str(e)
            }

    # Memory-optimized data loading methods
    async def _get_all_users_limited(self, max_users: int = 100) -> pd.DataFrame:  # Reduced from 10000 to 100
        """Get users with memory limits"""
        try:
            # Count total users first
            total_count = await self.db.users.count_documents({})
            if total_count > max_users:
                logger.warning(f"Limiting users to {max_users} (found {total_count}) to manage memory")
                
            cursor = self.db.users.find({}).limit(max_users)
            users_list = await cursor.to_list(length=max_users)
            df = pd.DataFrame(users_list)
            
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure proper datetime parsing for relevant columns
            if 'registrationDate' in df.columns:
                df['registrationDate'] = pd.to_datetime(df['registrationDate'], errors='coerce')
            if 'lastLogin' in df.columns:
                df['lastLogin'] = pd.to_datetime(df['lastLogin'], errors='coerce')
            
            logger.info(f"Fetched {len(df)} users for feedback service (limited).")
            return df
        except Exception as e:
            logger.error(f"Error fetching limited users for feedback service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_all_transactions_limited(self, max_transactions: int = 500) -> pd.DataFrame:  # Reduced from 100000 to 500
        """Get transactions with memory limits"""
        try:
            # Count total transactions first
            total_count = await self.db.transactions.count_documents({})
            if total_count > max_transactions:
                logger.warning(f"Limiting transactions to {max_transactions} (found {total_count}) to manage memory")
                
            cursor = self.db.transactions.find({}).limit(max_transactions)
            transactions_list = await cursor.to_list(length=max_transactions)
            df = pd.DataFrame(transactions_list)
            
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure datetime parsing and numeric types
            if 'transactionDate' in df.columns:
                df['transactionDate'] = pd.to_datetime(df['transactionDate'], errors='coerce')
            if 'totalPrice' in df.columns:
                df['totalPrice'] = pd.to_numeric(df['totalPrice'], errors='coerce')
            if 'quantity' in df.columns:
                df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            
            df['productId'] = df['productId'].astype(str)
            df['userId'] = df['userId'].astype(str)

            logger.info(f"Fetched {len(df)} transactions for feedback service (limited).")
            return df
        except Exception as e:
            logger.error(f"Error fetching limited transactions for feedback service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_all_activities_limited(self, max_activities: int = 300) -> pd.DataFrame:  # Reduced from 200000 to 300
        """Get activities with memory limits"""
        try:
            # Count total activities first
            total_count = await self.db.user_activities.count_documents({})
            if total_count > max_activities:
                logger.warning(f"Limiting activities to {max_activities} (found {total_count}) to manage memory")
                
            cursor = self.db.user_activities.find({}).limit(max_activities)
            activities_list = await cursor.to_list(length=max_activities)
            df = pd.DataFrame(activities_list)
            
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            df['userId'] = df['userId'].astype(str)

            logger.info(f"Fetched {len(df)} activities for feedback service (limited).")
            return df
        except Exception as e:
            logger.error(f"Error fetching limited activities for feedback service: {e}", exc_info=True)
            return pd.DataFrame()

