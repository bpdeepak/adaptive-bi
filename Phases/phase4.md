# Phase 4: Advanced AI & Cognitive Reasoning Implementation

## Overview
This phase implements advanced AI features including dynamic pricing, customer churn prediction, explainable AI, knowledge graphs, and feedback mechanisms. All components are designed to integrate seamlessly with the existing backend and AI microservice from phases 1-3.

## File Structure
```
ai_service/
├── models/
│   ├── __init__.py
│   ├── advanced_models.py          # Dynamic pricing & churn prediction
│   ├── knowledge_graph.py          # Graph-based reasoning
│   └── explainable_ai.py          # SHAP/LIME integration
├── services/
│   ├── __init__.py
│   ├── pricing_service.py         # Dynamic pricing logic
│   ├── churn_service.py          # Churn prediction service
│   ├── reasoning_service.py       # Cognitive reasoning
│   └── feedback_service.py        # Model improvement feedback
├── utils/
│   ├── __init__.py
│   ├── feature_engineering.py     # Advanced feature processing
│   ├── model_utils.py            # Model management utilities
│   └── graph_utils.py            # Graph operations
├── api/
│   ├── __init__.py
│   └── advanced_endpoints.py      # New API endpoints
├── config/
│   ├── __init__.py
│   └── model_config.py           # Model configurations
└── requirements_phase4.txt        # Additional dependencies
```

## Implementation Files

### 1. Additional Dependencies (`requirements_phase4.txt`)
```txt
# Phase 4 Additional Dependencies
shap==0.42.1
lime==0.2.0.1
networkx==3.2.1
lightgbm==4.1.0
xgboost==1.7.6
plotly==5.17.0
kaleido==0.2.1
scikit-optimize==0.9.0
category_encoders==2.6.2
imbalanced-learn==0.11.0
optuna==3.4.0
redis==5.0.1
celery==5.3.4
scipy==1.11.4
mlflow==2.9.2
```

### 2. Advanced Models (`ai_service/models/advanced_models.py`)
```python
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
        
        # Time-based features
        features['hour'] = pd.to_datetime(features['timestamp']).dt.hour
        features['day_of_week'] = pd.to_datetime(features['timestamp']).dt.dayofweek
        features['month'] = pd.to_datetime(features['timestamp']).dt.month
        features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # Demand elasticity features
        features['demand_ratio'] = features['quantity'] / features['quantity'].rolling(window=7).mean()
        features['price_elasticity'] = (features['price'].pct_change() / 
                                      features['quantity'].pct_change()).fillna(0)
        
        # Market features
        features['market_share'] = features.groupby('product_id')['quantity'].transform(
            lambda x: x / x.sum()
        )
        features['competitive_index'] = features.groupby('category')['price'].transform(
            lambda x: (x - x.mean()) / x.std()
        ).fillna(0)
        
        # Inventory features
        features['inventory_turnover'] = features['quantity'] / features.get('stock_level', 100)
        features['stockout_risk'] = (features.get('stock_level', 100) < 
                                   features['quantity'].rolling(window=3).mean()).astype(int)
        
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
            best_model = min(scores, key=scores.get)
            self.model = trained_models[best_model]
            self.is_trained = True
            
            # Save model
            self.save_model()
            
            return {
                'status': 'success',
                'best_model': best_model,
                'mae': scores[best_model],
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
            X_scaled = self.scaler.transform(X)
            
            base_prices = self.model.predict(X_scaled)
            
            # Scenario adjustments
            scenario_multipliers = {
                'high_demand': 1.15,
                'normal': 1.0,
                'low_demand': 0.9,
                'clearance': 0.7
            }
            
            optimal_prices = base_prices * scenario_multipliers.get(demand_scenario, 1.0)
            
            # Price bounds (prevent extreme pricing)
            current_prices = data['price'].values
            min_prices = current_prices * 0.7
            max_prices = current_prices * 1.5
            
            optimal_prices = np.clip(optimal_prices, min_prices, max_prices)
            
            return {
                'status': 'success',
                'prices': optimal_prices.tolist(),
                'scenario': demand_scenario,
                'price_changes': ((optimal_prices - current_prices) / current_prices * 100).tolist(),
                'expected_revenue_lift': np.mean((optimal_prices - current_prices) / current_prices * 100)
            }
            
        except Exception as e:
            logger.error(f"Error predicting optimal price: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def save_model(self, path: str = 'models/dynamic_pricing_model.pkl'):
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
    
    def load_model(self, path: str = 'models/dynamic_pricing_model.pkl'):
        """Load a trained model."""
        try:
            model_data = joblib.load(path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.is_trained = model_data['is_trained']
            logger.info(f"Pricing model loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading pricing model: {str(e)}")

class ChurnPredictionModel:
    """Advanced customer churn prediction with reasoning capabilities."""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.target_encoder = TargetEncoder()
        self.feature_columns = []
        self.is_trained = False
        self.feature_importance = {}
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare comprehensive features for churn prediction."""
        features = data.copy()
        
        # Recency, Frequency, Monetary (RFM) features
        current_date = pd.to_datetime(features['timestamp']).max()
        customer_metrics = features.groupby('user_id').agg({
            'timestamp': lambda x: (current_date - pd.to_datetime(x).max()).days,  # Recency
            'transaction_id': 'count',  # Frequency
            'amount': ['sum', 'mean', 'std']  # Monetary
        }).reset_index()
        
        customer_metrics.columns = ['user_id', 'recency_days', 'frequency', 
                                  'total_spent', 'avg_order_value', 'spending_volatility']
        customer_metrics['spending_volatility'] = customer_metrics['spending_volatility'].fillna(0)
        
        # Behavioral features
        behavior_features = features.groupby('user_id').agg({
            'category': lambda x: x.nunique(),  # Category diversity
            'product_id': lambda x: x.nunique(),  # Product diversity
            'timestamp': lambda x: (pd.to_datetime(x).max() - pd.to_datetime(x).min()).days,  # Customer lifetime
        }).reset_index()
        
        behavior_features.columns = ['user_id', 'category_diversity', 
                                   'product_diversity', 'customer_lifetime_days']
        
        # Merge features
        customer_features = customer_metrics.merge(behavior_features, on='user_id')
        
        # Derived features
        customer_features['avg_days_between_purchases'] = (
            customer_features['customer_lifetime_days'] / 
            customer_features['frequency'].clip(lower=1)
        )
        customer_features['monetary_trend'] = (
            customer_features['total_spent'] / 
            customer_features['customer_lifetime_days'].clip(lower=1)
        )
        customer_features['engagement_score'] = (
            customer_features['frequency'] * customer_features['category_diversity'] * 
            customer_features['avg_order_value']
        )
        
        # Risk indicators
        customer_features['high_recency_risk'] = (customer_features['recency_days'] > 30).astype(int)
        customer_features['low_frequency_risk'] = (customer_features['frequency'] < 3).astype(int)
        customer_features['declining_value_risk'] = (
            customer_features['avg_order_value'] < customer_features['avg_order_value'].median()
        ).astype(int)
        
        return customer_features
    
    def train(self, data: pd.DataFrame, churn_col: str = 'churned') -> Dict:
        """Train the churn prediction model."""
        try:
            logger.info("Training churn prediction model...")
            
            # Prepare features
            features = self.prepare_features(data)
            
            # Create synthetic churn labels if not provided
            if churn_col not in features.columns:
                # Define churn based on recency and frequency
                features['churned'] = (
                    (features['recency_days'] > 60) | 
                    (features['frequency'] < 2) |
                    (features['avg_days_between_purchases'] > 45)
                ).astype(int)
                churn_col = 'churned'
            
            # Select features
            exclude_cols = ['user_id', churn_col]
            self.feature_columns = [col for col in features.columns if col not in exclude_cols]
            
            X = features[self.feature_columns].fillna(0)
            y = features[churn_col]
            
            # Handle class imbalance with SMOTE
            smote = SMOTE(random_state=42)
            X_balanced, y_balanced = smote.fit_resample(X, y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_balanced, y_balanced, test_size=0.2, random_state=42, stratify=y_balanced
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
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
            self.save_model()
            
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
            features = self.prepare_features(data)
            X = features[self.feature_columns].fillna(0)
            X_scaled = self.scaler.transform(X)
            
            # Predictions
            churn_probabilities = self.model.predict_proba(X_scaled)[:, 1]
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
                
                if customer['recency_days'] > 45:
                    reasons.append(f"High recency: {customer['recency_days']} days since last purchase")
                if customer['frequency'] < 3:
                    reasons.append(f"Low frequency: Only {customer['frequency']} purchases")
                if customer['avg_days_between_purchases'] > 30:
                    reasons.append(f"Irregular purchasing: {customer['avg_days_between_purchases']:.1f} days between purchases")
                if customer['declining_value_risk']:
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
    
    def save_model(self, path: str = 'models/churn_model.pkl'):
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
    
    def load_model(self, path: str = 'models/churn_model.pkl'):
        """Load a trained model."""
        try:
            model_data = joblib.load(path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.feature_importance = model_data['feature_importance']
            self.is_trained = model_data['is_trained']
            logger.info(f"Churn model loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading churn model: {str(e)}")
```

### 3. Knowledge Graph (`ai_service/models/knowledge_graph.py`)
```python
import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CustomerBehaviorGraph:
    """Knowledge graph for customer behavior analysis and reasoning."""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.node_attributes = {}
        self.edge_attributes = {}
        
    def build_graph_from_data(self, transactions: pd.DataFrame, 
                            products: pd.DataFrame = None, 
                            users: pd.DataFrame = None) -> Dict:
        """Build knowledge graph from transaction data."""
        try:
            logger.info("Building customer behavior knowledge graph...")
            
            # Add customer nodes
            customers = transactions['user_id'].unique()
            for customer_id in customers:
                customer_data = transactions[transactions['user_id'] == customer_id]
                
                # Customer attributes
                attrs = {
                    'type': 'customer',
                    'total_spent': customer_data['amount'].sum(),
                    'transaction_count': len(customer_data),
                    'avg_order_value': customer_data['amount'].mean(),
                    'first_purchase': customer_data['timestamp'].min(),
                    'last_purchase': customer_data['timestamp'].max(),
                    'favorite_category': customer_data['category'].mode().iloc[0] if not customer_data['category'].mode().empty else 'unknown',
                    'categories_purchased': customer_data['category'].nunique(),
                    'products_purchased': customer_data['product_id'].nunique()
                }
                
                self.graph.add_node(f"customer_{customer_id}", **attrs)
                self.node_attributes[f"customer_{customer_id}"] = attrs
            
            # Add product nodes
            products_list = transactions['product_id'].unique()
            for product_id in products_list:
                product_data = transactions[transactions['product_id'] == product_id]
                
                attrs = {
                    'type': 'product',
                    'category': product_data['category'].iloc[0],
                    'total_sales': product_data['amount'].sum(),
                    'units_sold': product_data['quantity'].sum(),
                    'avg_price': product_data['price'].mean(),
                    'unique_customers': product_data['user_id'].nunique(),
                    'popularity_score': len(product_data)
                }
                
                self.graph.add_node(f"product_{product_id}", **attrs)
                self.node_attributes[f"product_{product_id}"] = attrs
            
            # Add category nodes
            categories = transactions['category'].unique()
            for category in categories:
                category_data = transactions[transactions['category'] == category]
                
                attrs = {
                    'type': 'category',
                    'total_revenue': category_data['amount'].sum(),
                    'product_count': category_data['product_id'].nunique(),
                    'customer_count': category_data['user_id'].nunique(),
                    'avg_price': category_data['price'].mean()
                }
                
                self.graph.add_node(f"category_{category}", **attrs)
                self.node_attributes[f"category_{category}"] = attrs
            
            # Add relationships
            self._add_purchase_relationships(transactions)
            self._add_category_relationships(transactions)
            self._add_similarity_relationships(transactions)
            
            logger.info(f"Knowledge graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
            
            return {
                'status': 'success',
                'nodes': self.graph.number_of_nodes(),
                'edges': self.graph.number_of_edges(),
                'node_types': self._get_node_type_counts()
            }
            
        except Exception as e:
            logger.error(f"Error building knowledge graph: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _add_purchase_relationships(self, transactions: pd.DataFrame):
        """Add customer-product purchase relationships."""
        for _, transaction in transactions.iterrows():
            customer_node = f"customer_{transaction['user_id']}"
            product_node = f"product_{transaction['product_id']}"
            
            # Purchase relationship
            edge_attrs = {
                'type': 'purchased',
                'amount': transaction['amount'],
                'quantity': transaction['quantity'],
                'timestamp': transaction['timestamp'],
                'price': transaction['price']
            }
            
            self.graph.add_edge(customer_node, product_node, **edge_attrs)
    
    def _add_category_relationships(self, transactions: pd.DataFrame):
        """Add product-category relationships."""
        for _, transaction in transactions.iterrows():
            product_node = f"product_{transaction['product_id']}"
            category_node = f"category_{transaction['category']}"
            
            # Belongs to relationship
            if not self.graph.has_edge(product_node, category_node):
                self.graph.add_edge(product_node, category_node, type='belongs_to')
    
    def _add_similarity_relationships(self, transactions: pd.DataFrame):
        """Add customer similarity relationships based on purchase behavior."""
        # Customer-customer similarity based on shared products
        customer_products = transactions.groupby('user_id')['product_id'].apply(set).to_dict()
        
        customers = list(customer_products.keys())
        for i, customer1 in enumerate(customers):
            for customer2 in customers[i+1:]:
                products1 = customer_products[customer1]
                products2 = customer_products[customer2]
                
                # Jaccard similarity
                intersection = len(products1.intersection(products2))
                union = len(products1.union(products2))
                
                if union > 0:
                    similarity = intersection / union
                    
                    if similarity > 0.1:  # Threshold for similarity
                        self.graph.add_edge(
                            f"customer_{customer1}", 
                            f"customer_{customer2}",
                            type='similar_to',
                            similarity=similarity,
                            shared_products=intersection
                        )
    
    def get_customer_insights(self, customer_id: str) -> Dict:
        """Get comprehensive insights for a specific customer."""
        try:
            customer_node = f"customer_{customer_id}"
            
            if customer_node not in self.graph:
                return {'status': 'error', 'message': 'Customer not found'}
            
            # Basic customer info
            customer_attrs = self.node_attributes[customer_node]
            
            # Purchase patterns
            purchased_products = []
            for edge in self.graph.out_edges(customer_node, data=True):
                if edge[2]['type'] == 'purchased':
                    purchased_products.append({
                        'product_id': edge[1].replace('product_', ''),
                        'amount': edge[2]['amount'],
                        'timestamp': edge[2]['timestamp']
                    })
            
            # Similar customers
            similar_customers = []
            for edge in self.graph.out_edges(customer_node, data=True):
                if edge[2]['type'] == 'similar_to':
                    similar_customers.append({
                        'customer_id': edge[1].replace('customer_', ''),
                        'similarity': edge[2]['similarity']
                    })
            
            # Recommendations based on similar customers
            recommendations = self._get_recommendations(customer_id)
            
            return {
                'status': 'success',
                'customer_profile': customer_attrs,
                'purchase_history': purchased_products,
                'similar_customers': similar_customers,
                'recommendations': recommendations,
                'insights': self._generate_customer_insights(customer_attrs, purchased_products)
            }
            
        except Exception as e:
            logger.error(f"Error getting customer insights: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_recommendations(self, customer_id: str, top_n: int = 5) -> List[Dict]:
        """Generate product recommendations based on graph analysis."""
        customer_node = f"customer_{customer_id}"
        
        # Get products purchased by similar customers
        similar_customers = []
        for edge in self.graph.out_edges(customer_node, data=True):
            if edge[2]['type'] == 'similar_to':
                similar_customers.append((edge[1], edge[2]['similarity']))
        
        # Get products purchased by customer
        customer_products = set()
        for edge in self.graph.out_edges(customer_node, data=True):
            if edge[2]['type'] == 'purchased':
                customer_products.add(edge[1])
        
        # Score products based on similar customers' purchases
        product_scores = defaultdict(float)
        
        for similar_customer, similarity in similar_customers:
            for edge in self.graph.out_edges(similar_customer, data=True):
                if edge[2]['type'] == 'purchased' and edge[1] not in customer_products:
                    product_id = edge[1]
                    product_scores[product_id] += similarity * edge[2]['amount']
        
        # Sort and return top recommendations
        sorted_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for product_node, score in sorted_products[:top_n]:
            product_id = product_node.replace('product_', '')
            product_attrs = self.node_attributes.get(product_node, {})
            
            recommendations.append({
                'product_id': product_id,
                'recommendation_score': score,
                'category': product_attrs.get('category', 'unknown'),
                'avg_price': product_attrs.get('avg_price', 0),
                'popularity': product_attrs.get('popularity_score', 0)
            })
        
        return recommendations
    
    def _generate_customer_insights(self, customer_attrs: Dict, purchases: List[Dict]) -> List[str]:
        """Generate textual insights about customer behavior."""
        insights = []
        
        # Spending behavior
        if customer_attrs['avg_order_value'] > 100:
            insights.append("High-value customer with above-average order values")
        elif customer_attrs['avg_order_value'] < 50:
            insights.append("Price-sensitive customer with lower order values")
        
        # Purchase frequency
        if customer_attrs['transaction_count'] > 10:
            insights.append("Frequent buyer with strong engagement")
        elif customer_attrs['transaction_count'] < 3:
            insights.append("Infrequent buyer - potential churn risk")
        
        # Category diversity
        if customer_attrs['categories_purchased'] > 3:
            insights.append("Diverse shopper across multiple categories")
        else:
            insights.append(f"Focused shopper primarily in {customer_attrs['favorite_category']}")
        
        # Recency analysis
        try:
            last_purchase = pd.to_datetime(customer_attrs['last_purchase'])
            days_since_last = (datetime.now() - last_purchase).days
            
            if days_since_last < 7:
                insights.append("Recent active customer")
            elif days_since_last > 30:
                insights.append("At-risk customer - no recent purchases")
        except:
            pass
        
        return insights
    
    def _get_node_type_counts(self) -> Dict:
        """Get count of nodes by type."""
        type_counts = defaultdict(int)
        for node, attrs in self.node_attributes.items():
            type_counts[attrs['type']] += 1
        return dict(type_counts)
    
    def get_category_insights(self, category: str) -> Dict:
        """Get insights for a specific product category."""
        try:
            category_node = f"category_{category}"
            
            if category_node not in self.graph:
                return {'status': 'error', 'message': 'Category not found'}
            
            category_attrs = self.node_attributes[category_node]
            
            # Top products in category
            top_products = []
            for node, attrs in self.node_attributes.items():
                if attrs.get('type') == 'product' and attrs.get('category') == category:
                    top_products.append({
                        'product_id': node.replace('product_', ''),
                        'total_sales': attrs['total_sales'],
                        'popularity': attrs['popularity_score']
                    })
            
            top_products = sorted(top_products, key=lambda x: x['total_sales'], reverse=True)[:10]
            
            # Customer segments for this category
            customer_segments = self._analyze_category_customers(category)
            
            return {
                'status': 'success',
                'category_profile': category_attrs,
                'top_products': top_products,
                'customer_segments': customer_segments
            }
            
        except Exception as e:
            logger.error(f"Error getting category insights: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _analyze_category_customers(self, category: str) -> Dict:
        """Analyze customer segments for a category."""
        category_customers = []
        
        for node, attrs in self.node_attributes.items():
            if attrs.get('type') == 'customer' and attrs.get('favorite_category') == category:
                category_customers.append(attrs)
        
        if not category_customers:
            return {'total_customers': 0}
        
        total_spent = [c['total_spent'] for c in category_customers]
        transaction_counts = [c['transaction_count'] for c in category_customers]
        
        return {
            'total_customers': len(category_customers),
            'avg_customer_value': np.mean(total_spent),
            'avg_transactions_per_customer': np.mean(transaction_counts),
            'high_value_customers': sum(1 for x in total_spent if x > np.percentile(total_spent, 75)),
            'loyal_customers': sum(1 for x in transaction_counts if x > 5)
        }
    
    def export_graph(self, format: str = 'json') -> Dict:
        """Export graph in specified format."""
        try:
            if format == 'json':
                data = nx.node_link_data(self.graph)
                return {'status': 'success', 'data': data}
            elif format == 'gexf':
                # For Gephi visualization
                return {'status': 'success', 'message': 'Use nx.write_gexf() for file export'}
            else:
                return {'status': 'error', 'message': 'Unsupported format'}
                
        except Exception as e:
            logger.error(f"Error exporting graph: {str(e)}")
            return {'status': 'error', 'message': str(e)}


class ReasoningEngine:
    """Cognitive reasoning engine for business intelligence."""
    
    def __init__(self):
        self.knowledge_graph = CustomerBehaviorGraph()
        self.rules = self._load_business_rules()
    
    def _load_business_rules(self) -> Dict:
        """Load business rules for reasoning."""
        return {
            'churn_risk_rules': [
                {'condition': 'recency_days > 60', 'risk_level': 'high', 'reason': 'Long time since last purchase'},
                {'condition': 'frequency < 3', 'risk_level': 'medium', 'reason': 'Low purchase frequency'},
                {'condition': 'avg_order_value < 30', 'risk_level': 'low', 'reason': 'Low average order value'},
            ],
            'pricing_rules': [
                {'condition': 'demand_ratio > 1.5', 'action': 'increase_price', 'factor': 1.1},
                {'condition': 'inventory_turnover > 2', 'action': 'discount', 'factor': 0.9},
                {'condition': 'competitive_index < -1', 'action': 'premium_pricing', 'factor': 1.15},
            ],
            'recommendation_rules': [
                {'condition': 'customer_lifetime_value > 1000', 'strategy': 'premium_products'},
                {'condition': 'purchase_frequency > 10', 'strategy': 'loyalty_rewards'},
                {'condition': 'category_diversity > 3', 'strategy': 'cross_sell'},
            ]
        }
    
    def analyze_customer_journey(self, customer_id: str, transactions: pd.DataFrame) -> Dict:
        """Analyze and reason about customer journey."""
        try:
            customer_data = transactions[transactions['user_id'] == customer_id].copy()
            customer_data = customer_data.sort_values('timestamp')
            
            journey_stages = []
            current_stage = 'discovery'
            
            # Analyze transaction patterns
            for i, (_, transaction) in enumerate(customer_data.iterrows()):
                if i == 0:
                    stage = 'first_purchase'
                elif i < 3:
                    stage = 'exploration'
                elif customer_data[:i+1]['amount'].sum() > 500:
                    stage = 'loyal_customer'
                else:
                    stage = 'regular_customer'
                
                journey_stages.append({
                    'transaction_id': transaction['transaction_id'],
                    'stage': stage,
                    'timestamp': transaction['timestamp'],
                    'amount': transaction['amount'],
                    'category': transaction['category']
                })
            
            # Reasoning about journey
            insights = self._reason_about_journey(journey_stages, customer_data)
            
            # Predict next best action
            next_action = self._predict_next_action(customer_data)
            
            return {
                'status': 'success',
                'customer_id': customer_id,
                'journey_stages': journey_stages,
                'insights': insights,
                'next_action': next_action,
                'customer_summary': {
                    'total_spent': customer_data['amount'].sum(),
                    'transaction_count': len(customer_data),
                    'favorite_category': customer_data['category'].mode().iloc[0] if not customer_data['category'].mode().empty else 'unknown',
                    'customer_lifetime_days': (pd.to_datetime(customer_data['timestamp'].max()) - 
                                             pd.to_datetime(customer_data['timestamp'].min())).days
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing customer journey: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _reason_about_journey(self, journey_stages: List[Dict], customer_data: pd.DataFrame) -> List[str]:
        """Generate reasoning about customer journey."""
        insights = []
        
        # Journey progression analysis
        stages = [stage['stage'] for stage in journey_stages]
        
        if 'loyal_customer' in stages:
            insights.append("Customer has progressed to loyal status with high-value purchases")
        
        if len(set(stage['category'] for stage in journey_stages)) > 2:
            insights.append("Customer shows cross-category exploration behavior")
        
        # Purchase pattern analysis
        amounts = [stage['amount'] for stage in journey_stages]
        if len(amounts) > 1:
            trend = np.polyfit(range(len(amounts)), amounts, 1)[0]
            if trend > 0:
                insights.append("Increasing purchase value trend indicates growing engagement")
            elif trend < -5:
                insights.append("Declining purchase values may indicate disengagement risk")
        
        # Frequency analysis
        if len(journey_stages) > 5:
            timestamps = pd.to_datetime([stage['timestamp'] for stage in journey_stages])
            avg_days_between = np.mean(np.diff(timestamps).astype('timedelta64[D]').astype(int))
            
            if avg_days_between < 15:
                insights.append("High purchase frequency indicates strong engagement")
            elif avg_days_between > 45:
                insights.append("Low purchase frequency suggests potential churn risk")
        
        return insights
    
    def _predict_next_action(self, customer_data: pd.DataFrame) -> Dict:
        """Predict next best action for customer."""
        total_spent = customer_data['amount'].sum()
        transaction_count = len(customer_data)
        last_category = customer_data['category'].iloc[-1]
        
        # Rule-based next action prediction
        if total_spent > 1000 and transaction_count > 10:
            action = {
                'type': 'premium_offer',
                'description': 'Offer premium products or VIP status',
                'expected_impact': 'Increase customer lifetime value'
            }
        elif transaction_count < 3:
            action = {
                'type': 'onboarding_campaign',
                'description': 'Send targeted onboarding emails with product recommendations',
                'expected_impact': 'Increase engagement and repeat purchases'
            }
        else:
            action = {
                'type': 'cross_sell',
                'description': f'Recommend products from categories other than {last_category}',
                'expected_impact': 'Increase order value and category diversity'
            }
        
        return action
    
    def generate_business_insights(self, data: pd.DataFrame) -> Dict:
        """Generate comprehensive business insights using reasoning."""
        try:
            insights = {
                'revenue_insights': self._analyze_revenue_patterns(data),
                'customer_insights': self._analyze_customer_behavior(data),
                'product_insights': self._analyze_product_performance(data),
                'operational_insights': self._analyze_operational_metrics(data)
            }
            
            # Meta-insights (insights about insights)
            meta_insights = self._generate_meta_insights(insights)
            insights['meta_insights'] = meta_insights
            
            return {'status': 'success', 'insights': insights}
            
        except Exception as e:
            logger.error(f"Error generating business insights: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _analyze_revenue_patterns(self, data: pd.DataFrame) -> Dict:
        """Analyze revenue patterns with reasoning."""
        daily_revenue = data.groupby(data['timestamp'].dt.date)['amount'].sum()
        
        # Trend analysis
        x = np.arange(len(daily_revenue))
        trend = np.polyfit(x, daily_revenue.values, 1)[0]
        
        # Seasonality detection
        if len(daily_revenue) >= 7:
            weekly_pattern = data.groupby(data['timestamp'].dt.dayofweek)['amount'].mean()
            peak_day = weekly_pattern.idxmax()
            
        insights = {
            'total_revenue': data['amount'].sum(),
            'avg_daily_revenue': daily_revenue.mean(),
            'revenue_trend': 'increasing' if trend > 0 else 'decreasing',
            'trend_strength': abs(trend),
            'peak_day': peak_day if len(daily_revenue) >= 7 else None,
            'revenue_volatility': daily_revenue.std() / daily_revenue.mean() if daily_revenue.mean() > 0 else 0
        }
        
        return insights
    
    def _analyze_customer_behavior(self, data: pd.DataFrame) -> Dict:
        """Analyze customer behavior patterns."""
        customer_metrics = data.groupby('user_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'category': 'nunique',
            'timestamp': lambda x: (x.max() - x.min()).days
        }).round(2)
        
        customer_metrics.columns = ['total_spent', 'avg_order_value', 'frequency', 'categories', 'lifetime_days']
        
        insights = {
            'total_customers': len(customer_metrics),
            'avg_customer_value': customer_metrics['total_spent'].mean(),
            'avg_order_value': customer_metrics['avg_order_value'].mean(),
            'avg_purchase_frequency': customer_metrics['frequency'].mean(),
            'high_value_customers': len(customer_metrics[customer_metrics['total_spent'] > customer_metrics['total_spent'].quantile(0.8)]),
            'cross_category_shoppers': len(customer_metrics[customer_metrics['categories'] > 1]),
            'customer_retention_risk': len(customer_metrics[customer_metrics['frequency'] < 3])
        }
        
        return insights
    
    def _analyze_product_performance(self, data: pd.DataFrame) -> Dict:
        """Analyze product performance with reasoning."""
        product_metrics = data.groupby('product_id').agg({
            'amount': ['sum', 'mean'],
            'quantity': 'sum',
            'user_id': 'nunique'
        }).round(2)
        
        product_metrics.columns = ['total_revenue', 'avg_price', 'units_sold', 'unique_customers']
        
        # Category performance
        category_metrics = data.groupby('category').agg({
            'amount': 'sum',
            'product_id': 'nunique',
            'user_id': 'nunique'
        }).round(2)
        
        insights = {
            'total_products': len(product_metrics),
            'best_selling_product': product_metrics['total_revenue'].idxmax(),
            'most_popular_product': product_metrics['unique_customers'].idxmax(),
            'top_category': category_metrics['amount'].idxmax(),
            'category_diversity': len(category_metrics),
            'avg_products_per_category': len(product_metrics) / len(category_metrics),
            'underperforming_products': len(product_metrics[product_metrics['unique_customers'] < 2])
        }
        
        return insights
    
    def _analyze_operational_metrics(self, data: pd.DataFrame) -> Dict:
        """Analyze operational metrics."""
        # Time-based analysis
        hourly_sales = data.groupby(data['timestamp'].dt.hour)['amount'].sum()
        daily_sales = data.groupby(data['timestamp'].dt.dayofweek)['amount'].sum()
        
        insights = {
            'peak_hour': hourly_sales.idxmax(),
            'peak_day': daily_sales.idxmax(),
            'avg_transaction_value': data['amount'].mean(),
            'transaction_volume': len(data),
            'sales_concentration': (data['amount'].quantile(0.8) - data['amount'].quantile(0.2)) / data['amount'].mean()
        }
        
        return insights
    
    def _generate_meta_insights(self, insights: Dict) -> List[str]:
        """Generate high-level insights about the business."""
        meta_insights = []
        
        revenue = insights['revenue_insights']
        customers = insights['customer_insights']
        products = insights['product_insights']
        
        # Business health assessment
        if revenue['revenue_trend'] == 'increasing' and customers['avg_customer_value'] > 100:
            meta_insights.append("Business shows strong growth with increasing revenue and healthy customer values")
        
        # Customer portfolio analysis
        if customers['high_value_customers'] / customers['total_customers'] > 0.2:
            meta_insights.append("Strong high-value customer segment indicates good market positioning")
        
        # Product portfolio insights
        if products['category_diversity'] > 5:
            meta_insights.append("Diverse product portfolio reduces market risk")
        
        # Operational efficiency
        if customers['customer_retention_risk'] / customers['total_customers'] > 0.3:
            meta_insights.append("High customer retention risk requires immediate attention to engagement strategies")
        
        return meta_insights
```

### 4. Explainable AI (`ai_service/models/explainable_ai.py`)
```python
import numpy as np
import pandas as pd
import shap
import lime
import lime.tabular
from typing import Dict, List, Tuple, Optional, Any
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import joblib
import logging
from sklearn.base import BaseEstimator
import json
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

class ExplainableAI:
    """Explainable AI module using SHAP and LIME for model interpretability."""
    
    def __init__(self):
        self.shap_explainers = {}
        self.lime_explainers = {}
        self.feature_names = {}
        
    def setup_explainer(self, model: BaseEstimator, X_train: pd.DataFrame, 
                       model_name: str, explainer_type: str = 'both') -> Dict:
        """Setup SHAP and/or LIME explainers for a model."""
        try:
            logger.info(f"Setting up explainer for {model_name}")
            
            self.feature_names[model_name] = list(X_train.columns)
            
            if explainer_type in ['shap', 'both']:
                # Setup SHAP explainer
                if hasattr(model, 'predict_proba'):
                    # For classification models
                    self.shap_explainers[model_name] = shap.TreeExplainer(model)
                else:
                    # For regression models
                    self.shap_explainers[model_name] = shap.TreeExplainer(model)
            
            if explainer_type in ['lime', 'both']:
                # Setup LIME explainer
                mode = 'classification' if hasattr(model, 'predict_proba') else 'regression'
                self.lime_explainers[model_name] = lime.tabular.LimeTabularExplainer(
                    X_train.values,
                    feature_names=list(X_train.columns),
                    mode=mode,
                    discretize_continuous=True
                )
            
            return {
                'status': 'success',
                'model_name': model_name,
                'explainer_type': explainer_type,
                'feature_count': len(X_train.columns)
            }
            
        except Exception as e:
            logger.error(f"Error setting up explainer: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def explain_prediction_shap(self, model: BaseEstimator, X_instance: pd.DataFrame, 
                               model_name: str) -> Dict:
        """Generate SHAP explanations for a single prediction."""
        try:
            if model_name not in self.shap_explainers:
                return {'status': 'error', 'message': 'SHAP explainer not setup for this model'}
            
            explainer = self.shap_explainers[model_name]
            
            # Get SHAP values
            shap_values = explainer.shap_values(X_instance)
            
            # Handle multi-class output
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Use positive class for binary classification
            
            # Get feature contributions
            feature_contributions = []
            for i, feature in enumerate(self.feature_names[model_name]):
                contribution = float(shap_values[0][i]) if len(shap_values.shape) > 1 else float(shap_values[i])
                feature_contributions.append({
                    'feature': feature,
                    'value': float(X_instance.iloc[0][feature]),
                    'contribution': contribution,
                    'abs_contribution': abs(contribution)
                })
            
            # Sort by absolute contribution
            feature_contributions.sort(key=lambda x: x['abs_contribution'], reverse=True)
            
            # Get base value and prediction
            base_value = float(explainer.expected_value)
            if isinstance(explainer.expected_value, np.ndarray):
                base_value = float(explainer.expected_value[1])  # For binary classification
            
            prediction = model.predict(X_instance)[0]
            if hasattr(model, 'predict_proba'):
                prediction_proba = model.predict_proba(X_instance)[0]
            else:
                prediction_proba = None
            
            return {
                'status': 'success',
                'model_name': model_name,
                'prediction': float(prediction),
                'prediction_proba': prediction_proba.tolist() if prediction_proba is not None else None,
                'base_value': base_value,
                'feature_contributions': feature_contributions,
                'top_positive_features': [f for f in feature_contributions if f['contribution'] > 0][:5],
                'top_negative_features': [f for f in feature_contributions if f['contribution'] < 0][:5]
            }
            
        except Exception as e:
            logger.error(f"Error generating SHAP explanation: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def explain_prediction_lime(self, model: BaseEstimator, X_instance: pd.DataFrame, 
                               model_name: str, num_features: int = 10) -> Dict:
        """Generate LIME explanations for a single prediction."""
        try:
            if model_name not in self.lime_explainers:
                return {'status': 'error', 'message': 'LIME explainer not setup for this model'}
            
            explainer = self.lime_explainers[model_name]
            
            # Generate explanation
            if hasattr(model, 'predict_proba'):
                explanation = explainer.explain_instance(
                    X_instance.values[0], 
                    model.predict_proba, 
                    num_features=num_features
                )
            else:
                explanation = explainer.explain_instance(
                    X_instance.values[0], 
                    model.predict, 
                    num_features=num_features
                )
            
            # Extract feature contributions
            feature_contributions = []
            for feature_idx, contribution in explanation.as_list():
                feature_name = self.feature_names[model_name][feature_idx] if isinstance(feature_idx, int) else feature_idx
                feature_contributions.append({
                    'feature': feature_name,
                    'contribution': contribution,
                    'abs_contribution': abs(contribution)
                })
            
            # Get prediction
            prediction = model.predict(X_instance)[0]
            if hasattr(model, 'predict_proba'):
                prediction_proba = model.predict_proba(X_instance)[0]
            else:
                prediction_proba = None
            
            return {
                'status': 'success',
                'model_name': model_name,
                'prediction': float(prediction),
                'prediction_proba': prediction_proba.tolist() if prediction_proba is not None else None,
                'feature_contributions': feature_contributions,
                'explanation_score': explanation.score,
                'local_accuracy': explanation.local_exp
            }
            
        except Exception as e:
            logger.error(f"Error generating LIME explanation: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def generate_global_explanations(self, model: BaseEstimator, X_data: pd.DataFrame, 
                                   model_name: str, sample_size: int = 100) -> Dict:
        """Generate global model explanations using SHAP."""
        try:
            if model_name not in self.shap_explainers:
                return {'status': 'error', 'message': 'SHAP explainer not setup for this model'}
            
            # Sample data for efficiency
            if len(X_data) > sample_size:
                X_sample = X_data.sample(n=sample_size, random_state=42)
            else:
                X_sample = X_data
            
            explainer = self.shap_explainers[model_name]
            shap_values = explainer.shap_values(X_sample)
            
            # Handle multi-class output
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Use positive class for binary classification
            
            # Calculate feature importance
            feature_importance = np.abs(shap_values).mean(axis=0)
            
            # Create feature importance ranking
            feature_ranking = []
            for i, feature in enumerate(self.feature_names[model_name]):
                feature_ranking.append({
                    'feature': feature,
                    'importance': float(feature_importance[i]),
                    'mean_impact': float(np.mean(shap_values[:, i])),
                    'impact_std': float(np.std(shap_values[:, i]))
                })
            
            feature_ranking.sort(key=lambda x: x['importance'], reverse=True)
            
            # Generate summary statistics
            summary_stats = {
                'most_important_feature': feature_ranking[0]['feature'],
                'least_important_feature': feature_ranking[-1]['feature'],
                'total_features': len(feature_ranking),
                'top_5_features': [f['feature'] for f in feature_ranking[:5]],
                'feature_importance_distribution': {
                    'mean': float(np.mean(feature_importance)),
                    'std': float(np.std(feature_importance)),
                    'min': float(np.min(feature_importance)),
                    'max': float(np.max(feature_importance))
                }
            }
            
            return {
                'status': 'success',
                'model_name': model_name,
                'feature_ranking': feature_ranking,
                'summary_stats': summary_stats,
                'sample_size': len(X_sample)
            }
            
        except Exception as e:
            logger.error(f"Error generating global explanations: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def create_explanation_visualizations(self, explanation_data: Dict, 
                                        viz_type: str = 'feature_importance') -> Dict:
        """Create visualization for explanations."""
        try:
            if viz_type == 'feature_importance':
                return self._create_feature_importance_viz(explanation_data)
            elif viz_type == 'contribution_waterfall':
                return self._create_waterfall_viz(explanation_data)
            elif viz_type == 'feature_comparison':
                return self._create_feature_comparison_viz(explanation_data)
            else:
                return {'status': 'error', 'message': 'Unsupported visualization type'}
                
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _create_feature_importance_viz(self, explanation_data: Dict) -> Dict:
        """Create feature importance bar chart."""
        if 'feature_ranking' not in explanation_data:
            return {'status': 'error', 'message': 'No feature ranking data available'}
        
        features = [f['feature'] for f in explanation_data['feature_ranking'][:10]]
        importance = [f['importance'] for f in explanation_data['feature_ranking'][:10]]
        
        fig = go.Figure(data=[
            go.Bar(
                x=importance,
                y=features,
                orientation='h',
                marker_color='skyblue'
            )
        ])
        
        fig.update_layout(
            title='Top 10 Feature Importance',
            xaxis_title='Importance Score',
            yaxis_title='Features',
            height=500
        )
        
        return {
            'status': 'success',
            'chart_data': fig.to_dict(),
            'chart_type': 'feature_importance'
        }
    
    def _create_waterfall_viz(self, explanation_data: Dict) -> Dict:
        """Create waterfall chart for feature contributions."""
        if 'feature_contributions' not in explanation_data:
            return {'status': 'error', 'message': 'No feature contributions data available'}
        
        contributions = explanation_data['feature_contributions'][:8]  # Top 8 features
        
        features = [f['feature'] for f in contributions]
        values = [f['contribution'] for f in contributions]
        
        # Add base value and prediction
        x_labels = ['Base Value'] + features + ['Prediction']
        y_values = [explanation_data.get('base_value', 0)]
        
        cumulative = explanation_data.get('base_value', 0)
        for val in values:
            y_values.append(val)
            cumulative += val
        
        y_values.append(cumulative)
        
        colors = ['blue'] + ['green' if v > 0 else 'red' for v in values] + ['purple']
        
        fig = go.Figure(data=[
            go.Waterfall(
                name="Feature Contributions",
                orientation="v",
                measure=["absolute"] + ["relative"] * len(values) + ["total"],
                x=x_labels,
                textposition="outside",
                text=[f"{v:.3f}" for v in y_values],
                y=y_values,
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            )
        ])
        
        fig.update_layout(
            title="Feature Contribution Waterfall",
            showlegend=True,
            height=500
        )
        
        return {
            'status': 'success',
            'chart_data': fig.to_dict(),
            'chart_type': 'waterfall'
        }
    
    def _create_feature_comparison_viz(self, explanation_data: Dict) -> Dict:
        """Create feature comparison visualization."""
        if 'feature_contributions' not in explanation_data:
            return {'status': 'error', 'message': 'No feature contributions data available'}
        
        contributions = explanation_data['feature_contributions'][:10]
        
        features = [f['feature'] for f in contributions]
        values = [f['value'] for f in contributions]
        contributions_vals = [f['contribution'] for f in contributions]
        
        # Create subplot with feature values and contributions
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Feature Values', 'Feature Contributions'),
            horizontal_spacing=0.1
        )
        
        # Feature values
        fig.add_trace(
            go.Bar(x=features, y=values, name='Values', marker_color='lightblue'),
            row=1, col=1
        )
        
        # Feature contributions
        colors = ['green' if c > 0 else 'red' for c in contributions_vals]
        fig.add_trace(
            go.Bar(x=features, y=contributions_vals, name='Contributions', 
                  marker_color=colors),
            row=1, col=2
        )
        
        fig.update_layout(
            title='Feature Values vs Contributions',
            height=500,
            showlegend=False
        )
        
        fig.update_xaxes(tickangle=45)
        
        return {
            'status': 'success',
            'chart_data': fig.to_dict(),
            'chart_type': 'feature_comparison'
        }
    
    def batch_explain_predictions(self, model: BaseEstimator, X_batch: pd.DataFrame, 
                                 model_name: str, method: str = 'shap') -> Dict:
        """Generate explanations for a batch of predictions."""
        try:
            explanations = []
            
            for idx, row in X_batch.iterrows():
                X_instance = pd.DataFrame([row])
                
                if method == 'shap':
                    explanation = self.explain_prediction_shap(model, X_instance, model_name)
                elif method == 'lime':
                    explanation = self.explain_prediction_lime(model, X_instance, model_name)
                else:
                    return {'status': 'error', 'message': 'Unsupported explanation method'}
                
                if explanation['status'] == 'success':
                    explanation['instance_id'] = idx
                    explanations.append(explanation)
            
            return {
                'status': 'success',
                'explanations': explanations,
                'batch_size': len(explanations),
                'method': method
            }
            
        except Exception as e:
            logger.error(f"Error in batch explanation: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def save_explainer(self, model_name: str, filepath: str) -> Dict:
        """Save explainer configuration."""
        try:
            explainer_data = {
                'model_name': model_name,
                'feature_names': self.feature_names.get(model_name, []),
                'has_shap': model_name in self.shap_explainers,
                'has_lime': model_name in self.lime_explainers
            }
            
            with open(filepath, 'w') as f:
                json.dump(explainer_data, f, indent=2)
            
            return {'status': 'success', 'filepath': filepath}
            
        except Exception as e:
            logger.error(f"Error saving explainer: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def load_explainer(self, filepath: str) -> Dict:
        """Load explainer configuration."""
        try:
            with open(filepath, 'r') as f:
                explainer_data = json.load(f)
            
            model_name = explainer_data['model_name']
            self.feature_names[model_name] = explainer_data['feature_names']
            
            return {'status': 'success', 'model_name': model_name}
            
        except Exception as e:
            logger.error(f"Error loading explainer: {str(e)}")
            return {'status': 'error', 'message': str(e)}
```

### 5. Model Configurations (`ai_service/config/model_config.py`)
```python
"""
Model configuration settings for advanced AI features
"""
import os
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class ModelConfig:
    """Base configuration for ML models"""
    model_name: str
    model_type: str
    parameters: Dict[str, Any]
    feature_columns: List[str]
    target_column: str
    retrain_frequency: int  # hours
    performance_threshold: float

@dataclass
class PricingModelConfig(ModelConfig):
    """Configuration for dynamic pricing model"""
    price_bounds: Dict[str, float]
    elasticity_factors: Dict[str, float]
    competitor_weight: float
    demand_weight: float
    
@dataclass
class ChurnModelConfig(ModelConfig):
    """Configuration for churn prediction model"""
    risk_thresholds: Dict[str, float]
    intervention_triggers: List[str]
    feature_importance_threshold: float

# Model Configurations
PRICING_CONFIG = PricingModelConfig(
    model_name="dynamic_pricing_model",
    model_type="xgboost",
    parameters={
        "n_estimators": 100,
        "max_depth": 6,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42
    },
    feature_columns=[
        "base_price", "demand_score", "competitor_price", "inventory_level",
        "season_factor", "day_of_week", "hour_of_day", "customer_segment",
        "product_category", "promotion_active", "weather_factor"
    ],
    target_column="optimal_price",
    retrain_frequency=24,
    performance_threshold=0.85,
    price_bounds={"min_margin": 0.1, "max_markup": 2.0},
    elasticity_factors={"electronics": -1.2, "clothing": -0.8, "books": -0.5},
    competitor_weight=0.3,
    demand_weight=0.7
)

CHURN_CONFIG = ChurnModelConfig(
    model_name="churn_prediction_model",
    model_type="lightgbm",
    parameters={
        "objective": "binary",
        "metric": "auc",
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "verbose": 0
    },
    feature_columns=[
        "recency", "frequency", "monetary", "avg_order_value", "days_since_last_order",
        "total_orders", "total_spent", "avg_days_between_orders", "favorite_category",
        "support_tickets", "returns_count", "email_engagement", "app_usage_frequency"
    ],
    target_column="churned",
    retrain_frequency=168,  # Weekly
    performance_threshold=0.80,
    risk_thresholds={"high": 0.7, "medium": 0.4, "low": 0.2},
    intervention_triggers=["high_risk", "declining_engagement", "support_issues"],
    feature_importance_threshold=0.05
)

# Knowledge Graph Configuration
KNOWLEDGE_GRAPH_CONFIG = {
    "node_types": ["Customer", "Product", "Transaction", "Category", "Brand"],
    "relationship_types": [
        "PURCHASED", "VIEWED", "RATED", "RETURNED", "RECOMMENDED",
        "BELONGS_TO", "SIMILAR_TO", "FREQUENTLY_BOUGHT_TOGETHER"
    ],
    "embedding_dimensions": 128,
    "walk_length": 80,
    "num_walks": 10,
    "window_size": 5,
    "min_count": 1,
    "workers": 4
}

# Explainable AI Configuration
EXPLAINABLE_AI_CONFIG = {
    "shap_explainer_type": "tree",  # tree, linear, kernel
    "lime_num_features": 10,
    "lime_num_samples": 1000,
    "explanation_cache_ttl": 3600,  # seconds
    "visualization_formats": ["html", "json", "png"]
}

# Redis Configuration for Caching
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": int(os.getenv("REDIS_DB", 0)),
    "decode_responses": True,
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
    "retry_on_timeout": True
}

# Feedback System Configuration
FEEDBACK_CONFIG = {
    "min_feedback_samples": 100,
    "retrain_threshold": 0.05,  # Performance degradation threshold
    "feedback_weights": {
        "explicit": 1.0,  # Direct user feedback
        "implicit": 0.7,  # Behavioral feedback
        "system": 0.5     # System-generated feedback
    },
    "validation_split": 0.2,
    "test_split": 0.1
}
```

### 6. Feature Engineering (`ai_service/utils/feature_engineering.py`)
```python
"""
Advanced feature engineering utilities for Phase 4
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from category_encoders import TargetEncoder
import logging

logger = logging.getLogger(__name__)

class AdvancedFeatureEngineer:
    """Advanced feature engineering for AI models"""
    
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        self.feature_stats = {}
        
    def create_temporal_features(self, df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """Create temporal features from datetime column"""
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column])
        
        # Basic temporal features
        df['year'] = df[date_column].dt.year
        df['month'] = df[date_column].dt.month
        df['day'] = df[date_column].dt.day
        df['day_of_week'] = df[date_column].dt.dayofweek
        df['hour'] = df[date_column].dt.hour
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Cyclical encoding
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # Season encoding
        df['season'] = df['month'].apply(self._get_season)
        
        return df
    
    def create_rfm_features(self, transactions_df: pd.DataFrame, 
                          customer_col: str = 'customer_id',
                          date_col: str = 'transaction_date',
                          amount_col: str = 'amount') -> pd.DataFrame:
        """Create RFM (Recency, Frequency, Monetary) features"""
        current_date = transactions_df[date_col].max()
        
        rfm = transactions_df.groupby(customer_col).agg({
            date_col: lambda x: (current_date - x.max()).days,  # Recency
            amount_col: ['count', 'sum', 'mean']  # Frequency, Monetary
        }).reset_index()
        
        # Flatten column names
        rfm.columns = [customer_col, 'recency', 'frequency', 'monetary_total', 'monetary_avg']
        
        # RFM scores
        rfm['recency_score'] = pd.qcut(rfm['recency'], 5, labels=[5,4,3,2,1])
        rfm['frequency_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 5, labels=[1,2,3,4,5])
        rfm['monetary_score'] = pd.qcut(rfm['monetary_total'], 5, labels=[1,2,3,4,5])
        
        # Combined RFM score
        rfm['rfm_score'] = (rfm['recency_score'].astype(int) + 
                           rfm['frequency_score'].astype(int) + 
                           rfm['monetary_score'].astype(int))
        
        # Customer segments
        rfm['customer_segment'] = rfm['rfm_score'].apply(self._get_customer_segment)
        
        return rfm
    
    def create_behavioral_features(self, user_interactions: pd.DataFrame) -> pd.DataFrame:
        """Create behavioral features from user interactions"""
        features = []
        
        for user_id, group in user_interactions.groupby('user_id'):
            user_features = {
                'user_id': user_id,
                'total_sessions': len(group),
                'avg_session_duration': group['session_duration'].mean(),
                'total_page_views': group['page_views'].sum(),
                'bounce_rate': (group['page_views'] == 1).mean(),
                'avg_time_between_visits': self._calculate_avg_time_between_visits(group),
                'preferred_device': group['device_type'].mode().iloc[0] if not group['device_type'].mode().empty else 'unknown',
                'engagement_score': self._calculate_engagement_score(group)
            }
            features.append(user_features)
        
        return pd.DataFrame(features)
    
    def create_product_features(self, products_df: pd.DataFrame, 
                              transactions_df: pd.DataFrame) -> pd.DataFrame:
        """Create advanced product features"""
        # Basic product stats
        product_stats = transactions_df.groupby('product_id').agg({
            'amount': ['count', 'sum', 'mean', 'std'],
            'quantity': ['sum', 'mean'],
            'customer_id': 'nunique'
        }).reset_index()
        
        # Flatten columns
        product_stats.columns = ['product_id', 'total_orders', 'total_revenue', 
                               'avg_order_value', 'price_volatility', 'total_quantity',
                               'avg_quantity', 'unique_customers']
        
        # Merge with product info
        enhanced_products = products_df.merge(product_stats, on='product_id', how='left')
        
        # Fill missing values
        numeric_cols = ['total_orders', 'total_revenue', 'avg_order_value', 
                       'price_volatility', 'total_quantity', 'avg_quantity', 'unique_customers']
        enhanced_products[numeric_cols] = enhanced_products[numeric_cols].fillna(0)
        
        # Additional features
        enhanced_products['revenue_per_customer'] = (
            enhanced_products['total_revenue'] / enhanced_products['unique_customers']
        ).fillna(0)
        enhanced_products['reorder_rate'] = (
            enhanced_products['total_orders'] / enhanced_products['unique_customers']
        ).fillna(0)
        
        return enhanced_products
    
    def create_market_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create market and external features"""
        df = df.copy()
        
        # Seasonal factors
        df['holiday_factor'] = df.apply(self._get_holiday_factor, axis=1)
        df['weather_factor'] = np.random.normal(1.0, 0.1, len(df))  # Placeholder
        
        # Market conditions (simulated)
        df['market_sentiment'] = np.random.choice(['bullish', 'bearish', 'neutral'], len(df))
        df['competitor_activity'] = np.random.uniform(0.8, 1.2, len(df))
        
        return df
    
    def encode_categorical_features(self, df: pd.DataFrame, 
                                  categorical_cols: List[str],
                                  target_col: str = None,
                                  method: str = 'target') -> pd.DataFrame:
        """Encode categorical features using various methods"""
        df_encoded = df.copy()
        
        for col in categorical_cols:
            if col not in df_encoded.columns:
                continue
                
            if method == 'target' and target_col:
                if col not in self.encoders:
                    self.encoders[col] = TargetEncoder()
                    df_encoded[col] = self.encoders[col].fit_transform(df_encoded[col], df_encoded[target_col])
                else:
                    df_encoded[col] = self.encoders[col].transform(df_encoded[col])
            
            elif method == 'label':
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                    df_encoded[col] = self.encoders[col].fit_transform(df_encoded[col].astype(str))
                else:
                    df_encoded[col] = self.encoders[col].transform(df_encoded[col].astype(str))
        
        return df_encoded
    
    def scale_features(self, df: pd.DataFrame, 
                      feature_cols: List[str],
                      method: str = 'standard') -> pd.DataFrame:
        """Scale numerical features"""
        df_scaled = df.copy()
        
        for col in feature_cols:
            if col not in df_scaled.columns:
                continue
                
            if col not in self.scalers:
                if method == 'standard':
                    self.scalers[col] = StandardScaler()
                
                df_scaled[col] = self.scalers[col].fit_transform(df_scaled[[col]])
            else:
                df_scaled[col] = self.scalers[col].transform(df_scaled[[col]])
        
        return df_scaled
    
    def create_interaction_features(self, df: pd.DataFrame, 
                                  feature_pairs: List[Tuple[str, str]]) -> pd.DataFrame:
        """Create interaction features between specified feature pairs"""
        df_interaction = df.copy()
        
        for feat1, feat2 in feature_pairs:
            if feat1 in df_interaction.columns and feat2 in df_interaction.columns:
                # Multiplicative interaction
                df_interaction[f'{feat1}_x_{feat2}'] = df_interaction[feat1] * df_interaction[feat2]
                
                # Ratio interaction (avoid division by zero)
                df_interaction[f'{feat1}_div_{feat2}'] = (
                    df_interaction[feat1] / (df_interaction[feat2] + 1e-8)
                )
        
        return df_interaction
    
    def detect_anomalies(self, df: pd.DataFrame, 
                        feature_cols: List[str],
                        method: str = 'isolation_forest') -> pd.DataFrame:
        """Detect anomalies in the dataset"""
        from sklearn.ensemble import IsolationForest
        from sklearn.svm import OneClassSVM
        
        df_anomaly = df.copy()
        
        if method == 'isolation_forest':
            detector = IsolationForest(contamination=0.1, random_state=42)
        elif method == 'one_class_svm':
            detector = OneClassSVM(nu=0.1)
        
        # Fit and predict
        X = df_anomaly[feature_cols].fillna(0)
        anomaly_labels = detector.fit_predict(X)
        df_anomaly['is_anomaly'] = (anomaly_labels == -1).astype(int)
        
        return df_anomaly
    
    # Helper methods
    def _get_season(self, month: int) -> str:
        """Get season from month"""
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'
    
    def _get_customer_segment(self, rfm_score: int) -> str:
        """Get customer segment from RFM score"""
        if rfm_score >= 12:
            return 'champions'
        elif rfm_score >= 10:
            return 'loyal_customers'
        elif rfm_score >= 8:
            return 'potential_loyalists'
        elif rfm_score >= 6:
            return 'at_risk'
        else:
            return 'lost'
    
    def _calculate_avg_time_between_visits(self, group: pd.DataFrame) -> float:
        """Calculate average time between visits"""
        if len(group) <= 1:
            return 0
        
        group_sorted = group.sort_values('timestamp')
        time_diffs = group_sorted['timestamp'].diff().dt.total_seconds() / 3600  # hours
        return time_diffs.mean()
    
    def _calculate_engagement_score(self, group: pd.DataFrame) -> float:
        """Calculate user engagement score"""
        # Weighted combination of various engagement metrics
        session_score = min(group['session_duration'].mean() / 600, 1.0)  # Normalize to 10 minutes
        page_view_score = min(group['page_views'].mean() / 10, 1.0)  # Normalize to 10 pages
        frequency_score = min(len(group) / 30, 1.0)  # Normalize to 30 sessions
        
        return (session_score * 0.4 + page_view_score * 0.3 + frequency_score * 0.3)
    
    def _get_holiday_factor(self, row) -> float:
        """Get holiday factor for the date"""
        # Simplified holiday detection
        month, day = row.get('month', 1), row.get('day', 1)
        
        holidays = [
            (1, 1),   # New Year
            (12, 25), # Christmas
            (11, 24), # Thanksgiving (approximate)
            (7, 4),   # Independence Day
            (10, 31), # Halloween
        ]
        
        if (month, day) in holidays:
            return 1.5
        elif month == 12:  # Holiday season
            return 1.2
        else:
            return 1.0

# Utility functions
def create_lag_features(df: pd.DataFrame, 
                       value_col: str, 
                       group_col: str = None,
                       lags: List[int] = [1, 2, 3, 7, 14, 30]) -> pd.DataFrame:
    """Create lag features for time series data"""
    df_lag = df.copy()
    
    if group_col:
        for lag in lags:
            df_lag[f'{value_col}_lag_{lag}'] = df_lag.groupby(group_col)[value_col].shift(lag)
    else:
        for lag in lags:
            df_lag[f'{value_col}_lag_{lag}'] = df_lag[value_col].shift(lag)
    
    return df_lag

def create_rolling_features(df: pd.DataFrame,
                          value_col: str,
                          group_col: str = None,
                          windows: List[int] = [7, 14, 30]) -> pd.DataFrame:
    """Create rolling window features"""
    df_rolling = df.copy()
    
    if group_col:
        grouped = df_rolling.groupby(group_col)[value_col]
    else:
        grouped = df_rolling[value_col]
    
    for window in windows:
        df_rolling[f'{value_col}_rolling_mean_{window}'] = grouped.rolling(window=window).mean()
        df_rolling[f'{value_col}_rolling_std_{window}'] = grouped.rolling(window=window).std()
        df_rolling[f'{value_col}_rolling_min_{window}'] = grouped.rolling(window=window).min()
        df_rolling[f'{value_col}_rolling_max_{window}'] = grouped.rolling(window=window).max()
    
    return df_rolling
```

### 7. Model management utilities (`ai_service/utils/model_utils.py`)
```python
"""
Model management utilities
"""
import joblib
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import cross_val_score, GridSearchCV, RandomizedSearchCV
import mlflow
import mlflow.sklearn

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages ML model lifecycle including training, evaluation, and deployment"""
    
    def __init__(self, model_dir: str = "models", experiment_name: str = "adaptive_bi"):
        self.model_dir = model_dir
        self.experiment_name = experiment_name
        os.makedirs(model_dir, exist_ok=True)
        
        # Initialize MLflow
        mlflow.set_experiment(experiment_name)
    
    def save_model(self, model: Any, model_name: str, 
                   metadata: Dict[str, Any] = None) -> str:
        """Save model with metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(self.model_dir, f"{model_name}_{timestamp}.joblib")
        metadata_path = os.path.join(self.model_dir, f"{model_name}_{timestamp}_metadata.json")
        
        # Save model
        joblib.dump(model, model_path)
        
        # Save metadata
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "model_name": model_name,
            "timestamp": timestamp,
            "model_path": model_path,
            "model_type": str(type(model).__name__)
        })
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"Model saved: {model_path}")
        return model_path
    
    def load_model(self, model_name: str, version: str = "latest") -> Tuple[Any, Dict[str, Any]]:
        """Load model with metadata"""
        if version == "latest":
            # Find latest version
            model_files = [f for f in os.listdir(self.model_dir) 
                          if f.startswith(model_name) and f.endswith('.joblib')]
            if not model_files:
                raise FileNotFoundError(f"No models found for {model_name}")
            
            model_files.sort(reverse=True)
            model_file = model_files[0]
        else:
            model_file = f"{model_name}_{version}.joblib"
        
        model_path = os.path.join(self.model_dir, model_file)
        metadata_path = model_path.replace('.joblib', '_metadata.json')
        
        # Load model
        model = joblib.load(model_path)
        
        # Load metadata
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        logger.info(f"Model loaded: {model_path}")
        return model, metadata
    
    def evaluate_model(self, model: Any, X_test: pd.DataFrame, 
                      y_test: pd.Series, task_type: str = "classification") -> Dict[str, float]:
        """Evaluate model performance"""
        y_pred = model.predict(X_test)
        
        metrics = {}
        
        if task_type == "classification":
            metrics['accuracy'] = accuracy_score(y_test, y_pred)
            metrics['precision'] = precision_score(y_test, y_pred, average='weighted')
            metrics['recall'] = recall_score(y_test, y_pred, average='weighted')
            metrics['f1_score'] = f1_score(y_test, y_pred, average='weighted')
            
            # AUC for binary classification
            if len(np.unique(y_test)) == 2:
                y_pred_proba = model.predict_proba(X_test)[:, 1]
                metrics['auc'] = roc_auc_score(y_test, y_pred_proba)
        
        elif task_type == "regression":
            from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
            
            metrics['mse'] = mean_squared_error(y_test, y_pred)
            metrics['rmse'] = np.sqrt(metrics['mse'])
            metrics['mae'] = mean_absolute_error(y_test, y_pred)
            metrics['r2'] = r2_score(y_test, y_pred)
        
        return metrics
    
    def cross_validate_model(self, model: Any, X: pd.DataFrame, y: pd.Series,
                           cv: int = 5, scoring: str = 'accuracy') -> Dict[str, float]:
        """Perform cross-validation"""
        cv_scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)
        
        return {
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'cv_scores': cv_scores.tolist()
        }
    
    def hyperparameter_tuning(self, model: Any, param_grid: Dict[str, List],
                            X: pd.DataFrame, y: pd.Series,
                            method: str = "grid", cv: int = 5,
                            scoring: str = 'accuracy', n_iter: int = 100) -> Tuple[Any, Dict]:
        """Perform hyperparameter tuning"""
        
        if method == "grid":
            search = GridSearchCV(
                model, param_grid, cv=cv, scoring=scoring, 
                n_jobs=-1, verbose=1
            )
        elif method == "random":
            search = RandomizedSearchCV(
                model, param_grid, cv=cv, scoring=scoring,
                n_iter=n_iter, n_jobs=-1, verbose=1, random_state=42
            )
        else:
            raise ValueError("Method must be 'grid' or 'random'")
        
        search.fit(X, y)
        
        results = {
            'best_params': search.best_params_,
            'best_score': search.best_score_,
            'cv_results': search.cv_results_
        }
        
        return search.best_estimator_, results
    
    def model_drift_detection(self, reference_data: pd.DataFrame,
                            current_data: pd.DataFrame,
                            feature_cols: List[str],
                            threshold: float = 0.05) -> Dict[str, Any]:
        """Detect model drift using statistical tests"""
        from scipy import stats
        
        drift_results = {
            'drift_detected': False,
            'feature_drifts': {},
            'overall_drift_score': 0.0
        }
        
        drift_scores = []
        
        for feature in feature_cols:
            if feature in reference_data.columns and feature in current_data.columns:
                # Kolmogorov-Smirnov test
                ref_values = reference_data[feature].dropna()
                curr_values = current_data[feature].dropna()
                
                if len(ref_values) > 0 and len(curr_values) > 0:
                    ks_stat, p_value = stats.ks_2samp(ref_values, curr_values)
                    
                    drift_results['feature_drifts'][feature] = {
                        'ks_statistic': ks_stat,
                        'p_value': p_value,
                        'drift_detected': p_value < threshold
                    }
                    
                    drift_scores.append(ks_stat)
        
        if drift_scores:
            drift_results['overall_drift_score'] = np.mean(drift_scores)
            drift_results['drift_detected'] = drift_results['overall_drift_score'] > threshold
        
        return drift_results
    
    def feature_importance_analysis(self, model: Any, feature_names: List[str],
                                  top_k: int = 10) -> Dict[str, float]:
        """Analyze feature importance"""
        importance_dict = {}
        
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            importance_dict = dict(zip(feature_names, importances))
        elif hasattr(model, 'coef_'):
            # For linear models
            coefficients = np.abs(model.coef_)
            if coefficients.ndim > 1:
                coefficients = coefficients.flatten()
            importance_dict = dict(zip(feature_names, coefficients))
        
        # Sort by importance and return top k
        sorted_importance = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_importance[:top_k])
    
    def model_performance_monitoring(self, model_name: str, 
                                   current_metrics: Dict[str, float],
                                   historical_metrics: List[Dict[str, float]],
                                   threshold: float = 0.05) -> Dict[str, Any]:
        """Monitor model performance over time"""
        monitoring_results = {
            'performance_degradation': False,
            'degraded_metrics': [],
            'improvement_suggestions': []
        }
        
        if not historical_metrics:
            return monitoring_results
        
        # Calculate baseline (average of historical metrics)
        baseline_metrics = {}
        for metric in current_metrics.keys():
            historical_values = [m.get(metric, 0) for m in historical_metrics if metric in m]
            if historical_values:
                baseline_metrics[metric] = np.mean(historical_values)
        
        # Check for degradation
        for metric, current_value in current_metrics.items():
            if metric in baseline_metrics:
                baseline_value = baseline_metrics[metric]
                degradation = (baseline_value - current_value) / baseline_value
                
                if degradation > threshold:
                    monitoring_results['performance_degradation'] = True
                    monitoring_results['degraded_metrics'].append({
                        'metric': metric,
                        'current_value': current_value,
                        'baseline_value': baseline_value,
                        'degradation_percentage': degradation * 100
                    })
        
        # Generate improvement suggestions
        if monitoring_results['performance_degradation']:
            monitoring_results['improvement_suggestions'] = [
                "Consider retraining the model with recent data",
                "Check for data drift in input features",
                "Review feature engineering pipeline",
                "Evaluate hyperparameter tuning"
            ]
        
        return monitoring_results

class ModelVersioning:
    """Handle model versioning and deployment"""
    
    def __init__(self, model_registry_path: str = "model_registry"):
        self.registry_path = model_registry_path
        os.makedirs(model_registry_path, exist_ok=True)
        self.registry_file = os.path.join(model_registry_path, "model_registry.json")
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load model registry"""
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {"models": {}}
    
    def _save_registry(self):
        """Save model registry"""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2, default=str)
    
    def register_model(self, model_name: str, model_path: str, 
                      version: str, metrics: Dict[str, float],
                      metadata: Dict[str, Any] = None) -> bool:
        """Register a new model version"""
        if model_name not in self.registry["models"]:
            self.registry["models"][model_name] = {"versions": {}}
        
        version_info = {
            "version": version,
            "model_path": model_path,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat(),
            "status": "registered",
            "metadata": metadata or {}
        }
        
        self.registry["models"][model_name]["versions"][version] = version_info
        self._save_registry()
        
        logger.info(f"Model {model_name} version {version} registered")
        return True
    
    def promote_model(self, model_name: str, version: str, environment: str) -> bool:
        """Promote model to production environment"""
        if (model_name in self.registry["models"] and 
            version in self.registry["models"][model_name]["versions"]):
            
            # Update current production model
            if "production" not in self.registry["models"][model_name]:
                self.registry["models"][model_name]["production"] = {}
            
            self.registry["models"][model_name]["production"][environment] = {
                "version": version,
                "promoted_at": datetime.now().isoformat()
            }
            
            # Update version status
            self.registry["models"][model_name]["versions"][version]["status"] = f"deployed_{environment}"
            
            self._save_registry()
            logger.info(f"Model {model_name} version {version} promoted to {environment}")
            return True
        
        return False
    
    def get_production_model(self, model_name: str, environment: str = "production") -> Optional[Dict]:
        """Get current production model info"""
        if (model_name in self.registry["models"] and 
            "production" in self.registry["models"][model_name] and
            environment in self.registry["models"][model_name]["production"]):
            
            prod_info = self.registry["models"][model_name]["production"][environment]
            version = prod_info["version"]
            
            return self.registry["models"][model_name]["versions"][version]
        
        return None
    
    def list_model_versions(self, model_name: str) -> List[Dict]:
        """List all versions of a model"""
        if model_name in self.registry["models"]:
            return list(self.registry["models"][model_name]["versions"].values())
        return []
    
    def rollback_model(self, model_name: str, target_version: str, environment: str) -> bool:
        """Rollback to a previous model version"""
        if (model_name in self.registry["models"] and 
            target_version in self.registry["models"][model_name]["versions"]):
            
            return self.promote_model(model_name, target_version, environment)
        
        return False

# Utility functions for model management
def calculate_model_confidence(model: Any, X: pd.DataFrame, 
                             confidence_threshold: float = 0.8) -> Dict[str, Any]:
    """Calculate prediction confidence"""
    if hasattr(model, 'predict_proba'):
        probabilities = model.predict_proba(X)
        max_probs = np.max(probabilities, axis=1)
        
        high_confidence_mask = max_probs >= confidence_threshold
        
        return {
            'confidence_scores': max_probs.tolist(),
            'high_confidence_predictions': high_confidence_mask.sum(),
            'low_confidence_predictions': (~high_confidence_mask).sum(),
            'average_confidence': max_probs.mean(),
            'confidence_threshold': confidence_threshold
        }
    else:
        # For regression or models without probability
        predictions = model.predict(X)
        return {
            'predictions': predictions.tolist(),
            'note': 'Confidence scores not available for this model type'
        }

def ensemble_models(models: List[Any], X: pd.DataFrame, 
                   weights: Optional[List[float]] = None) -> np.ndarray:
    """Ensemble multiple models"""
    if weights is None:
        weights = [1.0] * len(models)
    
    predictions = []
    for model in models:
        pred = model.predict(X)
        predictions.append(pred)
    
    predictions = np.array(predictions)
    weighted_predictions = np.average(predictions, axis=0, weights=weights)
    
    return weighted_predictions
```


### 8. Graph operations and utilities for knowledge graph processing(`ai_service/utils/graph_utils.py`)
```python
"""
Graph operations and utilities for knowledge graph processing
"""
import networkx as nx
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class GraphAnalyzer:
    """Analyze and process knowledge graphs"""
    
    def __init__(self, graph: Optional[nx.Graph] = None):
        self.graph = graph or nx.Graph()
    
    def add_nodes_from_dataframe(self, df: pd.DataFrame, 
                                node_id_col: str,
                                node_type_col: str,
                                attribute_cols: List[str] = None) -> None:
        """Add nodes to graph from DataFrame"""
        for _, row in df.iterrows():
            node_id = row[node_id_col]
            node_type = row[node_type_col]
            
            # Prepare node attributes
            attributes = {'node_type': node_type}
            if attribute_cols:
                for col in attribute_cols:
                    if col in row:
                        attributes[col] = row[col]
            
            self.graph.add_node(node_id, **attributes)
    
    def add_edges_from_dataframe(self, df: pd.DataFrame,
                                source_col: str,
                                target_col: str,
                                relationship_col: str,
                                weight_col: str = None,
                                attribute_cols: List[str] = None) -> None:
        """Add edges to graph from DataFrame"""
        for _, row in df.iterrows():
            source = row[source_col]
            target = row[target_col]
            relationship = row[relationship_col]
            
            # Prepare edge attributes
            attributes = {'relationship': relationship}
            if weight_col and weight_col in row:
                attributes['weight'] = row[weight_col]
            
            if attribute_cols:
                for col in attribute_cols:
                    if col in row:
                        attributes[col] = row[col]
            
            self.graph.add_edge(source, target, **attributes)
    
    def calculate_centrality_measures(self, node_types: List[str] = None) -> Dict[str, Dict]:
        """Calculate various centrality measures"""
        centrality_measures = {}
        
        # Filter nodes by type if specified
        if node_types:
            nodes = [n for n, attr in self.graph.nodes(data=True) 
                    if attr.get('node_type') in node_types]
            subgraph = self.graph.subgraph(nodes)
        else:
            subgraph = self.graph
        
        # Degree centrality
        centrality_measures['degree'] = nx.degree_centrality(subgraph)
        
        # Betweenness centrality
        centrality_measures['betweenness'] = nx.betweenness_centrality(subgraph)
        
        # Closeness centrality
        centrality_measures['closeness'] = nx.closeness_centrality(subgraph)
        
        # PageRank
        centrality_measures['pagerank'] = nx.pagerank(subgraph)
        
        # Eigenvector centrality (if graph is connected)
        try:
            centrality_measures['eigenvector'] = nx.eigenvector_centrality(subgraph)
        except nx.NetworkXError:
            logger.warning("Could not calculate eigenvector centrality - graph may not be connected")
            centrality_measures['eigenvector'] = {}
        
        return centrality_measures
    
    def find_communities(self, method: str = "louvain") -> Dict[str, int]:
        """Find communities in the graph"""
        try:
            import community as community_louvain
        except ImportError:
            logger.error("python-louvain package required for community detection")
            return {}
        
        if method == "louvain":
            # Convert to undirected if needed
            if self.graph.is_directed():
                undirected_graph = self.graph.to_undirected()
            else:
                undirected_graph = self.graph
            
            partition = community_louvain.best_partition(undirected_graph)
            return partition
        
        return {}
    
    def calculate_similarity_scores(self, node1: str, node2: str,
                                  method: str = "jaccard") -> float:
        """Calculate similarity between two nodes"""
        if node1 not in self.graph or node2 not in self.graph:
            return 0.0
        
        neighbors1 = set(self.graph.neighbors(node1))
        neighbors2 = set(self.graph.neighbors(node2))
        
        if method == "jaccard":
            intersection = len(neighbors1 & neighbors2)
            union = len(neighbors1 | neighbors2)
            return intersection / union if union > 0 else 0.0
        
        elif method == "cosine":
            intersection = len(neighbors1 & neighbors2)
            return intersection / (np.sqrt(len(neighbors1)) * np.sqrt(len(neighbors2))) if len(neighbors1) > 0 and len(neighbors2) > 0 else 0.0
        
        elif method == "adamic_adar":
            common_neighbors = neighbors1 & neighbors2
            if not common_neighbors:
                return 0.0
            
            score = 0.0
            for neighbor in common_neighbors:
                neighbor_degree = self.graph.degree(neighbor)
                if neighbor_degree > 1:
                    score += 1.0 / np.log(neighbor_degree)
            
            return score
        
        return 0.0
    
    def recommend_connections(self, node: str, top_k: int = 10,
                            method: str = "jaccard") -> List[Tuple[str, float]]:
        """Recommend new connections for a node"""
        if node not in self.graph:
            return []
        
        current_neighbors = set(self.graph.neighbors(node))
        current_neighbors.add(node)  # Exclude self
        
        recommendations = []
        
        # Consider all other nodes
        for candidate in self.graph.nodes():
            if candidate not in current_neighbors:
                similarity = self.calculate_similarity_scores(node, candidate, method)
                if similarity > 0:
                    recommendations.append((candidate, similarity))
        
        # Sort by similarity and return top k
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:top_k]
    
    def find_shortest_paths(self, source: str, target: str = None,
                          relationship_types: List[str] = None) -> Dict[str, List]:
        """Find shortest paths between nodes"""
        if source not in self.graph:
            return {}
        
        # Filter edges by relationship type if specified
        if relationship_types:
            filtered_edges = [(u, v) for u, v, attr in self.graph.edges(data=True)
                            if attr.get('relationship') in relationship_types]
            subgraph = self.graph.edge_subgraph(filtered_edges)
        else:
            subgraph = self.graph
        
        if target:
            try:
                path = nx.shortest_path(subgraph, source, target)
                return {target: path}
            except nx.NetworkXNoPath:
                return {}
        else:
            # Find shortest paths to all reachable nodes
            try:
                paths = nx.single_source_shortest_path(subgraph, source)
                return paths
            except nx.NetworkXError:
                return {}
    
    def extract_subgraph(self, center_node: str, radius: int = 2,
                        node_types: List[str] = None,
                        relationship_types: List[str] = None) -> nx.Graph:
        """Extract subgraph around a center node"""
        if center_node not in self.graph:
            return nx.Graph()
        
        # Get nodes within radius
        nodes_in_radius = set()
        current_level = {center_node}
        
        for _ in range(radius + 1):
            nodes_in_radius.update(current_level)
            next_level = set()
            
            for node in current_level:
                neighbors = set(self.graph.neighbors(node))
                next_level.update(neighbors)
            
            current_level = next_level - nodes_in_radius
        
        # Filter by node types if specified
        if node_types:
            filtered_nodes = [n for n in nodes_in_radius 
                            if self.graph.nodes[n].get('node_type') in node_types]
            nodes_in_radius = set(filtered_nodes)
        
        # Create subgraph
        subgraph = self.graph.subgraph(nodes_in_radius).copy()
        
        # Filter edges by relationship type if specified
        if relationship_types:
            edges_to_remove = [(u, v) for u, v, attr in subgraph.edges(data=True)
                             if attr.get('relationship') not in relationship_types]
            subgraph.remove_edges_from(edges_to_remove)
        
        return subgraph
    
    def analyze_graph_structure(self) -> Dict[str, Any]:
        """Analyze overall graph structure"""
        analysis = {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'is_connected': nx.is_connected(self.graph) if not self.graph.is_directed() else nx.is_weakly_connected(self.graph),
        }
        
        # Node type distribution
        node_types = defaultdict(int)
        for _, attr in self.graph.nodes(data=True):
            node_type = attr.get('node_type', 'unknown')
            node_types[node_type] += 1
        analysis['node_type_distribution'] = dict(node_types)
        
        # Relationship type distribution
        relationship_types = defaultdict(int)
        for _, _, attr in self.graph.edges(data=True):
            relationship = attr.get('relationship', 'unknown')
            relationship_types[relationship] += 1
        analysis['relationship_type_distribution'] = dict(relationship_types)
        
        # Degree distribution
        degrees = [self.graph.degree(n) for n in self.graph.nodes()]
        if degrees:
            analysis['degree_statistics'] = {
                'mean': np.mean(degrees),
                'std': np.std(degrees),
                'min': min(degrees),
                'max': max(degrees)
            }
        
        return analysis
    
    def export_graph_data(self, format: str = "json") -> Any:
        """Export graph data in various formats"""
        if format == "json":
            return nx.node_link_data(self.graph)
        elif format == "gexf":
            return nx.write_gexf(self.graph, "graph.gexf")
        elif format == "graphml":
            return nx.write_graphml(self.graph, "graph.graphml")
        elif format == "edgelist":
            return nx.write_edgelist(self.graph, "graph.edgelist")
        else:
            raise ValueError(f"Unsupported format: {format}")

class GraphEmbedder:
    """Generate embeddings for graph nodes and edges"""
    
    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self.node_embeddings = {}
        self.edge_embeddings = {}
    
    def generate_node2vec_embeddings(self, dimensions: int = 128,
                                   walk_length: int = 80,
                                   num_walks: int = 10,
                                   window: int = 5,
                                   min_count: int = 1,
                                   batch_words: int = 4) -> Dict[str, np.ndarray]:
        """Generate Node2Vec embeddings"""
        try:
            from node2vec import Node2Vec
        except ImportError:
            logger.error("node2vec package required for Node2Vec embeddings")
            return {}
        
        # Create Node2Vec model
        node2vec = Node2Vec(
            self.graph,
            dimensions=dimensions,
            walk_length=walk_length,
            num_walks=num_walks,
            workers=4
        )
        
        # Fit model
        model = node2vec.fit(
            window=window,
            min_count=min_count,
            batch_words=batch_words
        )
        
        # Extract embeddings
        embeddings = {}
        for node in self.graph.nodes():
            try:
                embeddings[str(node)] = model.wv[str(node)]
            except KeyError:
                logger.warning(f"No embedding found for node: {node}")
        
        self.node_embeddings = embeddings
        return embeddings
    
    def generate_deepwalk_embeddings(self, dimensions: int = 128,
                                   walk_length: int = 40,
                                   num_walks: int = 80,
                                   window: int = 5) -> Dict[str, np.ndarray]:
        """Generate DeepWalk embeddings"""
        from gensim.models import Word2Vec
        
        # Generate random walks
        walks = self._generate_random_walks(walk_length, num_walks)
        
        # Train Word2Vec model
        model = Word2Vec(
            walks,
            vector_size=dimensions,
            window=window,
            min_count=1,
            sg=1,  # Skip-gram
            workers=4
        )
        
        # Extract embeddings
        embeddings = {}
        for node in self.graph.nodes():
            try:
                embeddings[str(node)] = model.wv[str(node)]
            except KeyError:
                logger.warning(f"No embedding found for node: {node}")
        
        self.node_embeddings = embeddings
        return embeddings
    
    def _generate_random_walks(self, walk_length: int, num_walks: int) -> List[List[str]]:
        """Generate random walks for DeepWalk"""
        walks = []
        nodes = list(self.graph.nodes())
        
        for _ in range(num_walks):
            np.random.shuffle(nodes)
            
            for node in nodes:
                walk = self._random_walk(node, walk_length)
                walks.append([str(n) for n in walk])
        
        return walks
    
    def _random_walk(self, start_node: str, walk_length: int) -> List[str]:
        """Generate a single random walk"""
        walk = [start_node]
        current_node = start_node
        
        for _ in range(walk_length - 1):
            neighbors = list(self.graph.neighbors(current_node))
            if not neighbors:
                break
            
            current_node = np.random.choice(neighbors)
            walk.append(current_node)
        
        return walk
    
    def calculate_node_similarity(self, node1: str, node2: str,
                                method: str = "cosine") -> float:
        """Calculate similarity between node embeddings"""
        if node1 not in self.node_embeddings or node2 not in self.node_embeddings:
            return 0.0
        
        emb1 = self.node_embeddings[node1]
        emb2 = self.node_embeddings[node2]
        
        if method == "cosine":
            return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        elif method == "euclidean":
            return 1.0 / (1.0 + np.linalg.norm(emb1 - emb2))
        elif method == "manhattan":
            return 1.0 / (1.0 + np.sum(np.abs(emb1 - emb2)))
        
        return 0.0

# Utility functions
def create_bipartite_graph(df: pd.DataFrame, 
                          left_col: str, right_col: str,
                          weight_col: str = None) -> nx.Graph:
    """Create bipartite graph from DataFrame"""
    G = nx.Graph()
    
    # Add nodes
    left_nodes = df[left_col].unique()
    right_nodes = df[right_col].unique()
    
    G.add_nodes_from(left_nodes, bipartite=0)
    G.add_nodes_from(right_nodes, bipartite=1)
    
    # Add edges
    for _, row in df.iterrows():
        left_node = row[left_col]
        right_node = row[right_col]
        
        edge_attrs = {}
        if weight_col and weight_col in row:
            edge_attrs['weight'] = row[weight_col]
        
        G.add_edge(left_node, right_node, **edge_attrs)
    
    return G

def project_bipartite_graph(G: nx.Graph, nodes: List[str]) -> nx.Graph:
    """Project bipartite graph to one set of nodes"""
    return nx.bipartite.projected_graph(G, nodes)

def calculate_graph_metrics(G: nx.Graph) -> Dict[str, float]:
    """Calculate common graph metrics"""
    metrics = {}
    
    # Basic metrics
    metrics['num_nodes'] = G.number_of_nodes()
    metrics['num_edges'] = G.number_of_edges()
    metrics['density'] = nx.density(G)
    
    # Connectivity
    if not G.is_directed():
        metrics['is_connected'] = nx.is_connected(G)
        if metrics['is_connected']:
            metrics['diameter'] = nx.diameter(G)
            metrics['radius'] = nx.radius(G)
    else:
        metrics['is_weakly_connected'] = nx.is_weakly_connected(G)
        metrics['is_strongly_connected'] = nx.is_strongly_connected(G)
    
    # Clustering
    try:
        metrics['avg_clustering'] = nx.average_clustering(G)
    except:
        metrics['avg_clustering'] = 0.0
    
    # Assortativity
    try:
        metrics['degree_assortativity'] = nx.degree_assortativity_coefficient(G)
    except:
        metrics['degree_assortativity'] = 0.0
    
    return metrics
```

### 9. Dynamic pricing service implementation(`ai_service/services/pricing_services.py`)
```python
"""
Dynamic pricing service implementation
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
import redis
import json

from ..models.advanced_models import DynamicPricingModel
from ..utils.feature_engineering import AdvancedFeatureEngineer
from ..config.model_config import PRICING_CONFIG, REDIS_CONFIG

logger = logging.getLogger(__name__)

@dataclass
class PricingRequest:
    """Pricing request data structure"""
    product_id: str
    base_price: float
    current_inventory: int
    competitor_prices: List[float]
    demand_indicators: Dict[str, float]
    customer_segment: str
    timestamp: datetime
    context: Dict[str, Any] = None

@dataclass
class PricingResponse:
    """Pricing response data structure"""
    product_id: str
    recommended_price: float
    price_change_percentage: float
    confidence_score: float
    reasoning: List[str]
    market_factors: Dict[str, float]
    risk_assessment: str
    timestamp: datetime

class DynamicPricingService:
    """Service for dynamic pricing recommendations"""
    
    def __init__(self):
        self.model = None
        self.feature_engineer = AdvancedFeatureEngineer()
        self.redis_client = self._initialize_redis()
        self.config = PRICING_CONFIG
        self.model_loaded = False
        
    def _initialize_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis client for caching"""
        try:
            client = redis.Redis(**REDIS_CONFIG)
            client.ping()
            return client
        except Exception as e:
            logger.warning(f"Failed to initialize Redis: {e}")
            return None
    
    def load_model(self, model_path: str = None) -> bool:
        """Load the pricing model"""
        try:
            if model_path:
                # Load specific model
                self.model = DynamicPricingModel.load_model(model_path)
            else:
                # Load default model
                self.model = DynamicPricingModel()
                # In production, this would load a pre-trained model
                
            self.model_loaded = True
            logger.info("Dynamic pricing model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load pricing model: {e}")
            return False
    
    def calculate_dynamic_price(self, request: PricingRequest) -> PricingResponse:
        """Calculate dynamic price for a product"""
        if not self.model_loaded:
            raise ValueError("Pricing model not loaded")
        
        # Check cache first
        cache_key = self._generate_cache_key(request)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result
        
        # Prepare features
        features = self._prepare_pricing_features(request)
        
        # Get model prediction
        predicted_price = self.model.predict(features)
        
        # Apply business constraints
        constrained_price = self._apply_pricing_constraints(
            predicted_price, request.base_price, request.product_id
        )
        
        # Calculate confidence and reasoning
        confidence_score = self._calculate_confidence(features, predicted_price)
        reasoning = self._generate_pricing_reasoning(request, features, constrained_price)
        market_factors = self._analyze_market_factors(features)
        risk_assessment = self._assess_pricing_risk(request, constrained_price)