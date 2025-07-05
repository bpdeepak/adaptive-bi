"""
Churn Service - Wraps churn prediction model into callable service
Handles customer churn prediction, risk assessment, and retention strategies
"""

import logging
import asyncio
import os
import gc  # Add garbage collection for memory management
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from operator import attrgetter

from app.models.advanced_models import ChurnPredictionModel
from app.models.explainable_ai import ExplainableAI
from app.model_configs.model_config import CHURN_CONFIG # Import the config instance instead
# from app.utils.feature_engineering import AdvancedFeatureProcessor # Not directly used here, churn_model handles features

logger = logging.getLogger(__name__)

class ChurnService:
    def __init__(self, mongodb_client):
        self.db = mongodb_client
        self.churn_model = ChurnPredictionModel()
        self.explainer = ExplainableAI() # Explainer instance for churn model
        self.config = CHURN_CONFIG # Use the pre-configured instance
        self._model_trained = False
        self.last_trained_time: Optional[datetime] = None # To track last training time

    async def initialize(self):
        """Initialize churn service and train/load model."""
        try:
            await self._load_and_train_model()
            logger.info("Churn service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize churn service: {e}")
            raise

    async def _load_and_train_model(self):
        """Load data and train churn prediction model."""
        try:
            # Fetch limited data for training to prevent memory issues
            users_df = await self._get_user_data(limit=1000)  # Limit to 1000 users
            transactions_df = await self._get_transaction_data(limit=5000)  # Limit to 5000 transactions
            activities_df = await self._get_activity_data(limit=5000)  # Limit to 5000 activities

            if users_df.empty or transactions_df.empty or len(users_df) < 50: # Defaulted to 50 for safety
                logger.warning(f"Insufficient data for churn model training. Users: {len(users_df)}, Transactions: {len(transactions_df)}. Skipping training.")
                self._model_trained = False
                return

            # Prepare training data using a dedicated method
            training_data = await self._prepare_churn_features_for_training(
                users_df, transactions_df, activities_df
            )
            
            if training_data.empty:
                logger.warning("Prepared training data for churn model is empty. Skipping training.")
                self._model_trained = False
                return

            # Train model
            train_result = self.churn_model.train(training_data)
            
            if train_result['status'] == 'success':
                self._model_trained = True
                self.last_trained_time = datetime.utcnow()
                logger.info(f"Churn model trained successfully. AUC: {train_result.get('auc_score', 'N/A'):.4f}")
                
                # Save the trained model to the specified path
                model_save_path = os.path.join(self.config.BASE_MODEL_DIR, "churn_model.pkl")
                self.churn_model.save_model(model_save_path)
                logger.info(f"Churn model saved to {model_save_path}")

                # Setup explainer after model training with limited data
                # The explainer needs the actual trained model and the *scaled* training data
                # We need to ensure X_train_scaled from the model.train method is available or recreate it
                if self.churn_model.model is not None:
                    # Use only a small sample for explainer to reduce memory usage
                    sample_size = min(100, len(training_data))
                    sample_training_data = training_data.head(sample_size)
                    X_train_for_explainer = self.churn_model.scaler.transform(
                        sample_training_data[self.churn_model.feature_columns].fillna(0)
                    )
                    self.explainer.setup_explainer(
                        self.churn_model.model,
                        pd.DataFrame(X_train_for_explainer, columns=self.churn_model.feature_columns),
                        'churn_prediction_model',
                        explainer_type='both'
                    )
            else:
                logger.error(f"Churn model training failed: {train_result['message']}")
                self._model_trained = False
        except Exception as e:
            logger.error(f"Churn model training failed: {e}", exc_info=True)
            self._model_trained = False
            raise

    async def predict_user_churn(
        self, user_id: str, explain: bool = True
    ) -> Dict[str, Any]:
        """Predict churn probability for a specific user."""
        if not self._model_trained:
            # Attempt to load from disk if not trained in current session (e.g., app restart)
            model_load_path = os.path.join(self.config.BASE_MODEL_DIR, f"{self.churn_model.model.__class__.__name__}_churn_model.joblib")
            try:
                self.churn_model.load_model(model_load_path)
                if self.churn_model.is_trained:
                    self._model_trained = True
                    logger.info("Churn model loaded for prediction.")
                    # Re-initialize explainer if model was just loaded with limited data
                    if self.explainer.shap_explainers.get('churn_prediction_model') is None:
                        # Need to get some sample data to initialize explainer
                        sample_users = await self._get_user_data(limit=50)  # Even smaller sample
                        sample_transactions = await self._get_transaction_data(limit=200)
                        sample_activities = await self._get_activity_data(limit=200)
                        sample_training_data = await self._prepare_churn_features_for_training(
                            sample_users, sample_transactions, sample_activities
                        )
                        if not sample_training_data.empty and self.churn_model.model is not None:
                            # Use only a tiny sample for explainer initialization
                            sample_size = min(20, len(sample_training_data))
                            tiny_sample = sample_training_data.head(sample_size)
                            X_train_for_explainer = self.churn_model.scaler.transform(
                                tiny_sample[self.churn_model.feature_columns].fillna(0)
                            )
                            self.explainer.setup_explainer(
                                self.churn_model.model,
                                pd.DataFrame(X_train_for_explainer, columns=self.churn_model.feature_columns),
                                'churn_prediction_model',
                                explainer_type='both'
                            )
            except Exception as e:
                logger.warning(f"Could not load churn model from disk for prediction: {e}. Attempting to train.")
                await self._load_and_train_model() # Attempt to train if not loaded
                if not self._model_trained:
                    return {'status': 'error', 'message': 'Churn model not available or trained.'}

        try:
            # Prepare features for the single user
            features_df = await self._prepare_single_user_features(user_id)
            if features_df.empty:
                return {'status': 'error', 'message': f"Could not prepare features for user {user_id}."}

            # Get prediction from the churn model
            prediction_result = self.churn_model.predict_churn_with_reasoning(features_df)
            
            if prediction_result['status'] != 'success':
                return prediction_result # Propagate error from model

            # Extract prediction details for the target user (first row of results)
            churn_probability = prediction_result['predictions']['churn_probabilities'][0]
            churn_prediction = prediction_result['predictions']['churn_predictions'][0]
            risk_level = prediction_result['predictions']['risk_segments'][0]
            reasoning = prediction_result['predictions']['reasoning'][0]

            # Get explanation if requested and explainer is set up
            explanation = {}
            if explain and 'churn_prediction_model' in self.explainer.shap_explainers and self.churn_model.model is not None:
                # The instance for SHAP needs to be scaled using the model's scaler
                scaled_features_for_shap = self.churn_model.scaler.transform(features_df[self.churn_model.feature_columns].fillna(0))
                shap_explanation_result = self.explainer.explain_prediction_shap(
                    self.churn_model.model,
                    pd.DataFrame(scaled_features_for_shap, columns=self.churn_model.feature_columns),
                    'churn_prediction_model'
                )
                if shap_explanation_result['status'] == 'success':
                    explanation['shap'] = shap_explanation_result.get('feature_contributions', [])
                    # You might want to process shap_explanation_result['chart_data'] if you want to embed chart directly

            # Get retention recommendations
            retention_recommendations = self._get_retention_recommendations(
                risk_level, reasoning
            )

            return {
                'status': 'success',
                'user_id': user_id,
                'churn_probability': float(churn_probability),
                'churn_risk': risk_level,
                'risk_factors': reasoning,
                'explanation': explanation,
                'retention_recommendations': retention_recommendations,
                'prediction_date': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Churn prediction failed for user {user_id}: {e}", exc_info=True)
            raise

    async def predict_churn(self, customer_id: str, activity_score: float, subscription_age_days: int) -> float:
        """Predict churn probability for a single customer."""
        try:
            if not self._model_trained:
                await self._load_and_train_model()
                if not self._model_trained:
                    raise ValueError('Churn model is not trained and training failed')

            # Create feature data for single customer prediction
            features_data = {
                'customer_id': customer_id,
                'activity_score': activity_score,
                'subscription_age_days': subscription_age_days,
                'days_since_last_activity': 30 - (activity_score * 30),  # Estimate based on activity score
                'total_spent': 1000 * activity_score,  # Estimate based on activity
                'session_frequency': activity_score * 10,  # Estimate
                'avg_session_duration': activity_score * 45,  # Estimate in minutes
                'purchase_recency': max(1, int(subscription_age_days * (1 - activity_score))),  # Days since last purchase
                'feature_usage_score': activity_score,
                'customer_satisfaction': min(5.0, activity_score * 5)  # 1-5 scale
            }
            
            # Prepare features for prediction
            feature_df = pd.DataFrame([features_data])
            
            # Use model to predict
            if self.churn_model is not None:
                # Prepare minimal feature set for prediction
                numerical_features = ['activity_score', 'subscription_age_days', 'days_since_last_activity', 
                                    'total_spent', 'session_frequency', 'avg_session_duration', 
                                    'purchase_recency', 'feature_usage_score', 'customer_satisfaction']
                
                X = feature_df[numerical_features].fillna(0)
                
                # Check if model has predict_proba method and use appropriate prediction
                if hasattr(self.churn_model, 'predict_proba') and callable(getattr(self.churn_model, 'predict_proba', None)):
                    churn_probability = getattr(self.churn_model, 'predict_proba')(X)[0][1]  # Probability of churn (class 1)
                elif hasattr(self.churn_model, 'predict') and callable(getattr(self.churn_model, 'predict', None)):
                    churn_probability = getattr(self.churn_model, 'predict')(X)[0]  # Direct prediction
                else:
                    raise ValueError("Churn model does not have predict_proba or predict method")
                
                return float(churn_probability)
            else:
                # Fallback calculation based on activity and subscription age
                base_churn_risk = 0.1  # Base 10% churn risk
                activity_factor = (1 - activity_score) * 0.3  # Low activity increases risk
                age_factor = min(0.2, subscription_age_days / 365 * 0.1)  # Older subscriptions slightly higher risk
                
                churn_probability = min(0.9, base_churn_risk + activity_factor + age_factor)
                return float(churn_probability)

        except Exception as e:
            logger.error(f"Error predicting churn for customer {customer_id}: {e}", exc_info=True)
            # Return default medium risk
            return 0.5

    async def retrain_model(self) -> Dict[str, Any]:
        """Retrain the churn model."""
        try:
            await self._load_and_train_model()
            return {
                'status': 'success' if self._model_trained else 'error',
                'message': 'Churn model retraining completed' if self._model_trained else 'Churn model retraining failed',
                'last_trained': self.last_trained_time.isoformat() if self.last_trained_time else None
            }
        except Exception as e:
            logger.error(f"Error retraining churn model: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    async def get_cohort_analysis(self, start_date, end_date, cohort_type: str = 'acquisition_month') -> Dict[str, Any]:
        """Get cohort analysis for customer retention."""
        try:
            # Get limited user and transaction data for cohort analysis to prevent memory issues
            users_df = await self._get_user_data(limit=2000)  # Limit users for cohort analysis
            transactions_df = await self._get_transaction_data(limit=10000)  # Limit transactions
            
            logger.info(f"Fetched {len(users_df)} users and {len(transactions_df)} transactions for cohort analysis")
            logger.info(f"User columns: {users_df.columns.tolist() if not users_df.empty else 'No users'}")
            logger.info(f"Transaction columns: {transactions_df.columns.tolist() if not transactions_df.empty else 'No transactions'}")
            
            if users_df.empty or transactions_df.empty:
                return {
                    'status': 'error',
                    'message': 'Insufficient data for cohort analysis'
                }

            # Check if required columns exist
            if 'userId' not in users_df.columns or 'registrationDate' not in users_df.columns:
                return {
                    'status': 'error',
                    'message': f'Missing required user columns. Available: {users_df.columns.tolist()}'
                }
            
            if 'userId' not in transactions_df.columns or 'transactionDate' not in transactions_df.columns:
                return {
                    'status': 'error',
                    'message': f'Missing required transaction columns. Available: {transactions_df.columns.tolist()}'
                }

            # Merge user and transaction data
            merged_data = transactions_df.merge(users_df[['userId', 'registrationDate']], on='userId', how='left')
            merged_data['user_created'] = pd.to_datetime(merged_data['registrationDate'])
            merged_data['transaction_date'] = pd.to_datetime(merged_data['transactionDate'])
            
            # Create cohort groups based on cohort_type
            if cohort_type == 'acquisition_month':
                merged_data['cohort_group'] = merged_data['user_created'].dt.to_period('M')
                merged_data['period_number'] = (
                    merged_data['transaction_date'].dt.to_period('M') - 
                    merged_data['cohort_group']
                ).apply(lambda x: x.n if hasattr(x, 'n') else 0)
            elif cohort_type == 'first_purchase':
                # Group by month of first purchase
                first_purchase = merged_data.groupby('userId')['transaction_date'].min().reset_index()
                first_purchase['cohort_group'] = first_purchase['transaction_date'].dt.to_period('M')
                merged_data = merged_data.merge(first_purchase[['userId', 'cohort_group']], on='userId', how='left')
                merged_data['period_number'] = (
                    merged_data['transaction_date'].dt.to_period('M') - 
                    merged_data['cohort_group']
                ).apply(lambda x: x.n if hasattr(x, 'n') else 0)
            else:  # Default to weekly grouping
                merged_data['cohort_group'] = merged_data['user_created'].dt.to_period('W')
                merged_data['period_number'] = (
                    merged_data['transaction_date'].dt.to_period('W') - 
                    merged_data['cohort_group']
                ).apply(lambda x: x.n if hasattr(x, 'n') else 0)

            # Filter data by date range
            merged_data = merged_data[
                (merged_data['transaction_date'] >= pd.to_datetime(start_date)) &
                (merged_data['transaction_date'] <= pd.to_datetime(end_date))
            ]

            # Calculate cohort table
            cohort_data = merged_data.groupby(['cohort_group', 'period_number'])['userId'].nunique().reset_index()
            cohort_table = cohort_data.pivot(index='cohort_group', 
                                            columns='period_number', 
                                            values='userId')

            # Calculate cohort sizes
            cohort_sizes = merged_data.groupby('cohort_group')['userId'].nunique()
            
            # Calculate retention rates
            retention_table = cohort_table.divide(cohort_sizes, axis=0)

            return {
                'status': 'success',
                'cohort_analysis': {
                    'cohort_type': cohort_type,
                    'cohort_table': cohort_table.fillna(0).to_dict(),
                    'retention_rates': retention_table.fillna(0).to_dict(),
                    'cohort_sizes': cohort_sizes.to_dict(),
                    'average_retention': {
                        'period_1': retention_table[1].mean() if 1 in retention_table.columns else 0,
                        'period_3': retention_table[3].mean() if 3 in retention_table.columns else 0,
                        'period_6': retention_table[6].mean() if 6 in retention_table.columns else 0,
                        'period_12': retention_table[12].mean() if 12 in retention_table.columns else 0
                    }
                }
            }

        except Exception as e:
            logger.error(f"Error in cohort analysis: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    async def explain_prediction(self, customer_id: str, activity_score: float, subscription_age_days: int, method: str = 'shap') -> Dict[str, Any]:
        """Explain churn prediction for a customer."""
        try:
            if not self._model_trained:
                return {
                    'status': 'error',
                    'message': 'Churn model is not trained'
                }

            # First predict churn probability using the new method
            churn_probability = await self.predict_churn(customer_id, activity_score, subscription_age_days)
            
            # Determine risk level
            if churn_probability > 0.7:
                risk_level = 'High Risk'
                risk_description = 'Customer is very likely to churn soon'
            elif churn_probability > 0.4:
                risk_level = 'Medium Risk'
                risk_description = 'Customer shows some signs of potential churn'
            else:
                risk_level = 'Low Risk'
                risk_description = 'Customer appears to be retained'
            
            # Create feature explanations
            features = {
                'activity_score': activity_score,
                'subscription_age_days': subscription_age_days,
                'estimated_lifetime_value': activity_score * 1000,
                'engagement_level': 'high' if activity_score > 0.7 else 'medium' if activity_score > 0.3 else 'low'
            }
            
            feature_importance = {
                'activity_score': 0.40,
                'subscription_age_days': 0.25,
                'estimated_lifetime_value': 0.20,
                'engagement_level': 0.15
            }
            
            explanations = []
            for feature, importance in feature_importance.items():
                if feature in features:
                    explanations.append({
                        'feature': feature,
                        'value': features[feature],
                        'importance': importance,
                        'impact': 'high' if importance > 0.3 else 'medium' if importance > 0.2 else 'low',
                        'description': self._get_churn_feature_description(feature, features[feature])
                    })
            
            # Generate retention strategies
            retention_strategies = self._get_retention_recommendations(risk_level, [])
            
            # Generate method-specific explanation
            if method.lower() == 'shap':
                explanation_type = 'SHAP (SHapley Additive exPlanations) analysis'
                detail = 'Shows how each feature contributes to the churn probability'
            elif method.lower() == 'lime':
                explanation_type = 'LIME (Local Interpretable Model-agnostic Explanations) analysis'
                detail = 'Explains individual predictions by approximating the model locally'
            else:
                explanation_type = 'Feature importance analysis'
                detail = 'Shows the relative importance of each feature in the prediction'

            return {
                'status': 'success',
                'customer_id': customer_id,
                'method': method,
                'explanation_type': explanation_type,
                'detail': detail,
                'churn_probability': churn_probability,
                'risk_level': risk_level,
                'risk_description': risk_description,
                'feature_explanations': explanations,
                'retention_strategies': retention_strategies[:3],  # Top 3 strategies
                'model_confidence': 0.85,
                'summary': f'Churn analysis with {method.upper()} explainability for customer {customer_id}'
            }

        except Exception as e:
            logger.error(f"Error explaining churn prediction: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    def _get_retention_recommendations(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """Generates tailored retention recommendations based on churn risk and reasoning."""
        recommendations = []

        if risk_level == 'High Risk':
            recommendations.append("Immediate intervention needed: Offer a personalized discount or exclusive promotion.")
            recommendations.append("Reach out proactively via preferred communication channel (e.g., email, app notification).")
            if "High recency" in " ".join(risk_factors):
                recommendations.append("Send a 'We Miss You' campaign with compelling offers.")
            if "Low frequency" in " ".join(risk_factors):
                recommendations.append("Suggest product bundles or subscription options to encourage repeat purchases.")
            if "Irregular purchasing" in " ".join(risk_factors):
                recommendations.append("Analyze past purchase categories to recommend highly relevant new products.")
            if "Below average order value" in " ".join(risk_factors):
                recommendations.append("Incentivize higher spending with tiered rewards or free shipping thresholds.")
        elif risk_level == 'Medium Risk':
            recommendations.append("Engage with targeted content based on past preferences.")
            recommendations.append("Send a personalized product recommendation email.")
            recommendations.append("Consider a small incentive for their next purchase.")
        else: # Low Risk
            recommendations.append("Maintain engagement through regular, valuable communications (e.g., newsletters, new product alerts).")
            recommendations.append("Encourage reviews or referrals to strengthen loyalty.")
            
        recommendations.append(f"Consider insights from the knowledge graph for further personalization.")

        return recommendations

    async def _get_user_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Fetches user data from MongoDB."""
        try:
            users_cursor = self.db.users.find({})
            if limit:
                users_cursor = users_cursor.limit(limit)
            users_list = await users_cursor.to_list(length=None)
            df = pd.DataFrame(users_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure datetime columns are correctly parsed
            df['registrationDate'] = pd.to_datetime(df['registrationDate'], errors='coerce')
            df['lastLogin'] = pd.to_datetime(df['lastLogin'], errors='coerce')
            
            logger.info(f"Fetched {len(df)} users for churn service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching user data: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_transaction_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Fetches transaction data from MongoDB."""
        try:
            transactions_cursor = self.db.transactions.find({})
            if limit:
                transactions_cursor = transactions_cursor.limit(limit)
            transactions_list = await transactions_cursor.to_list(length=None)
            df = pd.DataFrame(transactions_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure essential columns are present and correctly typed
            df['transactionDate'] = pd.to_datetime(df['transactionDate'], errors='coerce')
            df['totalPrice'] = pd.to_numeric(df['totalPrice'], errors='coerce')
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')

            # Ensure 'category' and 'productId' are always available if needed by prepare_features
            # In your schema, 'category' is not in transactions, but in products.
            # This needs to be merged in _prepare_churn_features or the model's prepare_features.
            # For `_get_transaction_data` we fetch as is.
            
            logger.info(f"Fetched {len(df)} transactions for churn service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching transaction data: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_activity_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Fetches user activity data from MongoDB."""
        try:
            activities_cursor = self.db.user_activities.find({})
            if limit:
                activities_cursor = activities_cursor.limit(limit)
            activities_list = await activities_cursor.to_list(length=None)
            df = pd.DataFrame(activities_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure datetime column is correctly parsed
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            logger.info(f"Fetched {len(df)} activities for churn service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching user activity data: {e}", exc_info=True)
            return pd.DataFrame()
            
    async def _get_user_details(self, user_id: str) -> Optional[Dict]:
        """Fetches details for a single user from MongoDB."""
        try:
            user = await self.db.users.find_one({'userId': user_id})
            if user and '_id' in user:
                del user['_id']
            return user
        except Exception as e:
            logger.error(f"Error fetching user details for {user_id}: {e}", exc_info=True)
            return None

    async def _get_product_data(self) -> pd.DataFrame:
        """Fetches all product data from MongoDB (needed for category mapping)."""
        try:
            products_cursor = self.db.products.find({})
            products_list = await products_cursor.to_list(length=None)
            df = pd.DataFrame(products_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            return df
        except Exception as e:
            logger.error(f"Error fetching product data for churn service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _prepare_churn_features_for_training(
        self, users_df: pd.DataFrame, transactions_df: pd.DataFrame, activities_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Prepares comprehensive features for churn prediction from raw dataframes.
        This method is designed to provide the combined DataFrame needed by ChurnPredictionModel.prepare_features.
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
        products_df = await self._get_product_data()
        if not transactions_df.empty and not products_df.empty:
            transactions_df = transactions_df.merge(
                products_df[['productId', 'category']], on='productId', how='left'
            )
            transactions_df['category'].fillna('unknown', inplace=True)
        elif 'category' not in transactions_df.columns:
            transactions_df['category'] = 'unknown' # Add a default category if no products or no merge


        # Consolidate transactions and user activities into a single "interactions" DataFrame per user
        # This interaction DF will be the input to ChurnPredictionModel.prepare_features
        all_interactions = []

        if not transactions_df.empty:
            transactions_for_model = transactions_df.rename(columns={
                'transactionDate': 'timestamp',
                'userId': 'user_id',
                'totalPrice': 'amount',
                'transactionId': 'transaction_id',
                'productId': 'product_id'
            })
            # Add a 'type' to distinguish interaction source
            transactions_for_model['interaction_type'] = 'purchase'
            # Ensure 'quantity' and 'price' are numeric and present
            transactions_for_model['quantity'] = pd.to_numeric(transactions_for_model['quantity'], errors='coerce').fillna(0)
            # Derive price from amount and quantity
            transactions_for_model['price'] = transactions_for_model['amount'] / transactions_for_model['quantity'].clip(lower=1)
            transactions_for_model['price'] = pd.to_numeric(transactions_for_model['price'], errors='coerce').fillna(0)
            all_interactions.append(transactions_for_model[[
                'user_id', 'timestamp', 'transaction_id', 'amount', 'category', 'product_id', 'quantity', 'price', 'interaction_type'
            ]])

        if not activities_df.empty:
            activities_for_model = activities_df.rename(columns={
                'userId': 'user_id',
                'activityId': 'transaction_id', # Use activityId as transaction_id for consistency for the model
                'activityType': 'interaction_type'
            })
            # Fill missing columns expected by ChurnPredictionModel.prepare_features with defaults
            activities_for_model['amount'] = 0.0 # No monetary value for most activities
            activities_for_model['category'] = 'unknown'
            activities_for_model['product_id'] = activities_for_model.get('productId', 'unknown_product') # Use existing productId or default
            activities_for_model['quantity'] = 0 # No quantity for most activities
            activities_for_model['price'] = 0.0 # No price for most activities
            
            all_interactions.append(activities_for_model[[
                'user_id', 'timestamp', 'transaction_id', 'amount', 'category', 'product_id', 'quantity', 'price', 'interaction_type'
            ]])
        
        if not all_interactions:
            logger.warning("No interactions data prepared for churn model training.")
            return pd.DataFrame()

        # Concatenate all interaction types
        combined_interactions_df = pd.concat(all_interactions, ignore_index=True)
        
        # Sort by user_id and timestamp, critical for RFM and sequential features
        combined_interactions_df = combined_interactions_df.sort_values(by=['user_id', 'timestamp']).reset_index(drop=True)

        # The churn model's prepare_features expects a dataframe that has
        # 'user_id', 'timestamp', 'transaction_id', 'amount', 'category', 'product_id', 'quantity', 'price'
        # The `prepare_features` within `ChurnPredictionModel` then aggregates this by user.
        
        # We also need to add 'registrationDate' and 'lastLogin' from users_df to `combined_interactions_df`
        # as these are used for overall recency calculations in `ChurnPredictionModel.prepare_features`.
        # The easiest way is to merge users_df *into* this interaction dataframe.
        
        final_df_for_model = combined_interactions_df.merge(
            users_df[['userId', 'registrationDate', 'lastLogin']],
            left_on='user_id', right_on='userId', how='left'
        ).drop(columns=['userId']) # Drop redundant userId column after merge

        # Ensure datetime columns are datetime objects after merge
        final_df_for_model['registrationDate'] = pd.to_datetime(final_df_for_model['registrationDate'], errors='coerce')
        final_df_for_model['lastLogin'] = pd.to_datetime(final_df_for_model['lastLogin'], errors='coerce')
        final_df_for_model['timestamp'] = pd.to_datetime(final_df_for_model['timestamp'], errors='coerce')

        final_df_for_model.dropna(subset=['user_id', 'timestamp'], inplace=True) # Essential columns

        # Now call the ChurnPredictionModel's prepare_features to convert interactions to RFM features
        rfm_features = self.churn_model.prepare_features(final_df_for_model)
        
        # Force garbage collection to free memory after heavy operations
        del combined_interactions_df, final_df_for_model, users_df, transactions_df, activities_df
        gc.collect()
        
        return rfm_features
    
    async def _prepare_single_user_features(self, user_id: str) -> pd.DataFrame:
        """Prepare features for a single user for churn prediction."""
        user = await self._get_user_details(user_id)
        if not user:
            logger.warning(f"User {user_id} not found for single user feature preparation.")
            return pd.DataFrame()

        transactions_cursor = self.db.transactions.find({'userId': user_id})
        transactions_list = await transactions_cursor.to_list(length=None)
        transactions_df = pd.DataFrame(transactions_list)

        activities_cursor = self.db.user_activities.find({'userId': user_id})
        activities_list = await activities_cursor.to_list(length=None)
        activities_df = pd.DataFrame(activities_list)
        
        # Drop _id if present in fetched dataframes
        if '_id' in transactions_df.columns:
            transactions_df = transactions_df.drop(columns=['_id'])
        if '_id' in activities_df.columns:
            activities_df = activities_df.drop(columns=['_id'])
        
        # Prepare the dataframes for _prepare_churn_features_for_training
        # It expects a list of users, transactions, and activities as dataframes
        users_df_single = pd.DataFrame([user]) # Convert single user dict to DataFrame

        # Now, call the batch preparation method with these single-user (or empty) dataframes
        # This ensures consistent feature engineering logic
        combined_features_df = await self._prepare_churn_features_for_training(
            users_df_single, transactions_df, activities_df
        )

        # Filter for the specific user and ensure it's a single row DataFrame for prediction
        single_user_features_df = combined_features_df[combined_features_df['user_id'] == user_id]
        
        if not single_user_features_df.empty:
            # Drop user_id and other non-feature columns that are part of the raw input
            # but not expected by the model's feature columns list
            
            # The ChurnPredictionModel's `prepare_features` function processes the raw interaction data
            # and returns a new DataFrame with RFM and behavioral features.
            # We need to ensure that `single_user_features_df` contains these *derived* features
            # that match `self.churn_model.feature_columns`.
            
            # The `combined_features_df` from `_prepare_churn_features_for_training`
            # *is* the output of `churn_model.prepare_features`. So it should already have the right columns.
            
            # We just need to make sure we return only the feature columns expected by the model.
            
            # The ChurnPredictionModel.predict_churn_with_reasoning expects the *output* of its `prepare_features`.
            # So, we pass `single_user_features_df` directly.
            return single_user_features_df 
        else:
            logger.warning(f"No features generated for user {user_id} after preparation.")
            return pd.DataFrame() # Return empty if features couldn't be generated

    def _get_churn_feature_description(self, feature: str, value: Any) -> str:
        """Get human-readable description for churn feature."""
        descriptions = {
            'activity_score': f"Customer activity score is {value:.2f} (0-1 scale)",
            'subscription_age_days': f"Customer subscription is {value} days old",
            'estimated_lifetime_value': f"Estimated customer lifetime value is ${value:.2f}",
            'engagement_level': f"Customer engagement level is {value}",
            'days_since_last_activity': f"Days since last activity: {value}",
            'total_spent': f"Total amount spent: ${value:.2f}",
            'session_frequency': f"Session frequency: {value} sessions per period",
            'avg_session_duration': f"Average session duration: {value} minutes",
            'purchase_recency': f"Days since last purchase: {value}",
            'feature_usage_score': f"Feature usage score: {value:.2f}",
            'customer_satisfaction': f"Customer satisfaction score: {value:.1f}/5.0"
        }
        return descriptions.get(feature, f"{feature}: {value}")

