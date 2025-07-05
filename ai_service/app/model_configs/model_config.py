"""
Model configuration settings for advanced AI features
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# Configuration constants
BASE_MODEL_DIR = os.getenv("BASE_MODEL_DIR", "/app/models/saved_models")
MIN_PRICING_DATA_POINTS = 1000
PRICING_RETRAIN_INTERVAL_DAYS = 7
PRICING_TRAINING_DAYS = 90
CHURN_BASELINE_RATE = 0.05
CHURN_RETRAIN_INTERVAL_DAYS = 14
MIN_KG_TRANSACTIONS = 500
KG_BUILD_INTERVAL_HOURS = 24

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
    
    # Class attributes for configuration constants
    BASE_MODEL_DIR: str = BASE_MODEL_DIR
    MIN_PRICING_DATA_POINTS: int = MIN_PRICING_DATA_POINTS
    PRICING_RETRAIN_INTERVAL_DAYS: int = PRICING_RETRAIN_INTERVAL_DAYS
    PRICING_TRAINING_DAYS: int = PRICING_TRAINING_DAYS
    CHURN_BASELINE_RATE: float = CHURN_BASELINE_RATE
    CHURN_RETRAIN_INTERVAL_DAYS: int = CHURN_RETRAIN_INTERVAL_DAYS
    MIN_KG_TRANSACTIONS: int = MIN_KG_TRANSACTIONS
    KG_BUILD_INTERVAL_HOURS: int = KG_BUILD_INTERVAL_HOURS

@dataclass
class PricingModelConfig(ModelConfig):
    """Configuration for dynamic pricing model"""
    price_bounds: Optional[Dict[str, float]] = None
    elasticity_factors: Optional[Dict[str, float]] = None
    competitor_weight: float = 0.3
    demand_weight: float = 0.7
    
@dataclass
class ChurnModelConfig(ModelConfig):
    """Configuration for churn prediction model"""
    risk_thresholds: Optional[Dict[str, float]] = None
    intervention_triggers: Optional[List[str]] = None
    feature_importance_threshold: float = 0.05

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

# Additional configuration constants
BASE_MODEL_DIR = os.getenv("BASE_MODEL_DIR", "/app/models/saved_models")
MIN_PRICING_DATA_POINTS = 1000
PRICING_RETRAIN_INTERVAL_DAYS = 7
PRICING_TRAINING_DAYS = 90
CHURN_BASELINE_RATE = 0.05
CHURN_RETRAIN_INTERVAL_DAYS = 14
MIN_KG_TRANSACTIONS = 500
KG_BUILD_INTERVAL_HOURS = 24

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
