import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, classification_report, roc_auc_score
import lightgbm as lgb
import xgboost as xgb
from category_encoders import TargetEncoder
from imblearn.over_sampling import SMOTE
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamicPricingModel:
    """Advanced dynamic pricing model with demand elasticity and competitive analysis."""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.is_trained = False
        
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for pricing model."""
        features = data.copy()
        
        # Ensure required columns are present
        required_cols = ['timestamp', 'quantity', 'price', 'amount']
        missing_cols = [col for col in required_cols if col not in features.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns for pricing features: {missing_cols}")
        
        # Check for ID columns with flexible naming
        if 'product_id' not in features.columns and 'productId' in features.columns:
            features['product_id'] = features['productId']
        if 'user_id' not in features.columns and 'userId' in features.columns:
            features['user_id'] = features['userId']
        
        # Ensure we have product_id and user_id columns
        if 'product_id' not in features.columns:
            raise ValueError("'product_id' column is required for pricing model features")
        if 'user_id' not in features.columns:
            raise ValueError("'user_id' column is required for pricing model features")
        
        # Time-based features
        features['hour'] = pd.to_datetime(features['timestamp']).dt.hour
        features['day_of_week'] = pd.to_datetime(features['timestamp']).dt.dayofweek
        features['month'] = pd.to_datetime(features['timestamp']).dt.month
        features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # Demand elasticity features
        # Add a small epsilon to avoid division by zero
        features['demand_ratio'] = features['quantity'] / (features['quantity'].rolling(window=7).mean() + 1e-6)
        
        # Ensure that quantity.pct_change() is not zero before dividing
        # Convert to numpy arrays to avoid Series alignment issues
        price_pct_change = np.array(features['price'].pct_change().fillna(0), dtype=float)
        quantity_pct_change = np.array(features['quantity'].pct_change().fillna(0), dtype=float)
        
        # Safe division with zero handling
        safe_quantity_pct_change = quantity_pct_change + 1e-6
        features['price_elasticity'] = np.where(safe_quantity_pct_change != 0, 
                                               price_pct_change / safe_quantity_pct_change, 
                                               0)
        
        # Market features
        # Handle cases where sum might be zero
        features['market_share'] = features.groupby('product_id')['quantity'].transform(
            lambda x: x / (x.sum() + 1e-6)
        )
        # Handle cases where std might be zero - check if category column exists
        if 'category' in features.columns:
            features['competitive_index'] = features.groupby('category')['price'].transform(
                lambda x: (x - x.mean()) / (x.std() + 1e-6)
            ).fillna(0)
        else:
            # Use product_id grouping as fallback if category doesn't exist
            features['competitive_index'] = features.groupby('product_id')['price'].transform(
                lambda x: (x - x.mean()) / (x.std() + 1e-6)
            ).fillna(0)
            logger.info("Using product_id for competitive index calculation - 'category' column not found")
        
        # Inventory features
        stock_level = features.get('stock_level', pd.Series([100] * len(features), index=features.index))
        if isinstance(stock_level, (int, float)):
            stock_level = pd.Series([stock_level] * len(features), index=features.index)
        
        # Ensure stock_level has the same index as features for proper alignment
        if not isinstance(stock_level, pd.Series):
            stock_level = pd.Series(stock_level, index=features.index)
        
        # Convert to numpy arrays to avoid Series alignment issues
        quantity_values = np.array(features['quantity'].values, dtype=float)
        stock_level_safe = np.array(stock_level.replace(0, 1).values, dtype=float)
        features['inventory_turnover'] = quantity_values / stock_level_safe
        
        # Convert to numpy arrays to avoid Series alignment issues
        stock_level_values = np.array(stock_level.values, dtype=float)
        quantity_rolling_mean = np.array(features['quantity'].rolling(window=3).mean().fillna(features['quantity'].mean()).values, dtype=float)
        features['stockout_risk'] = (stock_level_values < quantity_rolling_mean).astype(int)
        
        # Customer behavior features
        features['customer_lifetime_value'] = features.groupby('user_id')['amount'].transform('sum')
        features['avg_order_value'] = features.groupby('user_id')['amount'].transform('mean')
        features['purchase_frequency'] = features.groupby('user_id')['user_id'].transform('count')
        
        # Seasonal features
        features['quarter'] = pd.to_datetime(features['timestamp']).dt.quarter
        features['is_holiday_season'] = features['month'].isin([11, 12]).astype(int)
        
        return features
    
    def train(self, data: pd.DataFrame, target_col: str = 'optimal_price') -> Dict:
        """Train the dynamic pricing model."""
        try:
            logger.info("Training dynamic pricing model...")
            
            # Prepare features
            features = self.prepare_features(data)
            
            # Select feature columns (exclude non-numeric and target)
            numeric_cols = features.select_dtypes(include=[np.number]).columns
            exclude_cols = ['timestamp', target_col, 'transaction_id', 'user_id', 'product_id']
            self.feature_columns = [col for col in numeric_cols if col not in exclude_cols]
            
            X = features[self.feature_columns].fillna(0)
            y = features[target_col] if target_col in features.columns else features['price'] * 1.1  # Synthetic target
            
            # Handle cases where X or y might be empty or have issues
            if X.empty or y.empty or len(X) != len(y):
                raise ValueError("Prepared data (X or y) is empty or mismatched.")
            if len(X) < 2: # Need at least 2 samples for train_test_split
                 raise ValueError("Insufficient data for training after feature preparation.")

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train ensemble model
            models = {
                'rf': RandomForestRegressor(n_estimators=100, random_state=42),
                'lgb': lgb.LGBMRegressor(random_state=42, verbose=-1),
                'xgb': xgb.XGBRegressor(random_state=42, verbosity=0)
            }
            
            trained_models = {}
            scores = {}
            
            for name, model in models.items():
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                mae = mean_absolute_error(y_test, y_pred)
                
                trained_models[name] = model
                scores[name] = mae
                logger.info(f"{name.upper()} MAE: {mae:.4f}")
            
            # Use best performing model
            best_model_name = min(scores.keys(), key=lambda k: scores[k])
            self.model = trained_models[best_model_name]
            self.is_trained = True
            
            # Model will be saved by ModelManager with correct path
            
            return {
                'status': 'success',
                'best_model': best_model_name,
                'mae': scores[best_model_name],
                'all_scores': scores,
                'feature_count': len(self.feature_columns)
            }
            
        except Exception as e:
            logger.error(f"Error training pricing model: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def predict_optimal_price(self, data: pd.DataFrame, 
                            demand_scenario: str = 'normal') -> Dict:
        """Predict optimal pricing with scenario analysis."""
        if not self.is_trained:
            return {'status': 'error', 'message': 'Model not trained'}
        
        try:
            features = self.prepare_features(data)
            X = features[self.feature_columns].fillna(0)
            
            # Check if X is empty after feature preparation
            if X.empty:
                return {'status': 'error', 'message': 'No features generated for prediction.'}

            # Check if model is trained
            if not self.model:
                return {'status': 'error', 'message': 'Model is not trained'}
            
            X_scaled = self.scaler.transform(X)
            
            base_prices = self.model.predict(X_scaled)
            
            # Scenario adjustments
            scenario_multipliers = {
                'high_demand': 1.15,
                'normal': 1.0,
                'low_demand': 0.9,
                'clearance': 0.7
            }
            
            # Convert to numpy array to handle operations properly
            if hasattr(base_prices, 'values'):
                base_prices = base_prices.values
            optimal_prices = base_prices * scenario_multipliers.get(demand_scenario, 1.0)
            
            # Price bounds (prevent extreme pricing)
            if 'price' in data.columns:
                current_prices = np.array(data['price'])  # Convert to numpy array immediately
                min_prices = current_prices * 0.7
                max_prices = current_prices * 1.5
                optimal_prices = np.clip(optimal_prices, min_prices, max_prices)
            else:
                logger.warning("Current 'price' column not found in data for price bounding.")
                # If current_prices not available, use a generic bounding or skip
                optimal_prices = np.clip(optimal_prices, 0.5 * np.mean(optimal_prices) if len(optimal_prices) > 0 else 10, 
                                                       1.5 * np.mean(optimal_prices) if len(optimal_prices) > 0 else 500)
                current_prices = optimal_prices # For price_changes calculation

            # Ensure optimal_prices and current_prices are compatible for calculation
            if not isinstance(current_prices, np.ndarray):
                current_prices = np.array(current_prices)
            if not isinstance(optimal_prices, np.ndarray):
                optimal_prices = np.array(optimal_prices)
            
            # Avoid division by zero in price_changes
            price_changes_percent = np.where(current_prices != 0, 
                                             ((optimal_prices - current_prices) / current_prices) * 100, 
                                             0)

            # Ensure expected_revenue_lift calculation is safe
            expected_revenue_lift = np.mean(price_changes_percent) if len(price_changes_percent) > 0 else 0

            return {
                'status': 'success',
                'prices': optimal_prices.tolist(),
                'scenario': demand_scenario,
                'price_changes': price_changes_percent.tolist(),
                'expected_revenue_lift': expected_revenue_lift
            }
            
        except Exception as e:
            logger.error(f"Error predicting optimal price: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def save_model(self, path: str = 'models/saved_models/dynamic_pricing_model.pkl'):
        """Save the trained model."""
        if self.is_trained:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'is_trained': self.is_trained
            }
            joblib.dump(model_data, path)
            logger.info(f"Pricing model saved to {path}")
    
    def load_model(self, path: str = 'models/saved_models/dynamic_pricing_model.pkl'):
        """Load a trained model."""
        try:
            model_data = joblib.load(path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.is_trained = model_data['is_trained']
            logger.info(f"Pricing model loaded from {path}")
            return True
        except Exception as e:
            logger.warning(f"Could not load pricing model from {path}: {e}")
            return False

class ChurnPredictionModel:
    """Advanced customer churn prediction with reasoning capabilities."""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        # self.target_encoder = TargetEncoder() # Not directly used in prepare_features currently
        self.feature_columns = []
        self.is_trained = False
        self.feature_importance = {}
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare comprehensive features for churn prediction."""
        features = data.copy()
        
        # Debug: Log what columns we have
        logger.info(f"Churn model received data with columns: {list(features.columns)}")
        
        # Ensure required columns are present - handle missing category gracefully
        required_cols = ['timestamp', 'transaction_id', 'amount', 'product_id', 'user_id']
        for col in required_cols:
            if col not in features.columns:
                if col == 'timestamp':
                    features[col] = datetime.now() # Use current time as fallback
                elif col == 'amount':
                    features[col] = 0.0
                elif col == 'user_id':
                    features[col] = 'unknown_user'
                elif col == 'product_id':
                    features[col] = 'unknown_product'
                else:
                    features[col] = 'unknown' # Placeholder for string columns

        # Add category as a placeholder if not present (since it's not in transaction schema)
        if 'category' not in features.columns:
            features['category'] = 'unknown_category'  # Placeholder for missing category
            logger.info("Added placeholder 'category' column since it wasn't present in the data")

        # Ensure 'timestamp' is datetime type
        features['timestamp'] = pd.to_datetime(features['timestamp'], errors='coerce')
        features.dropna(subset=['timestamp'], inplace=True) # Drop rows where timestamp couldn't be parsed

        if features.empty:
            logger.warning("Features DataFrame is empty after timestamp processing.")
            return pd.DataFrame() # Return empty if no valid timestamps

        # Recency, Frequency, Monetary (RFM) features
        # Calculate current_date based on max timestamp in the actual data to avoid future dates
        current_date = features['timestamp'].max()
        if pd.isna(current_date): # Handle case where max() is NaN if all timestamps were NaT
            current_date = datetime.now()

        customer_metrics = features.groupby('user_id').agg(
            recency_days=('timestamp', lambda x: (current_date - pd.to_datetime(x).max()).days),  # Recency
            frequency=('transaction_id', 'count'),  # Frequency
            total_spent=('amount', 'sum'),  # Monetary Sum
            avg_order_value=('amount', 'mean'),  # Monetary Mean
            spending_volatility=('amount', 'std')  # Monetary Std
        ).reset_index()
        
        customer_metrics['spending_volatility'] = customer_metrics['spending_volatility'].fillna(0)
        
        # Behavioral features - handle missing category gracefully  
        logger.info(f"Preparing behavioral features, columns available: {list(features.columns)}")
        behavior_features = features.groupby('user_id').agg({
            'product_id': lambda x: x.nunique(),  # Product diversity
            'timestamp': lambda x: (pd.to_datetime(x).max() - pd.to_datetime(x).min()).days  # Customer lifetime
        }).reset_index()
        
        # Rename columns
        behavior_features.columns = ['user_id', 'product_diversity', 'customer_lifetime_days']
        
        # Add category diversity if category column has meaningful data
        has_category = 'category' in features.columns
        category_unique_count = features['category'].nunique() if has_category else 0
        has_meaningful_categories = has_category and category_unique_count > 1 and not features['category'].str.contains('unknown').all()
        
        logger.info(f"Checking category column: exists={has_category}, unique_values={category_unique_count}, meaningful={has_meaningful_categories}")
        
        if has_meaningful_categories:
            logger.info("Adding category diversity from actual category data")
            category_diversity = features.groupby('user_id')['category'].nunique().reset_index()
            category_diversity.columns = ['user_id', 'category_diversity']
            behavior_features = behavior_features.merge(category_diversity, on='user_id', how='left')
        else:
            logger.info("Using default category diversity (1) due to missing or uniform category data")
            behavior_features['category_diversity'] = 1  # Default to 1 category per user
        
        behavior_features['customer_lifetime_days'] = behavior_features['customer_lifetime_days'].fillna(0)

        # Merge features
        customer_features = customer_metrics.merge(behavior_features, on='user_id', how='left')
        
        # Derived features
        customer_features['avg_days_between_purchases'] = (
            customer_features['customer_lifetime_days'] / 
            customer_features['frequency'].clip(lower=1)
        ).fillna(0) # Fill NaN for users with 0 frequency
        
        customer_features['monetary_trend'] = (
            customer_features['total_spent'] / 
            customer_features['customer_lifetime_days'].clip(lower=1)
        ).fillna(0) # Fill NaN for 0 lifetime days
        
        customer_features['engagement_score'] = (
            customer_features['frequency'] * customer_features['category_diversity'] * customer_features['avg_order_value']
        ).fillna(0)
        
        # Risk indicators
        customer_features['high_recency_risk'] = (customer_features['recency_days'] > 30).astype(int)
        customer_features['low_frequency_risk'] = (customer_features['frequency'] < 3).astype(int)
        
        # Ensure median calculation is safe if avg_order_value is empty
        if not customer_features['avg_order_value'].empty:
            avg_order_value_median = customer_features['avg_order_value'].median()
            customer_features['declining_value_risk'] = (
                customer_features['avg_order_value'] < avg_order_value_median
            ).astype(int)
        else:
            customer_features['declining_value_risk'] = 0 # No risk if no data
        
        return customer_features
    
    def train(self, data: pd.DataFrame, churn_col: str = 'churned') -> Dict:
        """Train the churn prediction model."""
        try:
            logger.info("Training churn prediction model...")
            
            # Prepare features
            features = self.prepare_features(data)
            
            if features.empty:
                return {'status': 'error', 'message': 'Prepared features DataFrame is empty. Cannot train.'}

            # Create synthetic churn labels if not provided
            if churn_col not in features.columns:
                # Create realistic churn labels using BEHAVIORAL patterns, not temporal recency patterns
                # to avoid data leakage with recency_days feature
                
                # Use behavioral indicators that are independent of recency calculation
                # Handle missing 'category' column gracefully
                agg_dict = {
                    'amount': ['sum', 'mean', 'std', 'count'],
                    'product_id': 'nunique'
                }
                
                # Only add category aggregation if the column exists
                if 'category' in data.columns:
                    agg_dict['category'] = 'nunique'
                    user_behavior = data.groupby('user_id').agg(agg_dict).reset_index()
                    # Flatten column names
                    user_behavior.columns = ['user_id', 'total_spent', 'avg_amount', 'amount_std', 'transaction_count', 'category_count', 'product_count']
                    logger.info(f"Churn model using actual category data: {data['category'].nunique()} unique categories")
                else:
                    user_behavior = data.groupby('user_id').agg(agg_dict).reset_index()
                    # Flatten column names
                    user_behavior.columns = ['user_id', 'total_spent', 'avg_amount', 'amount_std', 'transaction_count', 'product_count']
                    # Set default category count to 1 (assuming each user has 1 category)
                    user_behavior['category_count'] = 1
                    logger.info("Churn model using default category count (1) - 'category' column not found in transaction data")
                user_behavior['amount_std'] = user_behavior['amount_std'].fillna(0)
                
                # Create churn labels based on SPENDING BEHAVIOR patterns (not time-based)
                # These are independent of the recency_days feature calculation
                
                # Calculate behavioral percentiles for realistic thresholds
                spending_p25 = user_behavior['total_spent'].quantile(0.25)
                freq_p25 = user_behavior['transaction_count'].quantile(0.25)
                diversity_p25 = user_behavior['category_count'].quantile(0.25)
                
                # Define churn using behavioral patterns (not temporal)
                churn_conditions = (
                    # Low value customers with low engagement
                    ((user_behavior['total_spent'] < spending_p25) & 
                     (user_behavior['transaction_count'] <= 2)) |
                    
                    # Low diversity customers with single category/product only
                    ((user_behavior['category_count'] == 1) & 
                     (user_behavior['product_count'] == 1) & 
                     (user_behavior['transaction_count'] <= 3)) |
                     
                    # Very low frequency customers regardless of spend
                    (user_behavior['transaction_count'] == 1) |
                    
                    # High variance in spending (inconsistent behavior)
                    ((user_behavior['amount_std'] > user_behavior['avg_amount']) & 
                     (user_behavior['transaction_count'] <= 3))
                )
                
                # Add structured randomness based on customer characteristics
                np.random.seed(42)  # For reproducibility
                
                # Create risk scores based on multiple factors
                user_behavior['risk_score'] = (
                    (user_behavior['total_spent'] < spending_p25).astype(int) * 0.3 +
                    (user_behavior['transaction_count'] <= freq_p25).astype(int) * 0.4 +
                    (user_behavior['category_count'] <= diversity_p25).astype(int) * 0.3
                )
                
                # Convert risk score to churn probability
                churn_prob = user_behavior['risk_score'] * 0.6 + np.random.normal(0, 0.1, len(user_behavior))
                churn_prob = np.clip(churn_prob, 0, 1)  # Ensure probabilities are between 0 and 1
                
                # Apply threshold with some randomness
                churn_threshold = np.random.normal(0.4, 0.1, len(user_behavior))
                churn_threshold = np.clip(churn_threshold, 0.2, 0.7)  # Reasonable threshold range
                
                # Combine rule-based and probabilistic factors
                user_behavior['churned'] = (
                    churn_conditions.astype(int) | 
                    (churn_prob > churn_threshold).astype(int)
                ).astype(int)
                
                # Ensure reasonable churn rate (between 15-35%)
                churn_rate = user_behavior['churned'].mean()
                if churn_rate < 0.15:  # Too low churn rate
                    # Increase churn for medium-risk customers
                    medium_risk = (user_behavior['risk_score'] > 0.3) & (user_behavior['risk_score'] < 0.6)
                    eligible_for_churn = user_behavior[medium_risk & (user_behavior['churned'] == 0)]
                    
                    if len(eligible_for_churn) > 0:  # Check if there are any eligible customers
                        sample_size = min(int(0.2 * len(user_behavior)), len(eligible_for_churn))
                        if sample_size > 0:
                            additional_churn_indices = eligible_for_churn.sample(
                                n=sample_size, random_state=42
                            ).index
                            user_behavior.loc[additional_churn_indices, 'churned'] = 1
                            logger.info(f"Increased churn for {sample_size} customers to improve balance")
                        else:
                            logger.info("No additional customers to mark as churned")
                    else:
                        logger.info("No eligible customers found to increase churn rate")
                        
                elif churn_rate > 0.35:  # Too high churn rate
                    # Reduce churn for higher-value customers
                    high_value = user_behavior['total_spent'] > user_behavior['total_spent'].quantile(0.6)
                    eligible_for_retention = user_behavior[high_value & (user_behavior['churned'] == 1)]
                    
                    if len(eligible_for_retention) > 0:  # Check if there are any eligible customers
                        sample_size = min(int(0.15 * len(user_behavior)), len(eligible_for_retention))
                        if sample_size > 0:
                            reduce_churn_indices = eligible_for_retention.sample(
                                n=sample_size, random_state=42
                            ).index
                            user_behavior.loc[reduce_churn_indices, 'churned'] = 0
                            logger.info(f"Reduced churn for {sample_size} customers to improve balance")
                        else:
                            logger.info("No customers to unmark as churned")
                    else:
                        logger.info("No eligible high-value customers found to reduce churn rate")
                
                # Merge churn labels with features
                features = features.merge(user_behavior[['user_id', 'churned']], on='user_id', how='left')
                features['churned'] = features['churned'].fillna(0).astype(int)  # Default to not churned if no match
                
                churn_col = 'churned'
                final_churn_rate = features['churned'].mean()
                logger.info(f"Created behavioral churn labels: {features['churned'].value_counts().to_dict()}, churn rate: {final_churn_rate:.3f}")
            
            # Select features
            exclude_cols = ['user_id', churn_col]
            self.feature_columns = [col for col in features.columns if col not in exclude_cols]
            
            X = features[self.feature_columns].fillna(0)
            y = features[churn_col]
            
            # Handle cases where X or y might be empty or have issues
            if X.empty or y.empty or len(X) != len(y):
                raise ValueError("Prepared data (X or y) is empty or mismatched for training.")
            
            # Check if there are enough samples and both classes are present
            if len(X) < 2 or len(np.unique(y)) < 2:
                # Fallback if not enough samples or only one class
                if len(X) >= 2:
                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                    logger.warning("Stratification skipped due to insufficient data or single class.")
                else:
                    raise ValueError("Insufficient data for training after feature preparation.")
            else:
                # Only use light SMOTE if class imbalance is severe (less than 10% minority class)
                class_counts = pd.Series(y).value_counts()
                minority_ratio = min(class_counts) / sum(class_counts)
                minority_count = min(class_counts)
                
                # Check if SMOTE is applicable and safe to use
                can_use_smote = (
                    minority_ratio < 0.1 and  # Severe imbalance
                    minority_count >= 6 and   # At least 6 minority samples (for k_neighbors=5)
                    len(X) >= 20              # Reasonable total sample size
                )
                
                if can_use_smote:
                    logger.info(f"Applying conservative SMOTE due to severe imbalance (minority class: {minority_ratio:.2%}, count: {minority_count})")
                    # Use very conservative SMOTE settings
                    k_neighbors = min(5, minority_count - 1)  # Ensure k_neighbors < minority_count
                    if k_neighbors >= 1:
                        smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
                        try:
                            X_balanced, y_balanced = smote.fit_resample(X, y)
                            logger.info(f"SMOTE applied successfully: {len(X)} -> {len(X_balanced)} samples")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"SMOTE failed with error: {e}")
                            logger.info("Proceeding without SMOTE balancing")
                            X_balanced, y_balanced = X, y
                    else:
                        logger.warning(f"Cannot apply SMOTE: insufficient minority samples ({minority_count})")
                        X_balanced, y_balanced = X, y
                else:
                    if minority_ratio >= 0.1:
                        logger.info(f"Skipping SMOTE - reasonable class balance (minority: {minority_ratio:.2%})")
                    else:
                        logger.warning(f"Skipping SMOTE - insufficient data (minority count: {minority_count}, total: {len(X)})")
                    X_balanced, y_balanced = X, y
                
                # Split data with stratification if we have enough samples
                try:
                    # Check if we have enough samples for stratified split
                    min_class_count = min(np.bincount(y_balanced))
                    if min_class_count >= 2:  # Need at least 2 samples per class for stratification
                        X_train, X_test, y_train, y_test = train_test_split(
                            X_balanced, y_balanced, test_size=0.3, random_state=42, stratify=y_balanced
                        )
                    else:
                        logger.warning(f"Insufficient samples for stratified split (min class: {min_class_count}), using random split")
                        X_train, X_test, y_train, y_test = train_test_split(
                            X_balanced, y_balanced, test_size=0.3, random_state=42
                        )
                except ValueError as e:
                    logger.warning(f"Stratified split failed: {e}, falling back to random split")
                    X_train, X_test, y_train, y_test = train_test_split(
                        X_balanced, y_balanced, test_size=0.3, random_state=42
                    )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model with better regularization to prevent overfitting
            self.model = GradientBoostingClassifier(
                n_estimators=50,  # Reduced from 100 to prevent overfitting
                learning_rate=0.05,  # Reduced learning rate
                max_depth=3,  # Reduced from 6 to prevent overfitting
                min_samples_split=10,  # Require more samples to split
                min_samples_leaf=5,   # Require more samples in leaf nodes
                subsample=0.8,        # Use only 80% of data for each tree
                random_state=42
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test_scaled)
            y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
            
            auc_score = roc_auc_score(y_test, y_pred_proba)
            classification_rep = classification_report(y_test, y_pred, output_dict=True)
            
            # Feature importance
            self.feature_importance = dict(zip(
                self.feature_columns, 
                self.model.feature_importances_
            ))
            
            self.is_trained = True
            # Model will be saved by ModelManager with correct path
            
            logger.info(f"Churn model trained - AUC: {auc_score:.4f}")
            
            return {
                'status': 'success',
                'auc_score': auc_score,
                'classification_report': classification_rep,
                'feature_importance': self.feature_importance,
                'churn_rate': y.mean()
            }
            
        except Exception as e:
            logger.error(f"Error training churn model: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def predict_churn_with_reasoning(self, data: pd.DataFrame) -> Dict:
        """Predict churn with detailed reasoning."""
        if not self.is_trained:
            return {'status': 'error', 'message': 'Model not trained'}
        
        try:
            # Assume data is already prepared features (RFM features)
            # If data contains raw transaction data, prepare features
            if 'recency_days' not in data.columns:
                features = self.prepare_features(data)
            else:
                features = data.copy()
            
            if features.empty:
                return {'status': 'error', 'message': 'No features generated for prediction.'}

            X = features[self.feature_columns].fillna(0)
            X_scaled = self.scaler.transform(X)
            
            # Check if model is trained and has predict_proba method
            if not self.model:
                return {'status': 'error', 'message': 'Model is not trained'}
            
            # Predictions
            if hasattr(self.model, 'predict_proba'):
                churn_probabilities = self.model.predict_proba(X_scaled)[:, 1]
            elif hasattr(self.model, 'predict'):
                # For models without predict_proba, use predict and normalize
                predictions = self.model.predict(X_scaled)
                churn_probabilities = np.clip(predictions, 0, 1)
            else:
                return {'status': 'error', 'message': 'Model does not support prediction'}
            
            churn_predictions = (churn_probabilities > 0.5).astype(int)
            
            # Risk segmentation
            risk_segments = []
            for prob in churn_probabilities:
                if prob >= 0.7:
                    risk_segments.append('High Risk')
                elif prob >= 0.4:
                    risk_segments.append('Medium Risk')
                else:
                    risk_segments.append('Low Risk')
            
            # Reasoning for each customer
            reasoning = []
            for i, (_, customer) in enumerate(features.iterrows()):
                reasons = []
                
                # Check if columns exist before accessing
                recency_days = customer.get('recency_days', 0)
                frequency = customer.get('frequency', 0)
                avg_days_between_purchases = customer.get('avg_days_between_purchases', 0)
                declining_value_risk = customer.get('declining_value_risk', 0)

                if recency_days > 45:
                    reasons.append(f"High recency: {recency_days} days since last purchase")
                if frequency < 3:
                    reasons.append(f"Low frequency: Only {frequency} purchases")
                if avg_days_between_purchases > 30:
                    reasons.append(f"Irregular purchasing: {avg_days_between_purchases:.1f} days between purchases")
                if declining_value_risk:
                    reasons.append("Below average order value")
                
                reasoning.append(reasons if reasons else ["Regular customer behavior"])
            
            return {
                'status': 'success',
                'predictions': {
                    'user_ids': features['user_id'].tolist(),
                    'churn_probabilities': churn_probabilities.tolist(),
                    'churn_predictions': churn_predictions.tolist(),
                    'risk_segments': risk_segments,
                    'reasoning': reasoning
                },
                'summary': {
                    'total_customers': len(features),
                    'high_risk_count': sum(1 for seg in risk_segments if seg == 'High Risk'),
                    'medium_risk_count': sum(1 for seg in risk_segments if seg == 'Medium Risk'),
                    'low_risk_count': sum(1 for seg in risk_segments if seg == 'Low Risk')
                }
            }
            
        except Exception as e:
            logger.error(f"Error predicting churn: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def save_model(self, path: str = 'models/saved_models/churn_model.pkl'):
        """Save the trained model."""
        if self.is_trained:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'feature_importance': self.feature_importance,
                'is_trained': self.is_trained
            }
            joblib.dump(model_data, path)
            logger.info(f"Churn model saved to {path}")
    
    def load_model(self, path: str = 'models/saved_models/churn_model.pkl'):
        """Load a trained model."""
        try:
            model_data = joblib.load(path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.feature_importance = model_data['feature_importance']
            self.is_trained = model_data['is_trained']
            logger.info(f"Churn model loaded from {path}")
            return True
        except Exception as e:
            logger.warning(f"Could not load churn model from {path}: {e}")
            return False
