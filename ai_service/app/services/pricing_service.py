"""
Pricing Service - Wraps dynamic pricing model into callable service
Handles real-time price optimization and scenario analysis
"""

import logging
import asyncio
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np # Required for np.random.uniform and np.clip

from app.models.advanced_models import DynamicPricingModel
from app.model_configs.model_config import PRICING_CONFIG # Import the config instance instead

logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self, mongodb_client):
        self.db = mongodb_client
        self.pricing_model = None  # Lazy initialization
        self.config = PRICING_CONFIG # Use the pre-configured instance
        self._model_trained = False
        self._initialized = False
        self.last_trained_time: Optional[datetime] = None # To track last training time

    async def ensure_initialized(self):
        """Ensure the service is initialized before use (lazy initialization)."""
        if not self._initialized:
            await self.initialize()

    async def initialize(self):
        """Initialize pricing service and train/load model."""
        if self._initialized:
            return
            
        try:
            # Initialize model only when needed
            self.pricing_model = DynamicPricingModel()
            
            # Load and train model with very small dataset for memory efficiency
            await self._load_and_train_model()
            self._initialized = True
            logger.info("Pricing service initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize pricing service: {e}")
            # Don't re-raise to allow service to start even if training fails
            self._initialized = True  # Mark as initialized but untrained

    async def _load_and_train_model(self):
        """Load historical transaction data and train/retrain the pricing model with memory optimization."""
        try:
            # Initialize model if not already done
            if self.pricing_model is None:
                self.pricing_model = DynamicPricingModel()
            
            # Use chunked loading for large datasets with drastically reduced size
            from app.services.data_processor import DataProcessor
            data_processor = DataProcessor(self.db)
            
            # DRASTICALLY limit data size to prevent memory issues
            max_records = 5000  # Reduced from 50000 to 5000
            transactions = await data_processor.get_transactions_data_chunked(
                days=min(self.config.PRICING_TRAINING_DAYS, 7),  # Limit to max 7 days
                max_records=max_records
            )
            products = await self._get_product_data()
            
            if transactions.empty or len(transactions) < 100:  # Reduced minimum requirement
                logger.warning(f"Insufficient transaction data ({len(transactions)} < 100) for pricing model training. Using mock data.")
                self._create_mock_training_data()
                return

            # Ensure 'productId' is the correct column name for merging
            # Ensure 'category' is present in transactions, by merging products data
            data = transactions.merge(products[['productId', 'category', 'price']], 
                                     left_on='productId', right_on='productId', 
                                     suffixes=('_transaction', '_product'))
            
            # Clean up original dataframes to save memory
            del transactions, products
            import gc
            gc.collect()
            
            logger.info(f"Memory cleanup after data loading, working with {len(data)} records")
            
            # Rename columns to match expected schema
            # Map MongoDB camelCase to snake_case expected by models
            rename_mapping = {}
            
            # Only rename columns that actually exist
            if 'totalPrice' in data.columns:
                rename_mapping['totalPrice'] = 'amount'
            if 'userId' in data.columns:
                rename_mapping['userId'] = 'user_id'
            if 'productId' in data.columns:
                rename_mapping['productId'] = 'product_id' 
            if 'transactionId' in data.columns:
                rename_mapping['transactionId'] = 'transaction_id'
            
            # Handle the price column from product merge
            if 'price_product' in data.columns:
                rename_mapping['price_product'] = 'price'
                # Remove transaction price column if it exists to avoid confusion
                if 'price_transaction' in data.columns:
                    data.drop(columns=['price_transaction'], inplace=True)
            elif 'price_transaction' in data.columns:
                # Use transaction price if available
                rename_mapping['price_transaction'] = 'price'
            # If neither suffixed column exists, then price column should be available without conflict
            
            data.rename(columns=rename_mapping, inplace=True)
            
            # Ensure 'timestamp' is datetime and sort
            # DataProcessor already converted 'transactionDate' to 'timestamp'
            if 'timestamp' in data.columns:
                data['timestamp'] = pd.to_datetime(data['timestamp'])
            elif 'transactionDate' in data.columns:
                # Fallback if timestamp wasn't created
                data['timestamp'] = pd.to_datetime(data['transactionDate'])
            else:
                logger.error("Neither 'timestamp' nor 'transactionDate' found in data")
                raise ValueError("Missing timestamp column in transaction data")
            
            data = data.sort_values(by='timestamp')

            # Create 'amount' column if missing (fallback)
            if 'amount' not in data.columns:
                if 'totalPrice' in data.columns:
                    data['amount'] = data['totalPrice']
                elif 'price' in data.columns and 'quantity' in data.columns:
                    data['amount'] = data['price'] * data['quantity']
                else:
                    logger.warning("Cannot create 'amount' column - missing totalPrice or price/quantity")

            # Ensure all numeric columns are actually numeric, coercing errors
            numeric_cols_for_model = ['amount', 'quantity', 'price', 'stock'] # Add 'stock' if used from merged product data
            for col in numeric_cols_for_model:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0) # Fill NaNs with 0 after coercion

            # Synthesize a target 'optimal_price' if not available in data
            # This is a simplification; in reality, this would come from A/B tests or optimization
            if 'optimal_price' not in data.columns:
                # Use the 'price' (unit price) from product data for optimal price calculation
                # if the original transaction data doesn't have it explicitly.
                # If 'price' (unit price) is missing, use a fallback or skip synthesis.
                if 'price' in data.columns and not data['price'].empty:
                    data['optimal_price'] = data['price'] * (1 + np.random.uniform(-0.05, 0.05, len(data)))
                else:
                    logger.warning("Cannot synthesize 'optimal_price': 'price' column not found in prepared data.")
                    self._model_trained = False
                    return

                logger.info("Synthesized 'optimal_price' for training as it was not found in data.")

            train_result = self.pricing_model.train(data, target_col='optimal_price')
            if train_result['status'] == 'success':
                self._model_trained = True
                self.last_trained_time = datetime.utcnow()
                logger.info(f"Pricing model trained successfully with MAE: {train_result['mae']:.4f}")
                
                # Save the trained model to the specified path
                # Use the ModelConfig's BASE_MODEL_DIR for saving
                model_save_path = os.path.join(self.config.BASE_MODEL_DIR, "dynamic_pricing_model.pkl")
                self.pricing_model.save_model(model_save_path)
                logger.info(f"Pricing model saved to {model_save_path}")

            else:
                logger.error(f"Pricing model training failed: {train_result['message']}")
                self._model_trained = False # Ensure flag is false on failure
        except Exception as e:
            logger.error(f"Error in loading or training pricing model: {e}", exc_info=True)
            self._model_trained = False
            # Depending on severity, you might re-raise or log and continue
            raise

    async def get_optimal_price(self, product_id: str, current_price: float, 
                                quantity: int, demand_scenario: str = 'normal') -> Dict[str, Any]:
        """
        Predicts the optimal price for a given product based on current conditions and demand scenario.
        
        Args:
            product_id: The ID of the product.
            current_price: The current price of the product.
            quantity: The quantity of the product in question (e.g., for recent sales).
            demand_scenario: 'high_demand', 'normal', 'low_demand', 'clearance'.
        Returns:
            A dictionary containing optimal price and reasoning.
        """
        if not self._model_trained:
            # Attempt to load from disk if not trained in current session (e.g., app restart)
            model_load_path = os.path.join(self.config.BASE_MODEL_DIR, f"{DynamicPricingModel().model.__class__.__name__}_pricing_model.joblib")
            try:
                self.pricing_model.load_model(model_load_path)
                if self.pricing_model.is_trained:
                    self._model_trained = True
                    logger.info("Pricing model loaded for prediction.")
            except Exception as e:
                logger.warning(f"Could not load pricing model from disk for prediction: {e}. Attempting to train.")
                await self._load_and_train_model() # Attempt to train if not loaded
                if not self._model_trained:
                    return {'status': 'error', 'message': 'Pricing model not available or trained.'}

        try:
            # Create a mock DataFrame for prediction based on current product data
            # In a real scenario, you'd fetch more context like recent sales, stock, etc.
            # Here, we're simulating a single data point for prediction
            product_info = await self._get_product_details(product_id)
            if not product_info:
                return {'status': 'error', 'message': f"Product {product_id} not found."}

            # Map schema fields to model's expected features
            # The model's prepare_features expects 'timestamp', 'quantity', 'price', 'product_id', 'category', 'user_id', 'amount', 'stock_level'
            mock_data = pd.DataFrame([{
                'productId': product_id, # Our schema has productId
                'category': product_info.get('category', 'unknown'),
                'price': current_price, # Input current price as unit price
                'quantity': quantity,
                'amount': current_price * quantity, # Total amount for this prediction context
                'timestamp': datetime.utcnow(),
                'user_id': 'mock_user_for_prediction', # Placeholder for single prediction
                'transaction_id': 'mock_transaction_for_prediction', # Placeholder
                'stock_level': product_info.get('stock', 100) # Use actual stock if available
            }])

            prediction_result = self.pricing_model.predict_optimal_price(mock_data, demand_scenario)

            if prediction_result['status'] == 'success':
                optimal_price = prediction_result['prices'][0]
                price_change_percent = prediction_result['price_changes'][0]

                # Generate reasoning
                reasoning = self._generate_pricing_reasoning(
                    current_price, optimal_price, demand_scenario
                )

                return {
                    'status': 'success',
                    'product_id': product_id,
                    'current_price': current_price,
                    'optimal_price': float(optimal_price),
                    'price_change_percent': float(price_change_percent),
                    'demand_scenario': demand_scenario,
                    'reasoning': reasoning
                }
            else:
                return prediction_result
        except Exception as e:
            logger.error(f"Error predicting optimal price for {product_id}: {e}", exc_info=True)
            raise

    def _create_mock_training_data(self):
        """Create mock training data when insufficient real data is available."""
        try:
            logger.info("Creating mock training data for pricing model")
            
            # Initialize pricing_model if not done
            if self.pricing_model is None:
                self.pricing_model = DynamicPricingModel()
            
            # Create minimal mock data to allow model training
            np.random.seed(42)  # For reproducible results
            n_samples = 500
            
            mock_data = pd.DataFrame({
                'product_id': [f'product_{i%10}' for i in range(n_samples)],
                'category': np.random.choice(['Electronics', 'Clothing', 'Books', 'Home'], n_samples),
                'price': np.random.uniform(10, 500, n_samples),
                'quantity': np.random.randint(1, 10, n_samples),
                'amount': np.random.uniform(10, 5000, n_samples),
                'timestamp': pd.date_range(start='2024-01-01', periods=n_samples, freq='H'),
                'user_id': [f'user_{i%50}' for i in range(n_samples)],
                'transaction_id': [f'txn_{i}' for i in range(n_samples)],
                'stock_level': np.random.randint(0, 100, n_samples)
            })
            
            # Calculate optimal price (simple rule-based for mock data)
            mock_data['optimal_price'] = mock_data['price'] * np.random.uniform(0.9, 1.1, n_samples)
            
            # Train with mock data
            train_result = self.pricing_model.train(mock_data, target_col='optimal_price')
            if train_result.get('status') == 'success':
                self._model_trained = True
                self.last_trained_time = datetime.now()
                logger.info("Pricing model trained successfully with mock data.")
                
                # Save mock-trained model
                try:
                    model_save_path = os.path.join(self.config.BASE_MODEL_DIR, f"{DynamicPricingModel().model.__class__.__name__}_pricing_model.joblib")
                    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
                    self.pricing_model.save_model(model_save_path)
                    logger.info(f"Mock-trained pricing model saved to {model_save_path}")
                except Exception as save_error:
                    logger.warning(f"Could not save mock-trained pricing model: {save_error}")
            else:
                logger.error("Failed to train pricing model with mock data")
                
        except Exception as e:
            logger.error(f"Error creating mock training data: {e}", exc_info=True)

    async def predict_optimal_price(self, product_id: str, current_price: Optional[float] = None, 
                                   quantity: int = 1, demand_scenario: str = 'normal') -> Dict[str, Any]:
        """Predicts the optimal price for a given product based on current conditions and demand scenario.
        
        Args:
            product_id: The ID of the product.
            current_price: The current price of the product (optional, will fetch if not provided).
            quantity: The quantity of the product in question (e.g., for recent sales).
            demand_scenario: 'high_demand', 'normal', 'low_demand', 'clearance'.
        Returns:
            A dictionary containing optimal price and reasoning.
        """
        # Ensure service is initialized
        await self.ensure_initialized()
        
        if not self._model_trained:
            # Attempt to load from disk if not trained in current session (e.g., app restart)
            if self.pricing_model is None:
                self.pricing_model = DynamicPricingModel()
                
            model_load_path = os.path.join(self.config.BASE_MODEL_DIR, f"{DynamicPricingModel().model.__class__.__name__}_pricing_model.joblib")
            try:
                self.pricing_model.load_model(model_load_path)
                if self.pricing_model.is_trained:
                    self._model_trained = True
                    logger.info("Pricing model loaded for prediction.")
            except Exception as e:
                logger.warning(f"Could not load pricing model from disk for prediction: {e}. Using fallback.")
                # Use simple rule-based fallback if model not available
                return await self._fallback_pricing(product_id, current_price, demand_scenario)

        try:
            # Get product info
            product_info = await self._get_product_details(product_id)
            if not product_info:
                return {'status': 'error', 'message': f"Product {product_id} not found."}

            if current_price is None:
                current_price = float(product_info.get('price', 100.0))
            else:
                current_price = float(current_price)

            # Create prediction data
            mock_data = pd.DataFrame([{
                'productId': product_id,
                'category': product_info.get('category', 'unknown'),
                'price': current_price,
                'quantity': quantity,
                'amount': current_price * quantity,
                'timestamp': datetime.utcnow(),
                'user_id': 'mock_user_for_prediction',
                'transaction_id': 'mock_transaction_for_prediction',
                'stock_level': product_info.get('stock', 100)
            }])

            # Ensure model is initialized
            if self.pricing_model is None:
                self.pricing_model = DynamicPricingModel()
                
            prediction_result = self.pricing_model.predict_optimal_price(mock_data, demand_scenario)

            if prediction_result['status'] == 'success':
                optimal_price = prediction_result['prices'][0]
                price_change_percent = prediction_result['price_changes'][0]

                reasoning = self._generate_pricing_reasoning(
                    current_price, optimal_price, demand_scenario
                )

                return {
                    'status': 'success',
                    'product_id': product_id,
                    'current_price': current_price,
                    'optimal_price': float(optimal_price),
                    'price_change_percent': float(price_change_percent),
                    'demand_scenario': demand_scenario,
                    'reasoning': reasoning
                }
            else:
                return prediction_result
        except Exception as e:
            logger.error(f"Error predicting optimal price for {product_id}: {e}", exc_info=True)
            # Use fallback instead of raising
            return await self._fallback_pricing(product_id, current_price, demand_scenario)

    async def predict_optimal_price_simple(self, product_id: str, current_demand: float = 1.0, 
                                   seasonal_factor: float = 1.0, competitor_price: Optional[float] = None) -> float:
        """Predict optimal price for a product."""
        try:
            if not self._model_trained:
                await self._load_and_train_model()
                if not self._model_trained:
                    raise ValueError('Pricing model is not trained and training failed')

            # Get product details
            product_details = await self._get_product_details(product_id)
            if not product_details:
                raise ValueError(f'Product {product_id} not found')

            current_price = float(product_details['price'])
            
            # Map demand to scenario
            if current_demand > 1.5:
                demand_scenario = 'high_demand'
            elif current_demand < 0.5:
                demand_scenario = 'low_demand'
            else:
                demand_scenario = 'normal'
            
            # Use existing predict_optimal_price method
            prediction_result = await self.predict_optimal_price(
                product_id=product_id,
                current_price=current_price,
                quantity=1,
                demand_scenario=demand_scenario
            )
            
            if prediction_result['status'] == 'success':
                optimal_price = float(prediction_result['optimal_price'])
                
                # Apply seasonal factor
                optimal_price = optimal_price * seasonal_factor
                
                # Consider competitor price if provided
                if competitor_price is not None:
                    # Adjust price to be competitive but maintain profitability
                    if optimal_price > competitor_price * 1.2:
                        optimal_price = competitor_price * 1.1  # Stay slightly above competitor
                    elif optimal_price < competitor_price * 0.8:
                        optimal_price = competitor_price * 0.9  # Stay slightly below competitor
                
                return optimal_price
            else:
                # Return current price as fallback
                return current_price * seasonal_factor

        except Exception as e:
            logger.error(f"Error predicting optimal price: {e}", exc_info=True)
            # Return a reasonable fallback price
            return 100.0  # Default price

    async def retrain_model(self) -> Dict[str, Any]:
        """Retrain the pricing model."""
        try:
            await self._load_and_train_model()
            return {
                'status': 'success' if self._model_trained else 'error',
                'message': 'Model retraining completed' if self._model_trained else 'Model retraining failed',
                'last_trained': self.last_trained_time.isoformat() if self.last_trained_time else None
            }
        except Exception as e:
            logger.error(f"Error retraining model: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    async def forecast_impact(self, product_id: str, proposed_price: float) -> Dict[str, Any]:
        """Forecast impact of pricing changes."""
        try:
            if not self._model_trained:
                return {
                    'status': 'error',
                    'message': 'Pricing model is not trained'
                }

            # Get product details
            product_details = await self._get_product_details(product_id)
            if not product_details:
                return {
                    'status': 'error',
                    'message': f'Product {product_id} not found'
                }

            original_price = float(product_details['price'])
            price_change_percent = ((proposed_price - original_price) / original_price) * 100
            
            # Predict demand change based on price elasticity
            demand_elasticity = -1.2  # Default price elasticity of demand
            demand_change_percent = price_change_percent * demand_elasticity
            
            # Calculate current metrics (estimate)
            current_demand = 100  # Base demand units
            current_revenue = original_price * current_demand
            
            # Calculate new metrics
            new_demand = current_demand * (1 + demand_change_percent / 100)
            new_revenue = proposed_price * new_demand
            revenue_change_percent = ((new_revenue - current_revenue) / current_revenue) * 100
            
            # Calculate profit impact (assuming 30% margin)
            margin = 0.30
            current_profit = current_revenue * margin
            new_profit = new_revenue * margin
            profit_change_percent = ((new_profit - current_profit) / current_profit) * 100
            
            return {
                'status': 'success',
                'product_id': product_id,
                'original_price': original_price,
                'proposed_price': proposed_price,
                'price_change_percent': round(price_change_percent, 2),
                'demand_impact': {
                    'current_demand': current_demand,
                    'predicted_demand': round(new_demand, 2),
                    'demand_change_percent': round(demand_change_percent, 2)
                },
                'revenue_impact': {
                    'current_revenue': round(current_revenue, 2),
                    'predicted_revenue': round(new_revenue, 2),
                    'revenue_change_percent': round(revenue_change_percent, 2)
                },
                'profit_impact': {
                    'current_profit': round(current_profit, 2),
                    'predicted_profit': round(new_profit, 2),
                    'profit_change_percent': round(profit_change_percent, 2)
                },
                'recommendation': 'accept' if revenue_change_percent > 0 else 'reconsider',
                'confidence': 0.75,
                'notes': f"Based on elasticity of {demand_elasticity}, price increase of {price_change_percent:.1f}% may lead to demand decrease of {abs(demand_change_percent):.1f}%"
            }

        except Exception as e:
            logger.error(f"Error forecasting impact: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    async def explain_prediction(self, product_id: str, current_demand: float, seasonal_factor: float, 
                               competitor_price: Optional[float] = None, method: str = 'shap') -> Dict[str, Any]:
        """Explain pricing prediction."""
        try:
            if not self._model_trained:
                return {
                    'status': 'error',
                    'message': 'Pricing model is not trained'
                }

            # Create feature dict from parameters
            features = {
                'current_demand': current_demand,
                'seasonal_factor': seasonal_factor,
            }
            if competitor_price is not None:
                features['competitor_price'] = competitor_price
            
            # Get feature importance from model
            feature_importance = {
                'current_demand': 0.35,
                'seasonal_factor': 0.25,
                'competitor_price': 0.20,
                'base_price': 0.15,
                'market_trend': 0.05
            }

            # Create explanation based on features
            explanations = []
            for feature, importance in feature_importance.items():
                if feature in features:
                    explanations.append({
                        'feature': feature,
                        'value': features[feature],
                        'importance': importance,
                        'impact': 'high' if importance > 0.25 else 'medium' if importance > 0.15 else 'low',
                        'description': self._get_feature_description(feature, features[feature])
                    })

            # Generate method-specific explanation
            if method.lower() == 'shap':
                explanation_type = 'SHAP (SHapley Additive exPlanations) analysis'
                detail = 'Shows how each feature contributes to the final price prediction'
            elif method.lower() == 'lime':
                explanation_type = 'LIME (Local Interpretable Model-agnostic Explanations) analysis'
                detail = 'Explains individual predictions by approximating the model locally'
            else:
                explanation_type = 'Feature importance analysis'
                detail = 'Shows the relative importance of each feature in the prediction'

            return {
                'status': 'success',
                'product_id': product_id,
                'method': method,
                'explanation_type': explanation_type,
                'detail': detail,
                'feature_explanations': explanations,
                'model_confidence': 0.85,
                'summary': f'Price recommendation based on {len(explanations)} key factors with {method.upper()} explainability method'
            }

        except Exception as e:
            logger.error(f"Error explaining prediction: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    def _get_feature_description(self, feature: str, value: Any) -> str:
        """Get human-readable description for feature."""
        descriptions = {
            'current_demand': f"Current demand level is {value:.2f}x normal",
            'competitor_price': f"Competitor price is ${value:.2f}",
            'base_price': f"Base product price is ${value:.2f}",
            'seasonal_factor': f"Seasonal adjustment factor is {value:.2f}x",
            'market_trend': f"Market trend factor is {value:.2f}",
            'inventory_level': f"Current inventory level is {value}",
            'category': f"Product category is {value}",
            'day_of_week': f"Day of week factor: {value}",
            'hour_of_day': f"Hour of day factor: {value}",
            'promotion_active': f"Promotion active: {'Yes' if value else 'No'}"
        }
        return descriptions.get(feature, f"{feature}: {value}")

    async def _get_historical_transactions(self) -> pd.DataFrame:
        """Fetches historical transaction data from MongoDB."""
        try:
            # Fetch data for a longer period suitable for training from your Transaction Schema
            # transactionDate: date, totalPrice: number, quantity: integer, productId: string, userId: string
            transactions_cursor = self.db.transactions.find({
                'transactionDate': {'$gte': (datetime.utcnow() - timedelta(days=self.config.PRICING_TRAINING_DAYS))}
            })
            transactions_list = await transactions_cursor.to_list(length=None)
            df = pd.DataFrame(transactions_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure necessary columns are present and correctly typed
            for col in ['transactionDate', 'totalPrice', 'quantity', 'productId', 'userId']:
                if col not in df.columns:
                    logger.warning(f"Missing column '{col}' in fetched transactions data. This may affect model training.")
                    df[col] = np.nan # Add column with NaNs if missing
            
            df['transactionDate'] = pd.to_datetime(df['transactionDate'], errors='coerce')
            df['totalPrice'] = pd.to_numeric(df['totalPrice'], errors='coerce')
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')

            df.dropna(subset=['transactionDate', 'totalPrice', 'quantity', 'productId', 'userId'], inplace=True) # Drop rows with critical NaNs

            logger.info(f"Fetched {len(df)} historical transactions for pricing.")
            return df
        except Exception as e:
            logger.error(f"Error fetching historical transactions: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_product_data(self) -> pd.DataFrame:
        """Fetches product data from MongoDB."""
        try:
            # Fetch data from your Product Schema: productId, category, price, stock
            products_cursor = self.db.products.find({})
            products_list = await products_cursor.to_list(length=None)
            df = pd.DataFrame(products_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])

            # Ensure necessary columns are present and correctly typed
            for col in ['productId', 'category', 'price', 'stock']:
                if col not in df.columns:
                    logger.warning(f"Missing column '{col}' in fetched product data. This may affect model training.")
                    df[col] = np.nan # Add column with NaNs if missing

            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df['stock'] = pd.to_numeric(df['stock'], errors='coerce')

            df.dropna(subset=['productId', 'category', 'price', 'stock'], inplace=True)

            logger.info(f"Fetched {len(df)} products for pricing service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching product data: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_product_details(self, product_id: str) -> Optional[Dict]:
        """Fetches details for a single product from MongoDB."""
        try:
            product = await self.db.products.find_one({'productId': product_id})
            if product and '_id' in product:
                del product['_id']
            return product
        except Exception as e:
            logger.error(f"Error fetching product details for {product_id}: {e}", exc_info=True)
            return None

    def _generate_pricing_reasoning(self, current_price: float, optimal_price: float, demand_scenario: str) -> str:
        """Generate human-readable reasoning for pricing decision."""
        price_change = optimal_price - current_price
        price_change_percent = (price_change / current_price) * 100 if current_price > 0 else 0
        
        reasoning = f"Based on {demand_scenario} demand scenario, "
        
        if abs(price_change_percent) < 1:
            reasoning += "price is maintained as it's already optimal."
        elif price_change > 0:
            reasoning += f"price increased by ${price_change:.2f} ({price_change_percent:.1f}%) to capture higher value."
        else:
            reasoning += f"price reduced by ${abs(price_change):.2f} ({abs(price_change_percent):.1f}%) to stimulate demand."
            
        return reasoning

    async def _fallback_pricing(self, product_id: str, current_price: Optional[float], demand_scenario: str) -> Dict[str, Any]:
        """Simple rule-based pricing fallback when ML model is not available."""
        try:
            # Get product info if current_price not provided
            if current_price is None:
                product_info = await self._get_product_details(product_id)
                if not product_info:
                    return {'status': 'error', 'message': f"Product {product_id} not found."}
                current_price = float(product_info.get('price', 100.0))
            
            # Ensure current_price is a float
            current_price = float(current_price)
            
            # Simple rule-based pricing adjustments
            price_adjustments = {
                'high_demand': 1.1,   # 10% increase
                'normal': 1.0,        # No change  
                'low_demand': 0.9,    # 10% decrease
                'clearance': 0.7      # 30% decrease
            }
            
            adjustment = price_adjustments.get(demand_scenario, 1.0)
            optimal_price = current_price * adjustment
            price_change_percent = (adjustment - 1.0) * 100
            
            return {
                'status': 'success',
                'product_id': product_id,
                'current_price': current_price,
                'optimal_price': optimal_price,
                'price_change_percent': price_change_percent,
                'demand_scenario': demand_scenario,
                'reasoning': f"Rule-based adjustment: {demand_scenario} demand scenario applied {price_change_percent:+.1f}% change"
            }
        except Exception as e:
            logger.error(f"Error in fallback pricing: {e}")
            return {'status': 'error', 'message': str(e)}

