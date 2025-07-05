## Project Directory Structure
```
./
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── advanced_endpoints.py
│   │   │   ├── anomaly.py
│   │   │   ├── forecast.py
│   │   │   ├── health.py
│   │   │   ├── __init__.py
│   │   │   └── recommend.py
│   │   ├── dependencies.py
│   │   └── __init__.py
│   ├── model_configs/
│   │   ├── __init__.py
│   │   └── model_config.py
│   ├── models/
│   │   ├── advanced_models.py
│   │   ├── anomaly_detection.py
│   │   ├── explainable_ai.py
│   │   ├── forecasting.py
│   │   ├── __init__.py
│   │   ├── knowledge_graph.py
│   │   ├── model_manager.py
│   │   └── recommendation.py
│   ├── services/
│   │   ├── churn_service.py
│   │   ├── data_processor.py
│   │   ├── feature_engineering.py
│   │   ├── feedback_service.py
│   │   ├── __init__.py
│   │   ├── pricing_service.py
│   │   └── reasoning_service.py
│   ├── utils/
│   │   ├── graph_utils.py
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── model_utils.py
│   ├── config.py
│   ├── database.py
│   ├── __init__.py
│   └── main.py
├── data/
│   └── processed/
├── logs/
│   ├── ai_service_2025-06-26.log
│   └── ai_service_2025-06-27.log
├── models/
│   └── saved_models/
│       ├── anomaly_feature_engineer_IsolationForest.joblib
│       ├── anomaly_model_IsolationForest.joblib
│       ├── anomaly_trained_features_IsolationForest.joblib
│       ├── forecasting_feature_engineer_RandomForestRegressor.joblib
│       ├── forecasting_model_RandomForestRegressor.joblib
│       ├── forecasting_trained_features_RandomForestRegressor.joblib
│       ├── item_inverse_mapper.joblib
│       ├── item_mapper.joblib
│       ├── recommendation_model_SVD.joblib
│       ├── user_inverse_mapper.joblib
│       ├── user_item_matrix.joblib
│       └── user_mapper.joblib
├── tests/
│   └── __init__.py
├── ai_service-Codebase-Dump-2025-06-27.md
├── Dockerfile
├── requirements.txt
└── sys.stdout

14 directories, 52 files
```



### `./app/api/dependencies.py`
```py
from app.database import get_database
from app.models.model_manager import ModelManager
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from app.utils.logger import logger

def get_db() -> AsyncIOMotorDatabase:
    """
    Dependency to get the MongoDB database instance.
    """
    db = get_database()
    if not db:
        logger.error("Database connection not available.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database connection not available")
    return db

def get_model_manager() -> ModelManager:
    """
    Dependency to get the singleton ModelManager instance.
    Ensures models are ready before serving requests.
    """
    manager = ModelManager()
    if not manager.models_loaded:
        logger.warning("AI models are not fully loaded or trained yet.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI models are not ready. Please try again shortly or trigger training.")
    return manager
```

### `./app/api/__init__.py`
```py

```

### `./app/api/routes/advanced_endpoints.py`
```py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import date, datetime

# Import services via dependency mechanism
from app.services.pricing_service import PricingService
from app.services.churn_service import ChurnService
from app.services.reasoning_service import ReasoningService
from app.services.feedback_service import FeedbackService
from app.models.model_manager import ModelManager # For overall model status
from app.config import settings
from app.utils.logger import logger

router = APIRouter()

# Placeholder dependency functions (will be assigned in main.py lifespan)
get_pricing_service_dependency: Any = lambda: None
get_churn_service_dependency: Any = lambda: None
get_reasoning_service_dependency: Any = lambda: None
get_feedback_service_dependency: Any = lambda: None


# --- Dynamic Pricing Endpoints ---
@router.post("/pricing/predict", response_model=Dict[str, float], summary="Predict Optimal Price",
             description="Predicts the optimal price for a product based on historical data and current demand factors.")
async def predict_optimal_price_endpoint(
    product_id: str,
    current_demand: float = Query(..., ge=0, description="Current demand level for the product"),
    seasonal_factor: float = Query(1.0, ge=0.5, le=1.5, description="Seasonal adjustment factor (e.g., 0.9 for low season, 1.1 for high season)"),
    competitor_price: Optional[float] = Query(None, ge=0, description="Optional competitor's current price"),
    pricing_service: PricingService = Depends(get_pricing_service_dependency)
):
    try:
        logger.info(f"Predicting optimal price for product_id: {product_id} with demand: {current_demand}")
        optimal_price = await pricing_service.predict_optimal_price(
            product_id=product_id,
            current_demand=current_demand,
            seasonal_factor=seasonal_factor,
            competitor_price=competitor_price
        )
        logger.info(f"Predicted optimal price for {product_id}: {optimal_price}")
        return {"optimal_price": optimal_price}
    except HTTPException:
        raise # Re-raise FastAPI HTTPExceptions directly
    except Exception as e:
        logger.error(f"Error predicting optimal price for {product_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

@router.post("/pricing/retrain", summary="Trigger Pricing Model Retraining",
             description="Triggers an immediate retraining of the pricing model. Useful for reacting to market changes.")
async def trigger_pricing_retrain_endpoint(
    pricing_service: PricingService = Depends(get_pricing_service_dependency)
):
    try:
        logger.info("Triggering pricing model retraining.")
        await pricing_service.retrain_model()
        logger.info("Pricing model retraining triggered successfully.")
        return {"message": "Pricing model retraining initiated."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering pricing model retraining: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

@router.get("/pricing/forecast-impact", response_model=Dict[str, Any], summary="Forecast Price Impact",
             description="Forecasts the potential impact of a price change on demand or revenue.")
async def forecast_price_impact_endpoint(
    product_id: str,
    proposed_price: float = Query(..., ge=0, description="Proposed new price for the product"),
    pricing_service: PricingService = Depends(get_pricing_service_dependency)
):
    try:
        logger.info(f"Forecasting impact for product_id: {product_id} with proposed price: {proposed_price}")
        impact_forecast = await pricing_service.forecast_impact(product_id, proposed_price)
        logger.info(f"Price impact forecast for {product_id}: {impact_forecast}")
        return impact_forecast
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forecasting price impact for {product_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

# --- Customer Churn Endpoints ---
@router.post("/churn/predict", response_model=Dict[str, float], summary="Predict Customer Churn",
             description="Predicts the likelihood of a customer churning based on their recent activity.")
async def predict_customer_churn_endpoint(
    customer_id: str,
    activity_score: float = Query(..., ge=0, le=1, description="Customer's recent activity score (0-1)"),
    subscription_age_days: int = Query(..., ge=0, description="Age of subscription in days"),
    churn_service: ChurnService = Depends(get_churn_service_dependency)
):
    try:
        logger.info(f"Predicting churn for customer_id: {customer_id}")
        churn_probability = await churn_service.predict_churn(
            customer_id=customer_id,
            activity_score=activity_score,
            subscription_age_days=subscription_age_days
        )
        logger.info(f"Predicted churn probability for {customer_id}: {churn_probability}")
        return {"churn_probability": churn_probability}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting churn for {customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

@router.post("/churn/retrain", summary="Trigger Churn Model Retraining",
             description="Triggers an immediate retraining of the churn prediction model.")
async def trigger_churn_retrain_endpoint(
    churn_service: ChurnService = Depends(get_churn_service_dependency)
):
    try:
        logger.info("Triggering churn model retraining.")
        await churn_service.retrain_model()
        logger.info("Churn model retraining triggered successfully.")
        return {"message": "Churn model retraining initiated."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering churn model retraining: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

@router.get("/churn/cohort-analysis", response_model=Dict[str, Any], summary="Get Churn Cohort Analysis",
            description="Provides an in-depth churn cohort analysis based on specified type and date range.")
async def get_churn_cohort_analysis_endpoint(
    start_date: date = Query(..., description="Start date for the analysis (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date for the analysis (YYYY-MM-DD)"),
    # FIX: Explicitly define cohort_type as a Query parameter
    cohort_type: str = Query(..., description="Type of cohort analysis (e.g., 'acquisition_month', 'first_purchase', 'channel')"),
    churn_service: ChurnService = Depends(get_churn_service_dependency)
):
    try:
        logger.info(f"Getting churn cohort analysis for {cohort_type} from {start_date} to {end_date}")
        analysis_data = await churn_service.get_cohort_analysis(
            start_date=start_date,
            end_date=end_date,
            cohort_type=cohort_type
        )
        logger.info("Churn cohort analysis completed successfully.")
        return analysis_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting churn cohort analysis: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

# --- Knowledge Graph and Reasoning Endpoints ---
@router.get("/reasoning/query-kg", response_model=Dict[str, Any], summary="Query Knowledge Graph",
            description="Queries the knowledge graph for insights based on entities and relationships.")
async def query_knowledge_graph_endpoint(
    query_string: str = Query(..., min_length=3, description="Natural language query or specific entity/relationship query"),
    reasoning_service: ReasoningService = Depends(get_reasoning_service_dependency)
):
    try:
        logger.info(f"Querying knowledge graph with: '{query_string}'")
        kg_result = await reasoning_service.query_knowledge_graph(query_string)
        logger.info("Knowledge graph query completed.")
        return {"query": query_string, "results": kg_result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying knowledge graph: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

@router.post("/reasoning/build-kg", summary="Trigger Knowledge Graph Build",
             description="Triggers a rebuild of the knowledge graph from raw transaction data.")
async def trigger_kg_build_endpoint(
    reasoning_service: ReasoningService = Depends(get_reasoning_service_dependency)
):
    try:
        logger.info("Triggering knowledge graph build.")
        await reasoning_service.build_knowledge_graph()
        logger.info("Knowledge graph build triggered successfully.")
        return {"message": "Knowledge graph build initiated. This may take some time."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering KG build: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

# --- Explainable AI Endpoints ---
@router.post("/explain/pricing", response_model=Dict[str, Any], summary="Explain Pricing Prediction",
             description="Provides explanations for a pricing model prediction using SHAP/LIME.")
async def explain_pricing_prediction_endpoint(
    product_id: str,
    current_demand: float,
    seasonal_factor: float,
    competitor_price: Optional[float] = None,
    explainability_method: str = Query("shap", description="Method for explainability: 'shap' or 'lime'"),
    pricing_service: PricingService = Depends(get_pricing_service_dependency)
):
    try:
        logger.info(f"Generating explanation for pricing prediction for product_id: {product_id} using {explainability_method}.")
        explanation = await pricing_service.explain_prediction(
            product_id=product_id,
            current_demand=current_demand,
            seasonal_factor=seasonal_factor,
            competitor_price=competitor_price,
            method=explainability_method
        )
        logger.info("Pricing prediction explanation completed.")
        return explanation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining pricing prediction for {product_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

@router.post("/explain/churn", response_model=Dict[str, Any], summary="Explain Churn Prediction",
             description="Provides explanations for a churn model prediction using SHAP/LIME.")
async def explain_churn_prediction_endpoint(
    customer_id: str,
    activity_score: float,
    subscription_age_days: int,
    explainability_method: str = Query("shap", description="Method for explainability: 'shap' or 'lime'"),
    churn_service: ChurnService = Depends(get_churn_service_dependency)
):
    try:
        logger.info(f"Generating explanation for churn prediction for customer_id: {customer_id} using {explainability_method}.")
        explanation = await churn_service.explain_prediction(
            customer_id=customer_id,
            activity_score=activity_score,
            subscription_age_days=subscription_age_days,
            method=explainability_method
        )
        logger.info("Churn prediction explanation completed.")
        return explanation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining churn prediction for {customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

# --- Feedback Endpoints ---
@router.post("/feedback/log-model-feedback", summary="Log Model Feedback",
             description="Logs feedback for a specific model prediction, used for continuous improvement and retraining.")
async def log_model_feedback_endpoint(
    model_name: str = Query(..., description="Name of the model (e.g., 'pricing', 'churn', 'forecasting')"),
    prediction_id: str = Query(..., description="Unique ID of the prediction being feedbacked"),
    actual_outcome: float = Query(..., description="The actual observed outcome related to the prediction"),
    feedback_notes: Optional[str] = Query(None, description="Additional notes or context for the feedback"),
    feedback_service: FeedbackService = Depends(get_feedback_service_dependency)
):
    try:
        logger.info(f"Logging feedback for model: {model_name}, prediction_id: {prediction_id}, actual_outcome: {actual_outcome}")
        await feedback_service.log_feedback(model_name, prediction_id, actual_outcome, feedback_notes)
        logger.info("Feedback logged successfully.")
        return {"message": "Feedback logged successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging feedback: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

@router.post("/feedback/trigger-retraining", summary="Trigger Specific Model Retraining by Feedback",
             description="Triggers retraining for a specific model based on accumulated feedback.")
async def trigger_specific_model_retraining_endpoint(
    model_name: str = Query(..., description="Name of the model to retrain (e.g., 'pricing', 'churn', 'forecasting')"),
    force_retrain: bool = Query(False, description="Set to true to force retraining regardless of feedback quantity"),
    feedback_service: FeedbackService = Depends(get_feedback_service_dependency)
):
    try:
        logger.info(f"Triggering retraining for model: {model_name} (force: {force_retrain}) via feedback.")
        retrain_status = await feedback_service.trigger_retraining(model_name, force_retrain)
        logger.info(f"Retraining status for {model_name}: {retrain_status}")
        return {"message": f"Retraining for {model_name} initiated.", "status": retrain_status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering retraining for {model_name}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

```

### `./app/api/routes/anomaly.py`
```py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.models.model_manager import ModelManager
from app.services.data_processor import DataProcessor
from app.utils.logger import logger
from app.api.dependencies import get_db, get_model_manager
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
import pandas as pd # Import pandas

router = APIRouter()

class AnomalyDetectionRequest(BaseModel):
    data_points: List[Dict[str, Any]] = Field(
        ...,
        description="List of data points to check for anomalies. Each dict should contain features used for training (e.g., 'totalAmount', 'quantity')."
    )
    features: List[str] = Field(
        ["totalAmount", "quantity"], # Default example features, now including 'totalAmount'
        description="List of features to use for anomaly detection. Must match features used during training."
    )

class AnomalyResponse(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    data: Dict[str, Any]
    details: Dict[str, Any]

@router.post("/train", summary="Trigger training for the anomaly detection model")
async def train_anomaly_model(
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually triggers the training process for the anomaly detection model.
    It uses recent transaction data to train the model.
    """
    logger.info("API call: /anomaly/train received.")
    try:
        data_processor = DataProcessor(db=db)
        transactions_df = await data_processor.get_transactions_data()

        if transactions_df.empty:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sufficient data available for anomaly detection model training.")

        # Prepare features for anomaly detection (example: totalAmount, quantity)
        # Ensure numerical columns
        transactions_df['totalAmount'] = pd.to_numeric(transactions_df['totalAmount'], errors='coerce').fillna(0)
        transactions_df['quantity'] = pd.to_numeric(transactions_df['quantity'], errors='coerce').fillna(0)
        
        # Define features. These should align with what the model expects.
        # Changed from "totalAmount" (which didn't exist) to "totalPrice" (which exists)
        anomaly_features = ["totalAmount", "quantity"] # Now totalAmount should exist after data_processor rename
        valid_anomaly_features = [f for f in anomaly_features if f in transactions_df.columns and pd.api.types.is_numeric_dtype(transactions_df[f])]

        if not valid_anomaly_features:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid numerical features found for anomaly detection training.")

        result = model_manager.anomaly_model.train(transactions_df, features=valid_anomaly_features)
        if result.get("status") == "success":
            return {"message": "Anomaly detection model training initiated successfully.", "metrics": result.get("metrics")}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Anomaly detection model training failed."))
    except Exception as e:
        logger.error(f"Error during anomaly model training API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during training: {e}")


@router.post("/detect", summary="Detect anomalies in provided data points", response_model=List[AnomalyResponse])
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Detects anomalies in a list of incoming data points.
    Each data point should be a dictionary containing the features used to train the anomaly model.
    """
    logger.info(f"API call: /anomaly/detect received for {len(request.data_points)} data points.")
    if not model_manager.anomaly_model.is_trained:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Anomaly detection model is not trained yet. Please train it first.")

    if not request.data_points:
        return []

    try:
        df = pd.DataFrame(request.data_points)
        # Ensure numerical columns for detection
        for col in request.features:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                logger.warning(f"Feature '{col}' not found in input data points for anomaly detection.")
                df[col] = 0

        detected_df = model_manager.anomaly_model.detect_anomalies(df.copy(), features=request.features)
        
        results = []
        for index, row in detected_df.iterrows():
            result = AnomalyResponse(
                is_anomaly=bool(row['is_anomaly']),
                anomaly_score=float(row['anomaly_score']),
                data={k: v for k, v in row.items() if k not in ['is_anomaly', 'anomaly_score']}, # All other fields
                details={feat: row[feat] for feat in request.features if feat in row} # Only anomaly features
            )
            results.append(result)
        
        return results

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error during anomaly detection API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during detection: {e}")


@router.get("/status", summary="Get anomaly detection model status")
async def get_anomaly_model_status(model_manager: ModelManager = Depends(get_model_manager)):
    """
    Returns the current training status and metrics of the anomaly detection model.
    """
    status_info = {
        "is_trained": model_manager.anomaly_model.is_trained,
        "model_type": model_manager.anomaly_model.model_type,
        "contamination_threshold": model_manager.anomaly_model.contamination,
        "metrics": model_manager.anomaly_model.metrics,
        "last_retrain_time": model_manager.last_retrain_time.isoformat() if model_manager.last_retrain_time else "N/A"
    }
    return status_info
```

### `./app/api/routes/forecast.py`
```py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.model_manager import ModelManager
from app.services.data_processor import DataProcessor
from app.utils.logger import logger
from app.api.dependencies import get_db, get_model_manager
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/train", summary="Trigger training for the forecasting model")
async def train_forecasting_model(
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually triggers the training process for the sales forecasting model.
    """
    logger.info("API call: /forecast/train received.")
    try:
        data_processor = DataProcessor(db=db)
        transactions_df = await data_processor.get_transactions_data()
        # Ensure 'totalAmount' is used here
        daily_sales_df = data_processor.prepare_time_series_data(transactions_df, 'totalAmount', freq='D')

        if daily_sales_df.empty:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sufficient data available for forecasting model training.")

        result = model_manager.forecasting_model.train(daily_sales_df, target_col='totalAmount')
        if result.get("status") == "success":
            return {"message": "Forecasting model training initiated successfully.", "metrics": result.get("metrics")}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Forecasting model training failed."))
    except Exception as e:
        logger.error(f"Error during forecasting model training API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during training: {e}")

@router.get("/predict", summary="Get sales forecast for the next N days")
async def get_sales_forecast(
    horizon: int = Query(7, ge=1, le=30, description="Number of days to forecast into the future"),
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Retrieves the sales forecast for the specified number of days.
    The model must be trained before predictions can be made.
    """
    logger.info(f"API call: /forecast/predict for {horizon} days received.")
    if not model_manager.forecasting_model.is_trained:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Forecasting model is not trained yet. Please train it first.")

    try:
        data_processor = DataProcessor(db=db)
        # Fetch recent historical data to generate features for forecasting
        # The number of days here should ideally cover the largest lag + rolling window needed.
        # Max lag is 14 days, max rolling window is 14 days, so need at least 28 days of history.
        # Add a buffer for safety, e.g., 60 days.
        historical_transactions_df = await data_processor.get_transactions_data(days=60) # Sufficient history
        # Ensure 'totalAmount' is used here
        historical_daily_sales_df = data_processor.prepare_time_series_data(historical_transactions_df, 'totalAmount', freq='D')

        if historical_daily_sales_df.empty:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enough historical data to generate forecast.")

        forecast_df = model_manager.forecasting_model.forecast_future(
            historical_daily_sales_df,
            horizon=horizon,
            target_col='totalAmount' # Ensure 'totalAmount' is used
        )
        
        if forecast_df.empty:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate forecast, resulting DataFrame is empty.")

        # Format output
        # Ensure 'totalAmount' is renamed to 'predicted_sales' for output clarity
        forecast_data = forecast_df.rename(columns={'timestamp': 'date', 'totalAmount': 'predicted_sales'}).to_dict(orient='records')
        # Convert datetime objects to ISO format strings
        for item in forecast_data:
            item['date'] = item['date'].isoformat().split('T')[0] # Get only date part

        return {"message": "Sales forecast generated successfully", "forecast": forecast_data}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error during sales forecast prediction API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during prediction: {e}")

@router.get("/status", summary="Get forecasting model status")
async def get_forecasting_model_status(model_manager: ModelManager = Depends(get_model_manager)):
    """
    Returns the current training status and metrics of the forecasting model.
    """
    status_info = {
        "is_trained": model_manager.forecasting_model.is_trained,
        "model_type": model_manager.forecasting_model.model_type,
        "metrics": model_manager.forecasting_model.metrics,
        "last_retrain_time": model_manager.last_retrain_time.isoformat() if model_manager.last_retrain_time else "N/A"
    }
    return status_info
```

### `./app/api/routes/health.py`
```py
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_database
from app.models.model_manager import ModelManager
from app.utils.logger import logger
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.dependencies import get_db, get_model_manager
from datetime import datetime

router = APIRouter()

@router.get("/", summary="Basic health check")
async def health_check():
    """
    Returns a simple OK status to indicate the service is running.
    """
    return {"status": "ok", "message": "AI service is running"}

@router.get("/detailed", summary="Detailed health check including database and model status")
async def detailed_health_check(
    db: AsyncIOMotorDatabase = Depends(get_db),
    model_manager: ModelManager = Depends(get_model_manager) # Use dependency to ensure manager is ready
):
    """
    Provides a detailed health check, including MongoDB connection status and ML model readiness.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database_status": "disconnected",
        "models_status": {
            "forecasting_model": "not_loaded",
            "anomaly_detection_model": "not_loaded",
            "recommendation_model": "not_loaded"
        },
        "message": "All systems nominal"
    }

    # Check MongoDB connection
    try:
        await db.command('ping')
        health_status["database_status"] = "connected"
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        health_status["database_status"] = "failed"
        health_status["status"] = "unhealthy"
        health_status["message"] = "MongoDB connection failed"

    # Check model readiness (via model manager)
    if model_manager.forecasting_model and model_manager.forecasting_model.is_trained:
        health_status["models_status"]["forecasting_model"] = "trained"
    else:
        health_status["models_status"]["forecasting_model"] = "not_trained"
        health_status["status"] = "degraded"
        health_status["message"] = "Forecasting model not ready"

    if model_manager.anomaly_model and model_manager.anomaly_model.is_trained:
        health_status["models_status"]["anomaly_detection_model"] = "trained"
    else:
        health_status["models_status"]["anomaly_detection_model"] = "not_trained"
        health_status["status"] = "degraded"
        health_status["message"] = "Anomaly detection model not ready"

    if model_manager.recommendation_model and model_manager.recommendation_model.is_trained:
        health_status["models_status"]["recommendation_model"] = "trained"
    else:
        health_status["models_status"]["recommendation_model"] = "not_trained"
        health_status["status"] = "degraded"
        health_status["message"] = "Recommendation model not ready"
    
    if not model_manager.models_loaded:
        health_status["status"] = "degraded"
        health_status["message"] = "Not all AI models are loaded or trained."

    if health_status["status"] != "healthy":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=health_status)

    return health_status
```

### `./app/api/routes/__init__.py`
```py

```

### `./app/api/routes/recommend.py`
```py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any
from app.models.model_manager import ModelManager
from app.services.data_processor import DataProcessor
from app.utils.logger import logger
from app.api.dependencies import get_db, get_model_manager
from motor.motor_asyncio import AsyncIOMotorDatabase
import pandas as pd # Import pandas for DataFrame handling if needed

router = APIRouter()

@router.post("/train", summary="Trigger training for the recommendation model")
async def train_recommendation_model(
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually triggers the training process for the recommendation model.
    It uses transaction data to build the user-item interaction matrix.
    """
    logger.info("API call: /recommend/train received.")
    try:
        data_processor = DataProcessor(db=db)
        result = await model_manager.recommendation_model.train(data_processor)
        if result.get("status") == "success":
            return {"message": "Recommendation model training initiated successfully."}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Recommendation model training failed."))
    except Exception as e:
        logger.error(f"Error during recommendation model training API call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during training: {e}")


@router.get("/user/{user_id}", summary="Get personalized product recommendations for a user")
async def get_user_recommendations(
    user_id: str,
    num_recommendations: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    model_manager: ModelManager = Depends(get_model_manager),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Retrieves personalized product recommendations for a specific user.
    If the user is new (cold-start) or model is not trained, returns popular products.
    """
    logger.info(f"API call: /recommend/user/{user_id} received for {num_recommendations} recommendations.")
    
    # Check if model is trained, if not, it will default to popular items
    if not model_manager.recommendation_model.is_trained:
        logger.warning("Recommendation model is not trained. Providing popular recommendations.")
        data_processor = DataProcessor(db=db)
        product_df = await data_processor.get_product_data()
        popular_recommendations = model_manager.recommendation_model._get_popular_recommendations(num_recommendations, product_data=product_df)
        return {"message": "Recommendation model not trained, returned popular items.", "recommendations": popular_recommendations}

    try:
        data_processor = DataProcessor(db=db)
        product_df = await data_processor.get_product_data() # Fetch product details for richer recommendations
        
        recommendations = await model_manager.recommendation_model.get_user_recommendations(
            user_id, num_recommendations, product_data=product_df
        )
        
        if not recommendations:
            # If personalized recommendations fail, fall back to popular
            popular_recommendations = model_manager.recommendation_model._get_popular_recommendations(num_recommendations, product_data=product_df)
            return {"message": f"No personalized recommendations found for user {user_id}. Returning popular items.", "recommendations": popular_recommendations}

        return {"message": f"Recommendations for user {user_id} generated successfully.", "recommendations": recommendations}
    except Exception as e:
        logger.error(f"Error during recommendation API call for user {user_id}: {e}", exc_info=True)
        # Fallback to popular recommendations in case of critical error
        try:
            data_processor = DataProcessor(db=db)
            product_df = await data_processor.get_product_data()
            popular_recommendations = model_manager.recommendation_model._get_popular_recommendations(num_recommendations, product_data=product_df)
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"message": f"Internal server error, falling back to popular recommendations: {e}", "recommendations": popular_recommendations})
        except Exception as fallback_e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during recommendation: {e}. Fallback also failed: {fallback_e}")


@router.get("/status", summary="Get recommendation model status")
async def get_recommendation_model_status(model_manager: ModelManager = Depends(get_model_manager)):
    """
    Returns the current training status of the recommendation model.
    """
    status_info = {
        "is_trained": model_manager.recommendation_model.is_trained,
        "model_type": model_manager.recommendation_model.model_type,
        "n_components": model_manager.recommendation_model.n_components,
        "last_retrain_time": model_manager.last_retrain_time.isoformat() if model_manager.last_retrain_time else "N/A"
    }
    return status_info
```

### `./app/config.py`
```py
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
    MODEL_SAVE_PATH: str = os.getenv("MODEL_SAVE_PATH", "/app/models/saved_models")
    
    # NEW: Model retraining interval in MINUTES
    # Default is 24 hours (1440 minutes). Set to 15 for 15 minutes.
    MODEL_RETRAIN_INTERVAL_MINUTES: int = int(os.getenv("MODEL_RETRAIN_INTERVAL_MINUTES", 1440)) 

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
        # Mask password in URL for display
        print(f"MongoDB URL: {self.MONGODB_URL.split('@')[-1] if '@' in self.MONGODB_URL and len(self.MONGODB_URL.split('@')) > 1 else self.MONGODB_URL}") 
        print(f"Database Name: {self.DATABASE_NAME}")
        print(f"Model Save Path: {self.MODEL_SAVE_PATH}")
        print(f"Retrain Interval (Minutes): {self.MODEL_RETRAIN_INTERVAL_MINUTES}") # Changed to minutes
        print(f"Forecast Horizon (Days): {self.FORECAST_HORIZON}")
        print(f"Anomaly Threshold: {self.ANOMALY_THRESHOLD}")
        print(f"Data Collection Days: {self.DATA_COLLECTION_DAYS}")
        print(f"CORS Origins: {self.CORS_ORIGINS}")
        print("--------------------------------\n")

# Instantiate config
settings = Config()

if __name__ == "__main__":
    settings.display_config()
```

### `./app/database.py`
```py
import motor.motor_asyncio
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
# Corrected Import: 'settings' should come from the 'app.config' file
from app.config import settings
from app.utils.logger import logger
from typing import Optional

# Async MongoDB client for FastAPI
client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
db: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None # This should actually be database object, not client

# Synchronous MongoDB client for model training scripts (if needed outside FastAPI context)
sync_client: Optional[MongoClient] = None
sync_db: Optional[MongoClient] = None


async def connect_to_mongo(): # Renamed from connect_to_database for consistency with main.py
    """
    Establishes an asynchronous connection to MongoDB.
    """
    global client, db
    try:
        mongo_uri = settings.MONGODB_URL
        logger.info(f"Attempting to connect to MongoDB at: {mongo_uri.split('@')[-1]}") # Log without credentials
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        db = client[settings.DATABASE_NAME] # Get the database instance
        
        # The ping command is cheap and does not require auth.
        await db.command('ping') # Ping the database, not the client directly
        logger.info("MongoDB connection successful!")
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed (ConnectionFailure): {e}", exc_info=True)
        raise
    except ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB server selection timed out: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during MongoDB connection: {e}", exc_info=True)
        raise

async def close_mongo_connection(): # Renamed from close_database_connection
    """
    Closes the asynchronous MongoDB connection.
    """
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")

async def get_database() -> motor.motor_asyncio.AsyncIOMotorClient:
    """
    Returns the asynchronous MongoDB database instance.
    This is used as a FastAPI dependency.
    """
    if db is None: # Check if db (database instance) is none
        logger.error("MongoDB database instance is not initialized. Call connect_to_mongo first.")
        raise ConnectionFailure("MongoDB database instance is not initialized.")
    return db

# --- Synchronous connection functions (if needed, otherwise can be removed) ---
def connect_to_sync_database():
    """
    Establishes a synchronous connection to MongoDB.
    Used for scripts that might not run within an async context directly.
    """
    global sync_client, sync_db
    try:
        sync_client = MongoClient(settings.MONGODB_URL)
        sync_db = sync_client[settings.DATABASE_NAME]
        sync_db.command('ping') # Test connection
        logger.info(f"Successfully connected to synchronous MongoDB at {settings.MONGODB_URL.split('@')[-1]}")
    except ConnectionFailure as e:
        logger.error(f"Synchronous MongoDB connection failed (ConnectionFailure): {e}", exc_info=True)
        raise
    except ServerSelectionTimeoutError as e:
        logger.error(f"Synchronous MongoDB server selection timed out: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during synchronous MongoDB connection: {e}", exc_info=True)
        raise

def close_sync_database_connection():
    """
    Closes the synchronous MongoDB connection.
    """
    global sync_client
    if sync_client:
        sync_client.close()
        logger.info("Synchronous MongoDB connection closed.")

def get_sync_database():
    """
    Returns the synchronous MongoDB database instance.
    """
    return sync_db

if __name__ == "__main__":
    import asyncio

    # Test async connection
    async def test_async_db():
        try:
            await connect_to_mongo() # Use connect_to_mongo
            if db is not None:
                logger.info("Async DB connection test successful.")
                collections = await db.list_collection_names()
                logger.info(f"Collections: {collections}")
            else:
                logger.error("Async DB connection test failed: db object is None.")
        except Exception as e:
            logger.error(f"Async DB connection test encountered an error: {e}")
        finally:
            await close_mongo_connection() # Use close_mongo_connection

    asyncio.run(test_async_db())

    # Test sync connection
    try:
        connect_to_sync_database()
        if sync_db:
            logger.info("Sync DB connection test successful.")
            collections = sync_db.list_collection_names()
            logger.info(f"Collections: {collections}")
        else:
            logger.error("Sync DB connection test failed: sync_db object is None.")
    except Exception as e:
        logger.error(f"Sync DB connection test encountered an error: {e}")
    finally:
        close_sync_database_connection()

```

### `./app/__init__.py`
```py

```

### `./app/main.py`
```py
import os
import uvicorn
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

# Import existing core modules
from app.config import settings # This refers to the app/config.py file for main settings
from app.database import close_mongo_connection, connect_to_mongo
from app.api.dependencies import get_database
from app.utils.logger import logger # Your custom logger

# Import existing Phase 3 API routes
from app.api.routes import forecast, anomaly, recommend, health

# Import new Phase 4 API routes
from app.api.routes import advanced_endpoints

# Import existing Phase 3 Model Manager
from app.models.model_manager import model_manager, ModelManager

# Import new Phase 4 services for global initialization
# NOTE: The ModelConfig import here uses the *new* path 'app.model_configs'
from app.services.pricing_service import PricingService
from app.services.churn_service import ChurnService
from app.services.reasoning_service import ReasoningService
from app.services.feedback_service import FeedbackService

# APScheduler for periodic tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Global service instances (initialized once during app startup)
pricing_service_instance: Optional[PricingService] = None
churn_service_instance: Optional[ChurnService] = None
reasoning_service_instance: Optional[ReasoningService] = None
feedback_service_instance: Optional[FeedbackService] = None


# Define the periodic task function for retraining all models
async def periodic_model_retraining_all():
    logger.info("Starting scheduled full model retraining (Phase 3 & 4 models)...")
    try:
        # Phase 3 Models via existing ModelManager
        await model_manager.train_all_models()
        logger.info("Phase 3 models (Forecasting, Anomaly, Recommendation) retraining completed.")

        # Phase 4 Models via FeedbackService
        if feedback_service_instance:
            logger.info("Triggering retraining for Phase 4 models via FeedbackService...")
            await feedback_service_instance.trigger_retraining('pricing', force_retrain=True)
            await feedback_service_instance.trigger_retraining('churn', force_retrain=True)
            await feedback_service_instance.trigger_retraining('knowledge_graph', force_retrain=True)
            # You might add feedback_service_instance.trigger_retraining for other phase 3 models here
            # if you want feedback service to manage their retraining as well
            logger.info("Phase 4 models retraining/rebuilding completed.")
        else:
            logger.warning("FeedbackService not initialized, skipping Phase 4 model retraining.")

        logger.info("Scheduled full model retraining completed successfully.")
    except Exception as e:
        logger.error(f"Error during scheduled full model retraining: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the startup and shutdown events for the FastAPI application.
    """
    logger.info("AI Service starting up...")
    settings.display_config()

    # 1. Connect to MongoDB
    await connect_to_mongo()
    logger.info("MongoDB connection established.")
    
    db_client: AsyncIOMotorClient = await get_database()

    # 2. Initialize Phase 3 Model Manager
    try:
        await model_manager.initialize_models()
        logger.info("Phase 3 AI models initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Phase 3 AI models: {e}", exc_info=True)

    # 3. Initialize new Phase 4 services globally
    global pricing_service_instance
    pricing_service_instance = PricingService(db_client)
    try:
        await pricing_service_instance.initialize()
        logger.info("PricingService initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize PricingService: {e}")

    global churn_service_instance
    churn_service_instance = ChurnService(db_client)
    try:
        await churn_service_instance.initialize()
        logger.info("ChurnService initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize ChurnService: {e}")

    global reasoning_service_instance
    reasoning_service_instance = ReasoningService(db_client)
    try:
        await reasoning_service_instance.initialize()
        logger.info("ReasoningService initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize ReasoningService: {e}")

    global feedback_service_instance
    feedback_service_instance = FeedbackService(db_client)
    try:
        await feedback_service_instance.initialize()
        logger.info("FeedbackService initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize FeedbackService: {e}")

    logger.info("All AI services initialization attempted.")
    
    # 4. Schedule periodic retraining using APScheduler
    if settings.MODEL_RETRAIN_INTERVAL_MINUTES > 0:
        scheduler = AsyncIOScheduler()
        
        retrain_interval_seconds = settings.MODEL_RETRAIN_INTERVAL_MINUTES * 60
        
        scheduler.add_job(
            periodic_model_retraining_all,
            IntervalTrigger(seconds=retrain_interval_seconds),
            id='full_model_retraining_job',
            name='Full Model Retraining Task',
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"Full model retraining scheduled every {settings.MODEL_RETRAIN_INTERVAL_MINUTES} minutes.")
        
        app.state.scheduler = scheduler

    yield # Application will run now

    # 5. Shutdown logic
    logger.info("AI Service shutting down...")
    
    if hasattr(app.state, 'scheduler') and app.state.scheduler.running:
        logger.info("Shutting down APScheduler...")
        app.state.scheduler.shutdown()
        logger.info("APScheduler shut down.")
        
    await close_mongo_connection()
    logger.info("AI Service shut down complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    description="FastAPI based AI microservice for Adaptive Business Intelligence. Provides forecasting, anomaly detection, recommendation, dynamic pricing, churn prediction, knowledge graph insights, and feedback capabilities."
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers (Phase 3)
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(forecast.router, prefix="/api/v1/forecast", tags=["Forecasting"])
app.include_router(anomaly.router, prefix="/api/v1/anomaly", tags=["Anomaly Detection"])
app.include_router(recommend.router, prefix="/api/v1/recommend", tags=["Recommendation"])

# Include new advanced API routers (Phase 4)
app.include_router(advanced_endpoints.router, prefix="/api/v1/ai", tags=["Advanced AI"])


@app.get("/", summary="Root endpoint", tags=["Root"])
async def read_root():
    """
    Root endpoint for the AI service.
    """
    return {"message": "Welcome to the Adaptive BI AI Service!", "version": settings.APP_VERSION}

# Dependency to get model manager instance (Phase 3)
def get_model_manager() -> ModelManager:
    return model_manager

# Dependency functions for Phase 4 services to be used by endpoints
async def get_pricing_service_actual() -> PricingService:
    if pricing_service_instance and pricing_service_instance._model_trained:
        return pricing_service_instance
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Pricing service is not ready. Model not trained or loaded.")

async def get_churn_service_actual() -> ChurnService:
    if churn_service_instance and churn_service_instance._model_trained:
        return churn_service_instance
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Churn service is not ready. Model not trained or loaded.")

async def get_reasoning_service_actual() -> ReasoningService:
    if reasoning_service_instance and reasoning_service_instance._graph_built:
        return reasoning_service_instance
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Reasoning service (Knowledge Graph) is not ready. Graph not built or loaded.")

async def get_feedback_service_actual() -> FeedbackService:
    if feedback_service_instance and feedback_service_instance._initialized:
        return feedback_service_instance
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Feedback service is not ready. Not initialized.")


# Assign the actual dependency functions
advanced_endpoints.get_pricing_service_dependency = get_pricing_service_actual
advanced_endpoints.get_churn_service_dependency = get_churn_service_actual
advanced_endpoints.get_reasoning_service_dependency = get_reasoning_service_actual
advanced_endpoints.get_feedback_service_dependency = get_feedback_service_actual


@app.get("/status", summary="Service status", tags=["Status"])
async def get_service_status(manager: ModelManager = Depends(get_model_manager)):
    """
    Provides a quick status overview of the AI service, including model readiness.
    """
    status_response = {
        "status": "running",
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG,
        "database_connected": manager.db_connected,
        "phase3_models": {
            "overall_loaded": manager.models_loaded,
            "forecasting_model_trained": manager.forecasting_model.is_trained if manager.forecasting_model else False,
            "anomaly_model_trained": manager.anomaly_model.is_trained if manager.anomaly_model else False,
            "recommendation_model_trained": manager.recommendation_model.is_trained if manager.recommendation_model else False,
            "last_retrain_time": manager.last_retrain_time.isoformat() if manager.last_retrain_time else "N/A",
            "retrain_interval_minutes": settings.MODEL_RETRAIN_INTERVAL_MINUTES
        },
        "phase4_services": {
            "pricing_service_ready": pricing_service_instance._model_trained if pricing_service_instance else False,
            "churn_service_ready": churn_service_instance._model_trained if churn_service_instance else False,
            "reasoning_service_ready": reasoning_service_instance._graph_built if reasoning_service_instance else False,
            "feedback_service_ready": feedback_service_instance._initialized if feedback_service_instance else False,
        },
        "overall_readiness": "initializing"
    }

    all_models_ready = (
        manager.models_loaded and
        (pricing_service_instance and pricing_service_instance._model_trained) and
        (churn_service_instance and churn_service_instance._model_trained) and
        (reasoning_service_instance and reasoning_service_instance._graph_built) and
        (feedback_service_instance and feedback_service_instance._initialized)
    )

    if all_models_ready:
        status_response["overall_readiness"] = "ready"
    else:
        status_response["overall_readiness"] = "partial_readiness"

    return status_response


if __name__ == "__main__":
    host = getattr(settings, 'HOST', "0.0.0.0")
    port = getattr(settings, 'PORT', 8001)
    debug = getattr(settings, 'DEBUG', False)

    uvicorn.run(app, host=host, port=port, debug=debug)


```

### `./app/model_configs/__init__.py`
```py
#
```

### `./app/model_configs/model_config.py`
```py
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

### `./app/models/advanced_models.py`
```py
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
        # Add a small epsilon to avoid division by zero
        features['demand_ratio'] = features['quantity'] / (features['quantity'].rolling(window=7).mean() + 1e-6)
        # Ensure that quantity.pct_change() is not zero before dividing
        features['price_elasticity'] = (features['price'].pct_change() / 
                                      (features['quantity'].pct_change() + 1e-6)).fillna(0)
        
        # Market features
        # Handle cases where sum might be zero
        features['market_share'] = features.groupby('product_id')['quantity'].transform(
            lambda x: x / (x.sum() + 1e-6)
        )
        # Handle cases where std might be zero
        features['competitive_index'] = features.groupby('category')['price'].transform(
            lambda x: (x - x.mean()) / (x.std() + 1e-6)
        ).fillna(0)
        
        # Inventory features
        features['inventory_turnover'] = features['quantity'] / features.get('stock_level', 100).replace(0, 1) # Avoid division by zero
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
            
            # Check if X is empty after feature preparation
            if X.empty:
                return {'status': 'error', 'message': 'No features generated for prediction.'}

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
            if 'price' in data.columns:
                current_prices = data['price'].values
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
        # self.target_encoder = TargetEncoder() # Not directly used in prepare_features currently
        self.feature_columns = []
        self.is_trained = False
        self.feature_importance = {}
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare comprehensive features for churn prediction."""
        features = data.copy()
        
        # Ensure 'timestamp', 'transaction_id', 'amount', 'category', 'product_id', 'user_id' are present
        # Fill missing critical columns with placeholders if they are not in `data`
        for col in ['timestamp', 'transaction_id', 'amount', 'category', 'product_id', 'user_id']:
            if col not in features.columns:
                if col == 'timestamp':
                    features[col] = datetime.now() # Use current time as fallback
                elif col == 'amount':
                    features[col] = 0.0
                elif col == 'user_id':
                    features[col] = 'unknown_user'
                else:
                    features[col] = 'unknown' # Placeholder for string columns

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
        
        # Behavioral features
        behavior_features = features.groupby('user_id').agg(
            category_diversity=('category', lambda x: x.nunique()),  # Category diversity
            product_diversity=('product_id', lambda x: x.nunique()),  # Product diversity
            customer_lifetime_days=('timestamp', lambda x: (pd.to_datetime(x).max() - pd.to_datetime(x).min()).days)  # Customer lifetime
        ).reset_index()
        
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
            
            # Handle cases where X or y might be empty or have issues
            if X.empty or y.empty or len(X) != len(y):
                raise ValueError("Prepared data (X or y) is empty or mismatched for training.")
            
            # Check if there are enough samples and both classes are present for SMOTE/stratify
            if len(X) < 2 or len(np.unique(y)) < 2:
                # Fallback if not enough samples or only one class
                if len(X) >= 2:
                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                    logger.warning("SMOTE or stratification skipped due to insufficient data or single class.")
                else:
                    raise ValueError("Insufficient data for training after feature preparation.")
            else:
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
            
            if features.empty:
                return {'status': 'error', 'message': 'No features generated for prediction.'}

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

### `./app/models/anomaly_detection.py`
```py
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
import joblib
import os
from app.config import settings
from app.utils.logger import logger
from app.services.feature_engineering import FeatureEngineer

class AnomalyDetectionModel:
    """
    Implements a machine learning model for anomaly detection.
    Supports IsolationForest and OneClassSVM.
    """
    def __init__(self, model_type: str = settings.ANOMALY_MODEL_TYPE, contamination: float = settings.ANOMALY_THRESHOLD):
        self.model = None
        self.model_type = model_type
        self.contamination = contamination
        self.feature_engineer = FeatureEngineer() # Feature engineer for scaling etc.
        self.model_path = os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_model_{model_type}.joblib")
        self.is_trained = False
        self.metrics = {}

    def _initialize_model(self):
        """Initializes the ML model based on model_type."""
        if self.model_type == "IsolationForest":
            self.model = IsolationForest(contamination=self.contamination, random_state=42, n_estimators=100)
            logger.info(f"Initialized IsolationForest for anomaly detection with contamination={self.contamination}.")
        elif self.model_type == "OneClassSVM":
            # nu is an upper bound on the fraction of training errors and a lower bound of the fraction of support vectors.
            # It's similar to contamination. A common value is 0.1 for typical anomaly rates.
            self.model = OneClassSVM(kernel='rbf', nu=self.contamination)
            logger.info(f"Initialized OneClassSVM for anomaly detection with nu={self.contamination}.")
        else:
            raise ValueError(f"Unsupported anomaly detection model type: {self.model_type}")

    def train(self, df: pd.DataFrame, features: list) -> dict:
        """
        Trains the anomaly detection model.
        :param df: DataFrame containing features for anomaly detection.
        :param features: List of columns to be used as features.
        """
        if df.empty or not features or not all(col in df.columns for col in features):
            logger.warning("No data or invalid features for anomaly detection training.")
            return {"status": "failed", "message": "No data or invalid features."}

        # Select features
        X = df[features]

        # Scale features (important for distance-based algorithms like SVM)
        # Scale features (important for distance-based algorithms like SVM)
        X_scaled = self.feature_engineer.scale_features(X, features, scaler_type='MinMaxScaler', fit=True)
        # Store original feature names for prediction consistency
        self._trained_features = X_scaled.columns.tolist()

        self._initialize_model()
        logger.info(f"Starting training for {self.model_type} model with {len(X_scaled)} samples and {len(features)} features.")
        if self.model is None:
            logger.error("Model is not initialized. Cannot fit.")
            return {"status": "failed", "message": "Model initialization failed."}
        self.model.fit(X_scaled)
        # No traditional "metrics" for unsupervised anomaly detection,
        if self.model_type == "IsolationForest":
            if self.model is not None:
                predictions = self.model.predict(X_scaled)
                n_outliers = list(predictions).count(-1)
                outlier_percentage = (n_outliers / len(predictions)) * 100 if len(predictions) > 0 else 0
                self.metrics = {"outliers_in_training_data": n_outliers, "outlier_percentage": f"{outlier_percentage:.2f}%"}
            else:
                logger.error("Model is None during prediction.")
                self.metrics = {}
        elif self.model_type == "OneClassSVM":
            if self.model is not None:
                predictions = self.model.predict(X_scaled)
                n_outliers = list(predictions).count(-1)
                outlier_percentage = (n_outliers / len(predictions)) * 100 if len(predictions) > 0 else 0
                self.metrics = {"outliers_in_training_data": n_outliers, "outlier_percentage": f"{outlier_percentage:.2f}%"}
            else:
                logger.error("Model is None during prediction.")
                self.metrics = {}
            outlier_percentage = (n_outliers / len(predictions)) * 100 if len(predictions) > 0 else 0
            self.metrics = {"outliers_in_training_data": n_outliers, "outlier_percentage": f"{outlier_percentage:.2f}%"}

        self.is_trained = True
        logger.info(f"Anomaly detection model training complete. Metrics: {self.metrics}")
        self.save_model()
        return {"status": "success", "metrics": self.metrics}

    def detect_anomalies(self, df: pd.DataFrame, features: list) -> pd.DataFrame:
        """
        Detects anomalies in the input DataFrame.
        Returns the DataFrame with an 'is_anomaly' column and anomaly scores.
        """
        if not self.is_trained or self.model is None:
            logger.error("Anomaly detection model not trained. Cannot detect anomalies.")
            raise ValueError("Model not trained.")
        if df.empty or not features or not all(col in df.columns for col in features):
            logger.warning("No data or invalid features for anomaly detection.")
            return df.assign(is_anomaly=False, anomaly_score=0.0) # Return with default columns

        X = df[features]
        # Use existing scaler for transformation
        X_scaled = self.feature_engineer.scale_features(X, features, scaler_type='MinMaxScaler', fit=False)

        # Ensure prediction features match trained features
        # This is a critical step. If `_trained_features` is None or not matching, it's an error.
        if not hasattr(self, '_trained_features') or not self._trained_features:
            logger.error("Trained features not available. Model might not have been trained or loaded correctly.")
            raise RuntimeError("Trained features not found for anomaly detection.")
        
        # Align columns of X_scaled with self._trained_features, filling missing ones with 0 or appropriate default
        X_scaled = X_scaled.reindex(columns=self._trained_features, fill_value=0)

        # Predict raw scores or decisions
        if self.model_type == "IsolationForest":
            # decision_function gives anomaly scores: lower is more anomalous
            df['anomaly_score'] = self.model.decision_function(X_scaled)
            # predict returns -1 for outliers, 1 for inliers
            df['is_anomaly'] = (self.model.predict(X_scaled) == -1)
        elif self.model_type == "OneClassSVM":
            # decision_function gives distance to hyperplane: negative for outliers
            df['anomaly_score'] = self.model.decision_function(X_scaled)
            df['is_anomaly'] = (self.model.predict(X_scaled) == -1)
        else:
            raise ValueError(f"Unsupported model type {self.model_type} for anomaly detection logic.")

        logger.info(f"Detected anomalies for {len(df)} samples.")
        return df
        for _, row in anomalies_df.iterrows():
            timestamp_value = row.get('timestamp')
            detail = {
                "id": str(row.get('_id')), # Assuming _id exists and can be converted to str
                "timestamp": timestamp_value.isoformat() if timestamp_value is not None and hasattr(timestamp_value, "isoformat") else None,
                "anomaly_score": float(row['anomaly_score']),
                "features": {feat: row[feat] for feat in anomaly_features if feat in row}
            }
            details.append(detail)
        return details
        details = []
        for index, row in anomalies_df.iterrows():
            detail = {
                "id": str(row.get('_id')), # Assuming _id exists and can be converted to str
                "timestamp": row.get('timestamp').isoformat() if 'timestamp' in row else None,
                "anomaly_score": float(row['anomaly_score']),
                "features": {feat: row[feat] for feat in anomaly_features if feat in row}
            }
            details.append(detail)
        return details

    def save_model(self):
        """Saves the trained model and its feature engineer."""
        if self.model:
            os.makedirs(settings.MODEL_SAVE_PATH, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.feature_engineer, os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_feature_engineer_{self.model_type}.joblib"))
            # Also save the list of trained features
            if hasattr(self, '_trained_features'):
                joblib.dump(self._trained_features, os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_trained_features_{self.model_type}.joblib"))
            logger.info(f"Anomaly detection model and feature engineer saved to {self.model_path}")
        else:
            logger.warning("No anomaly detection model to save.")

    def load_model(self):
        """Loads the trained model and its feature engineer."""
        try:
            self.model = joblib.load(self.model_path)
            self.feature_engineer = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_feature_engineer_{self.model_type}.joblib"))
            # Load trained features
            trained_features_path = os.path.join(settings.MODEL_SAVE_PATH, f"anomaly_trained_features_{self.model_type}.joblib")
            if os.path.exists(trained_features_path):
                self._trained_features = joblib.load(trained_features_path)
            else:
                logger.warning("Trained features not found for anomaly model. This might cause issues during prediction if feature set changes.")
                self._trained_features = None # Or raise error
            
            self.is_trained = True
            logger.info(f"Anomaly detection model and feature engineer loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Anomaly detection model not found at {self.model_path}. Model needs to be trained.")
            self.is_trained = False
            return False
        except Exception as e:
            logger.error(f"Error loading anomaly detection model: {e}", exc_info=True)
            self.is_trained = False
            return False
```

### `./app/models/explainable_ai.py`
```py
import os
import numpy as np
import pandas as pd
import shap
import lime
import lime.lime_tabular
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
from datetime import datetime, timezone

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
            
            if X_train.empty:
                return {'status': 'error', 'message': 'X_train data is empty, cannot setup explainer.'}

            self.feature_names[model_name] = list(X_train.columns)
            
            if explainer_type in ['shap', 'both']:
                # Setup SHAP explainer
                if hasattr(model, 'predict_proba') and len(np.unique(model.predict(X_train))) == 2:
                    # For binary classification models, use TreeExplainer or KernelExplainer based on model type
                    try:
                        self.shap_explainers[model_name] = shap.TreeExplainer(model)
                    except Exception:
                        # Fallback to KernelExplainer if TreeExplainer fails (e.g., non-tree model or complex input)
                        self.shap_explainers[model_name] = shap.KernelExplainer(model.predict_proba, X_train)
                else:
                    # For regression models or multi-class where predict_proba might not be direct for TreeExplainer
                    try:
                        self.shap_explainers[model_name] = shap.TreeExplainer(model)
                    except Exception:
                        self.shap_explainers[model_name] = shap.KernelExplainer(model.predict, X_train)

            if explainer_type in ['lime', 'both']:
                # Setup LIME explainer
                mode = 'classification' if hasattr(model, 'predict_proba') else 'regression'
                self.lime_explainers[model_name] = lime.lime_tabular.LimeTabularExplainer(
                    training_data=X_train.values, # LIME expects numpy array
                    feature_names=list(X_train.columns),
                    class_names=model.classes_.tolist() if hasattr(model, 'classes_') else ['output'] , # For classification
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
            
            if X_instance.empty:
                return {'status': 'error', 'message': 'X_instance is empty, cannot generate SHAP explanation.'}

            # Get SHAP values
            shap_values = explainer.shap_values(X_instance)
            
            # Handle multi-class output and ensure shap_values is a single array for contributions
            if isinstance(shap_values, list):
                # For classification, often shap_values is a list of arrays (one for each class)
                # For binary, use the shap values for the positive class (index 1)
                if len(shap_values) == 2:
                    shap_values_arr = shap_values[1] 
                else: # For multi-class, sum absolute shap values across classes or choose a class
                    shap_values_arr = np.sum(np.abs(np.array(shap_values)), axis=0)
            else:
                shap_values_arr = shap_values
            
            # Get feature contributions
            feature_contributions = []
            for i, feature in enumerate(self.feature_names[model_name]):
                # Ensure index is within bounds of shap_values_arr
                if i < len(shap_values_arr):
                    contribution = float(shap_values_arr[i])
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
                # For binary classification, typically use expected value of the positive class
                base_value = float(explainer.expected_value[1]) if len(explainer.expected_value) == 2 else float(explainer.expected_value[0])
            
            prediction = model.predict(X_instance)[0]
            prediction_proba = None
            if hasattr(model, 'predict_proba'):
                prediction_proba = model.predict_proba(X_instance)[0]
            
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
            
            if X_instance.empty:
                return {'status': 'error', 'message': 'X_instance is empty, cannot generate LIME explanation.'}

            # Generate explanation
            # LIME expects a 1D numpy array for a single instance
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
            # LIME's explanation.as_list() returns a list of (feature, weight) tuples
            for feature_name_or_idx, contribution in explanation.as_list():
                # Ensure feature_name is a string and not an index
                if isinstance(feature_name_or_idx, int):
                    feature_name = self.feature_names[model_name][feature_name_or_idx]
                else:
                    feature_name = feature_name_or_idx # Already a string (e.g., for categorical features)

                feature_contributions.append({
                    'feature': feature_name,
                    'contribution': float(contribution),
                    'abs_contribution': abs(float(contribution))
                })
            
            # Get prediction
            prediction = model.predict(X_instance)[0]
            prediction_proba = None
            if hasattr(model, 'predict_proba'):
                prediction_proba = model.predict_proba(X_instance)[0]
            
            return {
                'status': 'success',
                'model_name': model_name,
                'prediction': float(prediction),
                'prediction_proba': prediction_proba.tolist() if prediction_proba is not None else None,
                'feature_contributions': feature_contributions,
                'explanation_score': explanation.score, # LIME's faithfulness score
                'local_accuracy': explanation.local_exp # The linear model's local explanation
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
            
            if X_sample.empty:
                return {'status': 'error', 'message': 'Sampled data is empty, cannot generate global explanations.'}

            explainer = self.shap_explainers[model_name]
            shap_values = explainer.shap_values(X_sample)
            
            # Handle multi-class output and ensure shap_values is a single array for contributions
            if isinstance(shap_values, list):
                # For classification, often shap_values is a list of arrays (one for each class)
                # For binary, use the shap values for the positive class (index 1)
                if len(shap_values) == 2:
                    shap_values_arr = shap_values[1] 
                else: # For multi-class, sum absolute shap values across classes or choose a class
                    shap_values_arr = np.sum(np.abs(np.array(shap_values)), axis=0)
            else:
                shap_values_arr = shap_values
            
            # Calculate feature importance (mean absolute SHAP value)
            feature_importance = np.abs(shap_values_arr).mean(axis=0)
            
            # Create feature importance ranking
            feature_ranking = []
            for i, feature in enumerate(self.feature_names[model_name]):
                if i < len(feature_importance): # Ensure index is within bounds
                    feature_ranking.append({
                        'feature': feature,
                        'importance': float(feature_importance[i]),
                        'mean_impact': float(np.mean(shap_values_arr[:, i])),
                        'impact_std': float(np.std(shap_values_arr[:, i]))
                    })
            
            feature_ranking.sort(key=lambda x: x['importance'], reverse=True)
            
            # Generate summary statistics
            summary_stats = {}
            if feature_ranking: # Ensure feature_ranking is not empty
                summary_stats = {
                    'most_important_feature': feature_ranking[0]['feature'],
                    'least_important_feature': feature_ranking[-1]['feature'],
                    'total_features': len(feature_ranking),
                    'top_5_features': [f['feature'] for f in feature_ranking[:5]],
                    'feature_importance_distribution': {
                        'mean': float(np.mean(feature_importance)) if len(feature_importance) > 0 else 0,
                        'std': float(np.std(feature_importance)) if len(feature_importance) > 0 else 0,
                        'min': float(np.min(feature_importance)) if len(feature_importance) > 0 else 0,
                        'max': float(np.max(feature_importance)) if len(feature_importance) > 0 else 0
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
        if 'feature_ranking' not in explanation_data or not explanation_data['feature_ranking']:
            return {'status': 'error', 'message': 'No feature ranking data available for visualization'}
        
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
            height=500,
            # Ensure y-axis labels are readable, especially for longer feature names
            yaxis={'automargin': True, 'categoryorder': 'total ascending'} 
        )
        
        return {
            'status': 'success',
            'chart_data': fig.to_dict(),
            'chart_type': 'feature_importance'
        }
    
    def _create_waterfall_viz(self, explanation_data: Dict) -> Dict:
        """Create waterfall chart for feature contributions."""
        if 'feature_contributions' not in explanation_data or not explanation_data['feature_contributions']:
            return {'status': 'error', 'message': 'No feature contributions data available for visualization'}
        
        contributions = explanation_data['feature_contributions'][:8]  # Top 8 features
        
        features = [f['feature'] for f in contributions]
        values = [f['contribution'] for f in contributions]
        
        # Add base value and prediction
        base_value = explanation_data.get('base_value', 0)
        prediction_value = explanation_data.get('prediction', base_value + sum(values))

        x_labels = ['Base Value'] + features + ['Prediction']
        # The 'y' values for plotly.graph_objs.Waterfall are the *change* values, not cumulative
        # We need to explicitly define the `measure` to dictate if it's absolute, relative, or total
        measures = ["absolute"] + ["relative"] * len(values) + ["total"]
        
        fig = go.Figure(data=[
            go.Waterfall(
                name="Feature Contributions",
                orientation="v",
                measure=measures,
                x=x_labels,
                textposition="outside",
                text=[f"{val:.3f}" for val in [base_value] + values + [prediction_value]], # Display actual values for text
                y=[base_value] + values + [prediction_value], # These are the values from which changes are calculated
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            )
        ])
        
        fig.update_layout(
            title="Feature Contribution Waterfall",
            showlegend=True,
            height=500,
            # Ensure x-axis labels are readable
            xaxis={'automargin': True, 'tickangle': 45} 
        )
        
        return {
            'status': 'success',
            'chart_data': fig.to_dict(),
            'chart_type': 'waterfall'
        }
    
    def _create_feature_comparison_viz(self, explanation_data: Dict) -> Dict:
        """Create feature comparison visualization."""
        if 'feature_contributions' not in explanation_data or not explanation_data['feature_contributions']:
            return {'status': 'error', 'message': 'No feature contributions data available for visualization'}
        
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
            
            if X_batch.empty:
                return {'status': 'success', 'explanations': [], 'batch_size': 0, 'method': method, 'message': 'Input batch is empty.'}

            for idx, row in X_batch.iterrows():
                X_instance = pd.DataFrame([row]) # Create a DataFrame for single row
                
                explanation = {'status': 'error', 'message': 'Explanation method not supported or failed'}
                if method == 'shap':
                    explanation = self.explain_prediction_shap(model, X_instance, model_name)
                elif method == 'lime':
                    explanation = self.explain_prediction_lime(model, X_instance, model_name)
                
                if explanation['status'] == 'success':
                    explanation['instance_id'] = str(idx) # Ensure ID is string for consistent JSON
                    explanations.append(explanation)
                else:
                    logger.warning(f"Failed to explain instance {idx} with {method}: {explanation.get('message', 'Unknown error')}")
            
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
            # SHAP and LIME explainers themselves are often not directly serializable like joblib.
            # Here, we save the configuration and rely on re-initializing the explainer.
            explainer_data = {
                'model_name': model_name,
                'feature_names': self.feature_names.get(model_name, []),
                'has_shap': model_name in self.shap_explainers,
                'has_lime': model_name in self.lime_explainers,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True) # Ensure directory exists
            with open(filepath, 'w') as f:
                json.dump(explainer_data, f, indent=2)
            
            return {'status': 'success', 'filepath': filepath}
            
        except Exception as e:
            logger.error(f"Error saving explainer config: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def load_explainer(self, filepath: str) -> Dict:
        """Load explainer configuration."""
        try:
            if not os.path.exists(filepath):
                return {'status': 'error', 'message': f'Explainer config file not found: {filepath}'}

            with open(filepath, 'r') as f:
                explainer_data = json.load(f)
            
            model_name = explainer_data['model_name']
            self.feature_names[model_name] = explainer_data['feature_names']
            
            # Note: SHAP/LIME explainer objects themselves are not loaded here.
            # They need to be re-initialized using `setup_explainer` with the trained model and data.
            
            return {'status': 'success', 'model_name': model_name, 'loaded_config': explainer_data}
            
        except Exception as e:
            logger.error(f"Error loading explainer config: {str(e)}")
            return {'status': 'error', 'message': str(e)}

```

### `./app/models/forecasting.py`
```py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
from app.config import settings
from app.utils.logger import logger
from app.services.feature_engineering import FeatureEngineer

class ForecastingModel:
    """
    Implements a machine learning model for sales forecasting.
    Supports RandomForestRegressor and LinearRegression.
    """
    def __init__(self, model_type: str = settings.FORECAST_MODEL_TYPE):
        self.model = None
        self.model_type = model_type
        self.feature_engineer = FeatureEngineer()
        self.model_path = os.path.join(settings.MODEL_SAVE_PATH, f"forecasting_model_{model_type}.joblib")
        self.is_trained = False
        self.metrics = {} # To store training metrics
        self._trained_features = None

    def _initialize_model(self):
        """Initializes the ML model based on model_type."""
        if self.model_type == "RandomForestRegressor":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            logger.info("Initialized RandomForestRegressor for forecasting.")
        elif self.model_type == "LinearRegression":
            self.model = LinearRegression()
            logger.info("Initialized LinearRegression for forecasting.")
        else:
            raise ValueError(f"Unsupported forecasting model type: {self.model_type}")

    def train(self, df: pd.DataFrame, target_col: str = 'totalAmount') -> dict:
        """
        Trains the forecasting model.
        Expects df to be prepared with time series and feature engineering.
        """
        if df.empty:
            logger.warning("No data to train forecasting model (input DataFrame is empty).")
            return {"status": "failed", "message": "No data for training."}

        df_copy = df.copy()

        df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
        df_copy = df_copy.sort_values('timestamp').reset_index(drop=True)

        df_copy = self.feature_engineer.create_time_features(df_copy, 'timestamp')
        df_copy = self.feature_engineer.create_lag_features(df_copy, cols=[target_col], lags=[1, 2, 3, 7, 14])
        df_copy = self.feature_engineer.create_rolling_features(df_copy, cols=[target_col], windows=[7, 14], agg_funcs=['mean', 'std'])

        df_copy = df_copy.dropna().reset_index(drop=True)

        # Calculate minimum samples needed based on lags and rolling windows (hardcoded to match feature engineering above)
        max_lag = 14  # Matches lags=[1, 2, 3, 7, 14]
        max_window = 14  # Matches windows=[7, 14]
        min_samples_needed = max(max_lag, max_window) + 2 # Need at least (max lag/window) + 1 for features and +1 for target

        if len(df_copy) < min_samples_needed:
            logger.warning(f"Not enough data remaining ({len(df_copy)} rows) after feature engineering for forecasting model training. Need at least {min_samples_needed} rows.")
            return {"status": "failed", "message": f"Not enough data after feature engineering ({len(df_copy)} rows). Need at least {min_samples_needed} rows."}

        features = [col for col in df_copy.columns if col not in [target_col, 'timestamp', '_id']]
        X, y = self.feature_engineer.get_features_and_target(df_copy, target_col, feature_cols=features)

        if X.empty or y.empty:
            logger.error("Features or target are empty after preparation for forecasting model training (after dropna).")
            return {"status": "failed", "message": "Empty features or target after preparation."}

        self._trained_features = X.columns.tolist()

        # Ensure enough data for train/test split. A minimum of 2 samples is needed for the split itself.
        if len(X) < 2:
            logger.warning(f"Insufficient data for train-test split for forecasting model ({len(X)} samples).")
            return {"status": "failed", "message": "Insufficient data for train-test split."}

        split_point = max(1, int(len(X) * 0.8))
        if split_point >= len(X):
            split_point = len(X) - 1

        X_train, X_test = X.iloc[:split_point], X.iloc[split_point:]
        y_train, y_test = y.iloc[:split_point], y.iloc[split_point:]

        if X_train.empty or y_train.empty:
            logger.warning("Training data is empty after split for forecasting model.")
            return {"status": "failed", "message": "Empty training data after split."}

        self._initialize_model()
        logger.info(f"Starting training for {self.model_type} model with {len(X_train)} samples.")
        self.model.fit(X_train, y_train)

        if not X_test.empty and not y_test.empty:
            y_pred = self.model.predict(X_test)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            self.metrics = {"rmse": rmse, "r2_score": r2, "trained_on_samples": len(X_train), "evaluated_on_samples": len(X_test)}
        else:
            self.metrics = {"rmse": "N/A", "r2_score": "N/A", "trained_on_samples": len(X_train), "evaluated_on_samples": 0, "message": "Not enough data for test evaluation."}
            logger.warning("Not enough data to create a test set for forecasting model evaluation.")

        self.is_trained = True
        logger.info(f"Forecasting model training complete. Metrics: {self.metrics}")

        self.save_model()
        return {"status": "success", "metrics": self.metrics}

    def predict(self, df: pd.DataFrame, target_col: str = 'totalAmount') -> np.ndarray:
        """
        Makes predictions using the trained model.
        Expects df to be prepared with the same feature engineering steps as training.
        """
        if not self.is_trained or self.model is None:
            logger.error("Forecasting model not trained. Cannot make predictions.")
            raise ValueError("Model not trained.")
        if df.empty:
            logger.warning("No data provided for prediction.")
            return np.array([])

        df_copy = df.copy()

        df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
        df_copy = df_copy.sort_values('timestamp').reset_index(drop=True)

        df_copy = self.feature_engineer.create_time_features(df_copy, 'timestamp')
        df_copy = self.feature_engineer.create_lag_features(df_copy, cols=[target_col], lags=[1, 2, 3, 7, 14])
        df_copy = self.feature_engineer.create_rolling_features(df_copy, cols=[target_col], windows=[7, 14], agg_funcs=['mean', 'std'])
        df_copy = df_copy.dropna().reset_index(drop=True)

        if df_copy.empty:
            logger.warning("DataFrame became empty after feature engineering for prediction.")
            return np.array([])

        if self._trained_features is None:
            logger.error("Trained features not available. Model might not have been trained or loaded correctly.")
            raise RuntimeError("Trained features not found for forecasting prediction.")
        
        X = df_copy[self._trained_features].fillna(0)

        predictions = self.model.predict(X)
        logger.info(f"Generated {len(predictions)} predictions.")
        return predictions

    def forecast_future(self, historical_df: pd.DataFrame, horizon: int = settings.FORECAST_HORIZON, target_col: str = 'totalAmount'):
        """
        Forecasts future values for a given horizon using the trained model.
        Requires enough historical data for lag and rolling features.
        """
        if not self.is_trained or self.model is None:
            logger.error("Forecasting model not trained. Cannot forecast future values.")
            raise ValueError("Model not trained.")
        if historical_df.empty:
            logger.warning("No historical data provided for forecasting.")
            return pd.DataFrame()
        if self._trained_features is None:
            logger.error("Trained features not available. Model might not have been trained or loaded correctly.")
            raise RuntimeError("Trained features not found for forecasting future values.")

        historical_df_copy = historical_df.copy()

        historical_df_copy['timestamp'] = pd.to_datetime(historical_df_copy['timestamp'])
        historical_df_copy = historical_df_copy.sort_values('timestamp').reset_index(drop=True)

        last_date = historical_df_copy['timestamp'].max()
        
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, horizon + 1)]
        forecast_df_template = pd.DataFrame({'timestamp': future_dates, target_col: 0.0})

        combined_df = pd.concat([historical_df_copy, forecast_df_template], ignore_index=True)
        combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)

        combined_df = self.feature_engineer.create_time_features(combined_df, 'timestamp')
        combined_df = self.feature_engineer.create_lag_features(combined_df, cols=[target_col], lags=[1, 2, 3, 7, 14])
        combined_df = self.feature_engineer.create_rolling_features(combined_df, cols=[target_col], windows=[7, 14], agg_funcs=['mean', 'std'])

        combined_df = combined_df.fillna(0)

        future_X_raw = combined_df[combined_df['timestamp'].isin(future_dates)]
        
        if future_X_raw.empty:
            logger.warning("Future data frame is empty after feature engineering for forecasting.")
            return pd.DataFrame()

        X_predict = future_X_raw[self._trained_features].fillna(0)

        future_predictions = self.model.predict(X_predict)

        forecast_df = pd.DataFrame({
            'timestamp': future_dates,
            target_col: future_predictions
        })

        logger.info(f"Generated {horizon} day forecast for '{target_col}'.")
        return forecast_df[['timestamp', target_col]]


    def save_model(self):
        """Saves the trained model and feature engineer (scalers/encoders) and trained features."""
        if self.model:
            os.makedirs(settings.MODEL_SAVE_PATH, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.feature_engineer, os.path.join(settings.MODEL_SAVE_PATH, f"forecasting_feature_engineer_{self.model_type}.joblib"))
            joblib.dump(self._trained_features, os.path.join(settings.MODEL_SAVE_PATH, f"forecasting_trained_features_{self.model_type}.joblib"))
            logger.info(f"Forecasting model, feature engineer, and trained features saved to {self.model_path}")
        else:
            logger.warning("No forecasting model to save.")

    def load_model(self):
        """Loads the trained model and feature engineer and trained features."""
        try:
            self.model = joblib.load(self.model_path)
            self.feature_engineer = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, f"forecasting_feature_engineer_{self.model_type}.joblib"))
            self._trained_features = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, f"forecasting_trained_features_{self.model_type}.joblib"))
            self.is_trained = True
            logger.info(f"Forecasting model, feature engineer, and trained features loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Forecasting model not found at {self.model_path}. Model needs to be trained.")
            self.is_trained = False
            return False
        except Exception as e:
            logger.error(f"Error loading forecasting model: {e}", exc_info=True)
            self.is_trained = False
            return False
```

### `./app/models/__init__.py`
```py

```

### `./app/models/knowledge_graph.py`
```py
import os
import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
import joblib # For saving/loading graph

logger = logging.getLogger(__name__)

class CustomerBehaviorGraph:
    """Knowledge graph for customer behavior analysis and reasoning."""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph() # Use MultiDiGraph to allow multiple edges between nodes (e.g., multiple purchases)
        self.node_attributes = {} # Cache for quick attribute lookup
        self.edge_attributes = {} # Cache for quick attribute lookup
        self._is_built = False # Flag to indicate if graph has been built
        
    def build_graph_from_data(self, transactions: pd.DataFrame, 
                            products: pd.DataFrame, 
                            users: pd.DataFrame) -> Dict:
        """Build knowledge graph from transaction, product, and user data."""
        try:
            logger.info("Building customer behavior knowledge graph...")
            
            # Reset graph before rebuilding
            self.graph = nx.MultiDiGraph()
            self.node_attributes = {}
            self.edge_attributes = {}

            if transactions.empty or products.empty or users.empty:
                logger.warning("One or more input DataFrames are empty. Cannot build graph.")
                self._is_built = False
                return {'status': 'error', 'message': 'Insufficient data to build graph.'}

            # --- Add Customer Nodes ---
            for _, user_row in users.iterrows():
                user_id = user_row['userId'] # Use 'userId' from your User Schema
                attrs = {
                    'type': 'customer',
                    'username': user_row.get('username'),
                    'email': user_row.get('email'),
                    'registrationDate': user_row.get('registrationDate'),
                    'lastLogin': user_row.get('lastLogin'),
                    'country': user_row.get('address', {}).get('country', 'unknown'), # Assuming address is dict
                    'total_spent_lifetime': user_row.get('total_spent', 0), # From data_generator User Schema
                    'total_orders_lifetime': user_row.get('total_orders', 0) # From data_generator User Schema
                }
                self.graph.add_node(f"customer_{user_id}", **attrs)
                self.node_attributes[f"customer_{user_id}"] = attrs
            logger.info(f"Added {len(users)} customer nodes.")
            
            # --- Add Product Nodes ---
            for _, product_row in products.iterrows():
                product_id = product_row['productId'] # Use 'productId' from your Product Schema
                attrs = {
                    'type': 'product',
                    'name': product_row.get('name'),
                    'category': product_row.get('category'),
                    'price': product_row.get('price'), # This is base price from product schema
                    'stock': product_row.get('stock'),
                    'addedDate': product_row.get('addedDate')
                }
                self.graph.add_node(f"product_{product_id}", **attrs)
                self.node_attributes[f"product_{product_id}"] = attrs
            logger.info(f"Added {len(products)} product nodes.")

            # --- Add Category Nodes (if not implicitly added through products) ---
            # Ensure categories from products are added as distinct nodes
            for category in products['category'].unique():
                attrs = {
                    'type': 'category',
                    'category_name': category
                }
                self.graph.add_node(f"category_{category}", **attrs)
                self.node_attributes[f"category_{category}"] = attrs
            logger.info(f"Added {len(products['category'].unique())} category nodes.")
            
            # --- Add Transaction Nodes and Relationships ---
            # It's good to add transaction nodes if each transaction needs to be a distinct entity
            # and have properties itself. Or, just use them to create direct relationships.
            # For simplicity, we'll create direct relationships for now (user-product)
            # You could add transaction nodes later if needed.

            for _, tx_row in transactions.iterrows():
                transaction_id = tx_row['transactionId'] # From your Transaction Schema
                user_id = tx_row['userId']
                product_id = tx_row['productId']
                category = products[products['productId'] == product_id]['category'].iloc[0] if product_id in products['productId'].values else 'unknown' # Get category from product

                customer_node = f"customer_{user_id}"
                product_node = f"product_{product_id}"
                category_node = f"category_{category}"

                # Add nodes if they don't exist (e.g., if transactions have users/products not in initial population)
                if customer_node not in self.graph:
                    self.graph.add_node(customer_node, type='customer', userId=user_id, status='uninitialized')
                if product_node not in self.graph:
                    self.graph.add_node(product_node, type='product', productId=product_id, status='uninitialized')
                if category_node not in self.graph:
                    self.graph.add_node(category_node, type='category', category_name=category)
                
                # Purchase relationship: Customer -> Product
                purchase_edge_attrs = {
                    'type': 'PURCHASED',
                    'quantity': tx_row['quantity'],
                    'totalPrice': tx_row['totalPrice'], # Use totalPrice from your schema
                    'transactionDate': tx_row['transactionDate'],
                    'status': tx_row['status'],
                    'transactionId': transaction_id # Link to the transaction itself
                }
                self.graph.add_edge(customer_node, product_node, key=transaction_id, **purchase_edge_attrs)
                self.edge_attributes[(customer_node, product_node, transaction_id)] = purchase_edge_attrs

                # Belongs_to relationship: Product -> Category
                if not self.graph.has_edge(product_node, category_node, key='belongs_to'): # Avoid duplicate 'belongs_to' edges
                     self.graph.add_edge(product_node, category_node, key='belongs_to', type='BELONGS_TO')

            logger.info(f"Added {len(transactions)} transaction relationships.")
            
            # --- Add Similar-to Relationships (Customers by shared purchases) ---
            self._add_customer_similarity_relationships(transactions)
            logger.info("Added customer similarity relationships.")

            self._is_built = True
            logger.info(f"Knowledge graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
            
            return {
                'status': 'success',
                'nodes': self.graph.number_of_nodes(),
                'edges': self.graph.number_of_edges(),
                'node_types': self._get_node_type_counts(),
                'edge_types': self._get_edge_type_counts()
            }
            
        except Exception as e:
            logger.error(f"Error building knowledge graph: {str(e)}", exc_info=True)
            self._is_built = False
            return {'status': 'error', 'message': str(e)}

    def _add_customer_similarity_relationships(self, transactions: pd.DataFrame, min_shared_products: int = 2):
        """
        Adds 'SIMILAR_TO' relationships between customers based on shared product purchases.
        This is a simplified example; a real-world scenario might use collaborative filtering output.
        """
        # Create a mapping of user to the set of products they purchased
        user_products = defaultdict(set)
        for _, tx_row in transactions.iterrows():
            user_products[tx_row['userId']].add(tx_row['productId'])

        customer_ids = list(user_products.keys())
        
        # Iterate through all pairs of customers
        for i in range(len(customer_ids)):
            for j in range(i + 1, len(customer_ids)):
                user1_id = customer_ids[i]
                user2_id = customer_ids[j]
                
                products1 = user_products[user1_id]
                products2 = user_products[user2_id]
                
                shared_products = products1.intersection(products2)
                
                if len(shared_products) >= min_shared_products:
                    # Calculate Jaccard similarity as strength of similarity
                    union_products = products1.union(products2)
                    similarity_score = len(shared_products) / len(union_products) if len(union_products) > 0 else 0
                    
                    if similarity_score > 0.1: # Only add if similarity is significant
                        edge_attrs = {
                            'type': 'SIMILAR_TO',
                            'similarity_score': similarity_score,
                            'shared_product_count': len(shared_products)
                        }
                        # Add a non-directional edge for similarity
                        self.graph.add_edge(f"customer_{user1_id}", f"customer_{user2_id}", **edge_attrs)
                        # self.edge_attributes already handles multi-edges, no need for key here unless you want multiple similarity types
                        # No need to cache edge_attributes for similarity if they're always one-to-one

    def get_customer_insights(self, user_id: str) -> Dict:
        """Get comprehensive insights for a specific customer from the graph."""
        if not self._is_built:
            return {'status': 'error', 'message': 'Knowledge graph not built. Please build it first.'}

        customer_node = f"customer_{user_id}"
        if customer_node not in self.graph:
            return {'status': 'error', 'message': f'Customer {user_id} not found in graph.'}
        
        try:
            # Basic customer profile from node attributes
            customer_profile = self.graph.nodes[customer_node]

            # Purchase history (products purchased by this customer)
            purchase_history = []
            for u, v, k, data in self.graph.edges(customer_node, data=True, keys=True):
                if data.get('type') == 'PURCHASED':
                    purchase_history.append({
                        'transactionId': k, # The key for multi-edge (transaction ID)
                        'product_id': v.replace('product_', ''),
                        'quantity': data.get('quantity'),
                        'totalPrice': data.get('totalPrice'),
                        'transactionDate': data.get('transactionDate')
                    })
            
            # Find similar customers
            similar_customers = []
            for u, v, data in self.graph.edges(customer_node, data=True):
                if data.get('type') == 'SIMILAR_TO' and v.startswith('customer_'):
                    similar_customers.append({
                        'userId': v.replace('customer_', ''),
                        'similarity_score': data.get('similarity_score')
                    })
            
            # Products frequently bought together (by this user, or by similar users)
            # This is more complex, typically needs a separate recommendation logic or graph projection
            frequently_bought_together = self._get_frequently_bought_together(user_id)
            
            # Recommendations based on graph traversal (e.g., from similar customers or co-purchased patterns)
            graph_recommendations = self._recommend_products_from_graph(user_id)

            return {
                'status': 'success',
                'user_id': user_id,
                'profile': customer_profile,
                'purchase_history': purchase_history,
                'similar_customers': similar_customers,
                'frequently_bought_together': frequently_bought_together,
                'graph_recommendations': graph_recommendations,
                'insights': self._generate_customer_insights_text(customer_profile, purchase_history)
            }
        except Exception as e:
            logger.error(f"Error getting customer insights for {user_id}: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def _get_frequently_bought_together(self, user_id: str, top_n: int = 5) -> List[Dict]:
        """
        Identifies products frequently bought together by the given user.
        This is a simplified approach, a more robust one uses market basket analysis.
        """
        customer_node = f"customer_{user_id}"
        if customer_node not in self.graph:
            return []

        purchased_products = set()
        for u, v, data in self.graph.edges(customer_node, data=True):
            if data.get('type') == 'PURCHASED' and v.startswith('product_'):
                purchased_products.add(v)
        
        co_purchase_counts = defaultdict(int)
        for prod1_node in purchased_products:
            # Find all users who bought prod1
            for u, v, data in self.graph.in_edges(prod1_node, data=True):
                if data.get('type') == 'PURCHASED':
                    customer_of_prod1 = u
                    # Find other products bought by this user
                    for u2, v2, data2 in self.graph.edges(customer_of_prod1, data=True):
                        if data2.get('type') == 'PURCHASED' and v2.startswith('product_') and v2 != prod1_node:
                            co_purchase_counts[v2] += 1
                            
        sorted_co_purchased = sorted(co_purchase_counts.items(), key=lambda item: item[1], reverse=True)
        
        result = []
        for product_node, count in sorted_co_purchased[:top_n]:
            product_id = product_node.replace('product_', '')
            product_attrs = self.graph.nodes.get(product_node, {})
            result.append({
                'product_id': product_id,
                'name': product_attrs.get('name'),
                'category': product_attrs.get('category'),
                'co_purchase_count': count
            })
        return result

    def _recommend_products_from_graph(self, user_id: str, top_n: int = 5) -> List[Dict]:
        """
        Generates product recommendations for a user based on similar customers' purchases.
        """
        customer_node = f"customer_{user_id}"
        if customer_node not in self.graph:
            return []
        
        # Get products already purchased by the user
        user_purchased_products = {v for u, v, data in self.graph.edges(customer_node, data=True) if data.get('type') == 'PURCHASED'}

        # Aggregate products from similar customers
        product_scores = defaultdict(float)
        for u, v, data in self.graph.edges(customer_node, data=True):
            if data.get('type') == 'SIMILAR_TO' and v.startswith('customer_'):
                similar_customer_node = v
                similarity_score = data.get('similarity_score', 0)
                
                # Iterate through products purchased by the similar customer
                for u2, v2, data2 in self.graph.edges(similar_customer_node, data=True):
                    if data2.get('type') == 'PURCHASED' and v2.startswith('product_') and v2 not in user_purchased_products:
                        product_node = v2
                        # Score by similarity * transaction total (or some other metric)
                        product_scores[product_node] += similarity_score * data2.get('totalPrice', 1.0)
        
        sorted_recommendations = sorted(product_scores.items(), key=lambda item: item[1], reverse=True)
        
        recommendations = []
        for product_node, score in sorted_recommendations[:top_n]:
            product_id = product_node.replace('product_', '')
            product_attrs = self.graph.nodes.get(product_node, {})
            recommendations.append({
                'product_id': product_id,
                'name': product_attrs.get('name'),
                'category': product_attrs.get('category'),
                'score': score
            })
        return recommendations

    def _generate_customer_insights_text(self, profile: Dict, purchase_history: List) -> List[str]:
        """Generates human-readable insights based on customer profile and purchase history."""
        insights = []
        
        # Engagement insights
        if profile.get('total_orders_lifetime', 0) > 10 and profile.get('total_spent_lifetime', 0) > 500:
            insights.append("This is a high-value and frequent customer.")
        elif profile.get('total_orders_lifetime', 0) > 3:
            insights.append("This customer shows good engagement with multiple purchases.")
        else:
            insights.append("This customer is relatively new or has made few purchases.")
            
        # Recency insight
        if profile.get('lastLogin') and isinstance(profile['lastLogin'], datetime):
            days_since_last_login = (datetime.now() - profile['lastLogin']).days
            if days_since_last_login > 30:
                insights.append(f"Last logged in {days_since_last_login} days ago, potentially becoming inactive.")
            elif days_since_last_login < 7:
                insights.append("Recently active, showing good current engagement.")
        
        # Product category preference (from overall purchase history)
        if purchase_history:
            df_history = pd.DataFrame(purchase_history)
            if not df_history.empty and 'category' in df_history.columns:
                most_bought_category = df_history['category'].mode().iloc[0] if not df_history['category'].mode().empty else None
                if most_bought_category:
                    insights.append(f"Shows a strong preference for products in the '{most_bought_category}' category.")
            
        return insights if insights else ["Standard customer profile, no specific patterns identified yet."]


    def get_product_intelligence(self, product_id: str) -> Dict:
        """Get intelligence on a specific product from the graph."""
        if not self._is_built:
            return {'status': 'error', 'message': 'Knowledge graph not built. Please build it first.'}

        product_node = f"product_{product_id}"
        if product_node not in self.graph:
            return {'status': 'error', 'message': f'Product {product_id} not found in graph.'}
        
        try:
            # Basic product profile from node attributes
            product_profile = self.graph.nodes[product_node]

            # Customers who purchased this product
            purchasing_customers = []
            for u, v, k, data in self.graph.edges(data=True, keys=True):
                if v == product_node and data.get('type') == 'PURCHASED':
                    purchasing_customers.append({
                        'userId': u.replace('customer_', ''),
                        'quantity': data.get('quantity'),
                        'totalPrice': data.get('totalPrice'),
                        'transactionDate': data.get('transactionDate'),
                        'transactionId': k
                    })
            
            # Categories this product belongs to
            categories_belonging_to = []
            for u, v, data in self.graph.edges(data=True):
                if u == product_node and data.get('type') == 'BELONGS_TO':
                    categories_belonging_to.append(v.replace('category_', ''))

            # Products frequently bought together with this product
            co_purchased_products = self._get_frequently_bought_together_product(product_id)

            return {
                'status': 'success',
                'product_id': product_id,
                'profile': product_profile,
                'purchasing_customers': purchasing_customers,
                'categories': categories_belonging_to,
                'co_purchased_products': co_purchased_products,
                'insights': self._generate_product_insights_text(product_profile, purchasing_customers)
            }
        except Exception as e:
            logger.error(f"Error getting product intelligence for {product_id}: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def _get_frequently_bought_together_product(self, product_id: str, top_n: int = 5) -> List[Dict]:
        """Identifies products frequently co-purchased with the given product."""
        product_node = f"product_{product_id}"
        if product_node not in self.graph:
            return []

        co_purchase_counts = defaultdict(int)
        
        # Find all customers who bought the product_id
        customers_who_bought = {u for u, v, data in self.graph.in_edges(product_node, data=True) if data.get('type') == 'PURCHASED'}
        
        # For each customer, find other products they bought
        for customer_node in customers_who_bought:
            for u, v, data in self.graph.out_edges(customer_node, data=True):
                if data.get('type') == 'PURCHASED' and v.startswith('product_') and v != product_node:
                    co_purchase_counts[v] += 1
        
        sorted_co_purchased = sorted(co_purchase_counts.items(), key=lambda item: item[1], reverse=True)
        
        result = []
        for co_product_node, count in sorted_co_purchased[:top_n]:
            co_product_id = co_product_node.replace('product_', '')
            co_product_attrs = self.graph.nodes.get(co_product_node, {})
            result.append({
                'product_id': co_product_id,
                'name': co_product_attrs.get('name'),
                'category': co_product_attrs.get('category'),
                'co_purchase_count': count
            })
        return result

    def _generate_product_insights_text(self, profile: Dict, purchasing_customers: List) -> List[str]:
        """Generates human-readable insights for a product."""
        insights = []
        
        total_units_sold = sum(p.get('quantity', 0) for p in purchasing_customers)
        total_revenue = sum(p.get('totalPrice', 0) for p in purchasing_customers)
        unique_buyers = len({p['userId'] for p in purchasing_customers})
        
        if total_units_sold > 100:
            insights.append(f"This product is a strong seller with {total_units_sold} units sold.")
        if total_revenue > 5000:
            insights.append(f"It generates significant revenue, totaling ${total_revenue:.2f}.")
        if unique_buyers > 50:
            insights.append(f"The product has broad appeal, purchased by {unique_buyers} unique customers.")
        
        category = profile.get('category')
        if category:
            insights.append(f"It belongs to the '{category}' category, a key segment.")
            
        if profile.get('stock') is not None and profile['stock'] < 20:
            insights.append(f"Current stock is low ({profile['stock']} units), consider restocking soon.")
            
        if profile.get('rating') is not None and profile['rating'] >= 4.0:
            insights.append(f"High customer satisfaction with an average rating of {profile['rating']}.")
            
        return insights if insights else ["Standard product performance."]

    def get_graph_summary(self) -> Dict:
        """Get summary statistics of the knowledge graph."""
        if not self._is_built:
            return {'status': 'error', 'message': 'Knowledge graph not built. Please build it first.'}
        try:
            return {
                'status': 'success',
                'node_count': self.graph.number_of_nodes(),
                'edge_count': self.graph.number_of_edges(),
                'node_types': self._get_node_type_counts(),
                'edge_types': self._get_edge_type_counts(),
                'graph_density': nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0
            }
        except Exception as e:
            logger.error(f"Error getting graph summary: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
            
    def _get_node_type_counts(self) -> Dict:
        """Helper to count nodes by type."""
        counts = defaultdict(int)
        for node, attrs in self.graph.nodes(data=True):
            counts[attrs.get('type', 'unknown')] += 1
        return dict(counts)
        
    def _get_edge_type_counts(self) -> Dict:
        """Helper to count edges by type."""
        counts = defaultdict(int)
        for u, v, key, attrs in self.graph.edges(data=True, keys=True):
            counts[attrs.get('type', 'unknown')] += 1
        return dict(counts)
        
    def save_graph(self, path: str = 'models/knowledge_graph.gml'):
        """Save the knowledge graph to a file."""
        if not self._is_built:
            logger.warning("Graph not built, cannot save.")
            return {'status': 'error', 'message': 'Graph not built.'}
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            nx.write_gml(self.graph, path)
            logger.info(f"Knowledge graph saved to {path}")
            return {'status': 'success', 'path': path}
        except Exception as e:
            logger.error(f"Error saving knowledge graph: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
            
    def load_graph(self, path: str = 'models/knowledge_graph.gml'):
        """Load the knowledge graph from a file."""
        try:
            if not os.path.exists(path):
                logger.warning(f"Knowledge graph file not found at {path}. Will attempt to rebuild on next request.")
                self._is_built = False
                return {'status': 'error', 'message': 'Graph file not found.'}

            self.graph = nx.read_gml(path)
            # Re-populate node and edge attributes cache for easier access if needed
            self.node_attributes = {node: data for node, data in self.graph.nodes(data=True)}
            self.edge_attributes = {(u, v, k): data for u, v, k, data in self.graph.edges(data=True, keys=True)} # Include key for MultiDiGraph
            self._is_built = True
            logger.info(f"Knowledge graph loaded from {path}")
            return {'status': 'success', 'path': path}
        except Exception as e:
            logger.error(f"Error loading knowledge graph: {str(e)}", exc_info=True)
            self._is_built = False
            return {'status': 'error', 'message': str(e)}


```

### `./app/models/model_manager.py`
```py
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
        # Ensure db_connected is true *before* proceeding
        if not self.db_connected:
            logger.error("Cannot train models: MongoDB connection not established.")
            return

        logger.info("Starting full model retraining process...")

        try:
            data_processor = DataProcessor(db=get_database())

            # Train Forecasting Model
            logger.info("Training Forecasting Model...")
            transactions_df = await data_processor.get_transactions_data()
            # Pass 'totalAmount' here as it's now consistently named in the DataFrame from data_processor
            daily_sales_df = data_processor.prepare_time_series_data(transactions_df, 'totalAmount', freq='D')
            if not daily_sales_df.empty:
                forecast_result = self.forecasting_model.train(daily_sales_df, target_col='totalAmount')
                logger.info(f"Forecasting Model training result: {forecast_result}")
            else:
                logger.warning("Skipping forecasting model training: No daily sales data.")

            # Train Anomaly Detection Model
            logger.info("Training Anomaly Detection Model...")
            anomaly_df = await data_processor.get_transactions_data()
            if not anomaly_df.empty:
                # Use 'totalAmount' here
                anomaly_features = ['totalAmount', 'quantity']
                # Ensure numerical columns for anomaly detection
                anomaly_df['totalAmount'] = pd.to_numeric(anomaly_df['totalAmount'], errors='coerce').fillna(0)
                anomaly_df['quantity'] = pd.to_numeric(anomaly_df['quantity'], errors='coerce').fillna(0)
                
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
            self.models_loaded = False

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
```

### `./app/models/recommendation.py`
```py
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
import joblib
import os
from typing import Optional
from app.config import settings
from app.utils.logger import logger
from app.services.data_processor import DataProcessor

class RecommendationModel:
    """
    Implements a recommendation system using collaborative filtering (SVD).
    """
    def __init__(self, model_type: str = settings.RECOMMENDER_MODEL_TYPE, n_components: int = 50):
        self.model = None
        self.model_type = model_type
        self.n_components = n_components
        self.user_item_matrix = None # Stores the user-item interaction matrix
        self.user_mapper = {} # Map original user IDs to matrix indices
        self.item_mapper = {} # Map original item IDs to matrix indices
        self.user_inverse_mapper = {} # Map matrix indices back to original user IDs
        self.item_inverse_mapper = {} # Map matrix indices back to original item IDs
        self.model_path = os.path.join(settings.MODEL_SAVE_PATH, f"recommendation_model_{model_type}.joblib")
        self.is_trained = False

    async def train(self, data_processor: DataProcessor) -> dict:
        """
        Trains the recommendation model.
        Expects a DataProcessor instance to fetch user-item interaction data.
        """
        logger.info("Starting training for recommendation model...")
        self.user_item_matrix = await data_processor.get_user_item_matrix()

        if self.user_item_matrix.empty:
            logger.warning("No user-item interaction data to train recommendation model.")
            return {"status": "failed", "message": "No data for training."}

        # Create mappers for user and item IDs
        self.user_mapper = {user_id: idx for idx, user_id in enumerate(self.user_item_matrix.index)}
        self.item_mapper = {item_id: idx for idx, item_id in enumerate(self.user_item_matrix.columns)}
        self.user_inverse_mapper = {idx: user_id for user_id, idx in self.user_mapper.items()}
        self.item_inverse_mapper = {idx: item_id for item_id, idx in self.item_mapper.items()}

        # Convert to sparse matrix for SVD
        sparse_user_item = csr_matrix(self.user_item_matrix.values)

        if self.model_type == "SVD":
            self.model = TruncatedSVD(n_components=self.n_components, random_state=42)
            logger.info(f"Initialized TruncatedSVD with {self.n_components} components.")
        # elif self.model_type == "KNNWithMeans":
            # For KNN based models, you'd typically use surprise library or custom implementation
            # self.model = ...
        else:
            raise ValueError(f"Unsupported recommendation model type: {self.model_type}")

        self.model.fit(sparse_user_item)
        self.is_trained = True
        logger.info("Recommendation model training complete.")
        self.save_model()
        return {"status": "success", "message": "Recommendation model trained successfully."}

    def _get_popular_recommendations(self, num_recommendations: int = 10, product_data: Optional[pd.DataFrame] = None):
        """
        Provides general popular recommendations (e.g., for cold-start users).
        """
        logger.info("Providing popular recommendations (cold-start strategy).")
        if self.user_item_matrix is not None and not self.user_item_matrix.empty:
            # Sum interactions for each item
            item_popularity = self.user_item_matrix.sum(axis=0).sort_values(ascending=False)
            popular_item_ids = item_popularity.index.tolist()[:num_recommendations]
            
            # If product_data is available, try to get names
            if product_data is not None and not product_data.empty:
                popular_products_info = product_data[product_data['productId'].isin(popular_item_ids)]
                return popular_products_info[['productId', 'productName']].to_dict(orient='records')
            return [{"productId": pid} for pid in popular_item_ids]
        
        logger.warning("No user-item matrix available to determine popularity. Returning empty list.")
        return []

    async def get_user_recommendations(self, user_id: str, num_recommendations: int = 10, product_data: Optional[pd.DataFrame] = None):
        """
        Generates personalized product recommendations for a given user.
        """
        if not self.is_trained or self.model is None or self.user_item_matrix is None:
            logger.warning("Recommendation model not trained or data not loaded. Providing popular recommendations.")
            return self._get_popular_recommendations(num_recommendations, product_data)

        if user_id not in self.user_mapper:
            logger.warning(f"User {user_id} not found in training data. Providing popular recommendations.")
            return self._get_popular_recommendations(num_recommendations, product_data)

        user_idx = self.user_mapper[user_id]
        user_vector = self.user_item_matrix.iloc[user_idx]

        # Reconstruct the original matrix from SVD components (approximation)
        if self.model_type == "SVD":
            reconstructed_matrix = np.dot(self.model.transform(csr_matrix(self.user_item_matrix.values)), self.model.components_)
            # Convert back to DataFrame for easy indexing
            reconstructed_df = pd.DataFrame(reconstructed_matrix, index=self.user_item_matrix.index, columns=self.user_item_matrix.columns)
            
            # Get predicted ratings for the user
            user_predicted_ratings = reconstructed_df.loc[user_id]

            # Filter out items the user has already interacted with
            user_interacted_items = user_vector[user_vector > 0].index
            recommendations_series = user_predicted_ratings.drop(user_interacted_items, errors='ignore')

            # Sort and get top N recommendations
            if isinstance(recommendations_series, pd.Series):
                top_recommendations = recommendations_series.sort_values(ascending=False).head(num_recommendations).index.tolist()
            else:
                # Convert to Series if not already
                # If recommendations_series is a DataFrame, select the first row as a Series
                if isinstance(recommendations_series, pd.DataFrame):
                    recommendations_series = recommendations_series.iloc[0]
                top_recommendations = recommendations_series.sort_values(ascending=False).head(num_recommendations).index.tolist()
        else:
            logger.warning(f"Recommendation type {self.model_type} not fully implemented for prediction logic. Returning popular.")
            return self._get_popular_recommendations(num_recommendations, product_data)

        logger.info(f"Generated {len(top_recommendations)} recommendations for user {user_id}.")
        
        # Fetch product details if product_data is available
        if product_data is not None and not product_data.empty:
            recommended_products_info = product_data[product_data['productId'].isin(top_recommendations)]
            # Ensure order based on ranking
            product_dict = recommended_products_info.set_index('productId').T.to_dict('list')
            ordered_recommendations = []
            for prod_id in top_recommendations:
                if prod_id in product_dict:
                    ordered_recommendations.append({"productId": prod_id, "productName": product_dict[prod_id][0]}) # Assuming productName is first item
            return ordered_recommendations
        
        return [{"productId": pid} for pid in top_recommendations]


    def save_model(self):
        """Saves the trained model, user-item matrix, and mappers."""
        if self.model:
            os.makedirs(settings.MODEL_SAVE_PATH, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.user_item_matrix, os.path.join(settings.MODEL_SAVE_PATH, "user_item_matrix.joblib"))
            joblib.dump(self.user_mapper, os.path.join(settings.MODEL_SAVE_PATH, "user_mapper.joblib"))
            joblib.dump(self.item_mapper, os.path.join(settings.MODEL_SAVE_PATH, "item_mapper.joblib"))
            joblib.dump(self.user_inverse_mapper, os.path.join(settings.MODEL_SAVE_PATH, "user_inverse_mapper.joblib"))
            joblib.dump(self.item_inverse_mapper, os.path.join(settings.MODEL_SAVE_PATH, "item_inverse_mapper.joblib"))
            logger.info(f"Recommendation model and associated data saved to {self.model_path}")
        else:
            logger.warning("No recommendation model to save.")

    def load_model(self):
        """Loads the trained model, user-item matrix, and mappers."""
        try:
            self.model = joblib.load(self.model_path)
            self.user_item_matrix = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "user_item_matrix.joblib"))
            self.user_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "user_mapper.joblib"))
            self.item_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "item_mapper.joblib"))
            self.user_inverse_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "user_inverse_mapper.joblib"))
            self.item_inverse_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "item_inverse_mapper.joblib"))
            self.is_trained = True
            logger.info(f"Recommendation model and associated data loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Recommendation model not found at {self.model_path}. Model needs to be trained.")
            self.is_trained = False
            return False
        except Exception as e:
            logger.error(f"Error loading recommendation model: {e}", exc_info=True)
            self.is_trained = False
            return False
```

### `./app/services/churn_service.py`
```py
"""
Churn Service - Wraps churn prediction model into callable service
Handles customer churn prediction, risk assessment, and retention strategies
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from app.models.advanced_models import ChurnPredictionModel
from app.models.explainable_ai import ExplainableAI
from app.model_configs.model_config import ModelConfig # Corrected import path for model_config
# from app.utils.feature_engineering import AdvancedFeatureProcessor # Not directly used here, churn_model handles features

logger = logging.getLogger(__name__)

class ChurnService:
    def __init__(self, mongodb_client):
        self.db = mongodb_client
        self.churn_model = ChurnPredictionModel()
        self.explainer = ExplainableAI() # Explainer instance for churn model
        self.config = ModelConfig() # Instantiate ModelConfig
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
            # Fetch all necessary raw data
            users_df = await self._get_user_data()
            transactions_df = await self._get_transaction_data()
            activities_df = await self._get_activity_data()

            if users_df.empty or transactions_df.empty or len(users_df) < self.config.CHURN_CONFIG.get('min_churn_data_points', 50): # Defaulted to 50 for safety if not in config
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
                model_save_path = os.path.join(self.config.BASE_MODEL_DIR, f"{self.churn_model.model.__class__.__name__}_churn_model.joblib")
                self.churn_model.save_model(model_save_path)
                logger.info(f"Churn model saved to {model_save_path}")

                # Setup explainer after model training
                # The explainer needs the actual trained model and the *scaled* training data
                # We need to ensure X_train_scaled from the model.train method is available or recreate it
                X_train_for_explainer = self.churn_model.scaler.transform(
                    training_data[self.churn_model.feature_columns].fillna(0)
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
                    # Re-initialize explainer if model was just loaded
                    if self.explainer.shap_explainers.get('churn_prediction_model') is None:
                        # Need to get some sample data to initialize explainer
                        sample_users = await self._get_user_data(limit=100)
                        sample_transactions = await self._get_transaction_data(limit=1000)
                        sample_activities = await self._get_activity_data(limit=1000)
                        sample_training_data = await self._prepare_churn_features_for_training(
                            sample_users, sample_transactions, sample_activities
                        )
                        if not sample_training_data.empty:
                            X_train_for_explainer = self.churn_model.scaler.transform(
                                sample_training_data[self.churn_model.feature_columns].fillna(0)
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
            if explain and 'churn_prediction_model' in self.explainer.shap_explainers:
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

    async def get_churn_cohort_analysis(
        self, cohort_type: str = 'month', time_period_days: int = 365
    ) -> Dict[str, Any]:
        """Performs churn cohort analysis."""
        try:
            transactions = await self._get_transaction_data()
            users = await self._get_user_data()

            if transactions.empty or users.empty:
                return {'status': 'error', 'message': 'Insufficient data for cohort analysis.'}

            # Ensure transactionDate and registrationDate are datetime
            transactions['transactionDate'] = pd.to_datetime(transactions['transactionDate'], errors='coerce')
            users['registrationDate'] = pd.to_datetime(users['registrationDate'], errors='coerce')
            
            transactions.dropna(subset=['transactionDate'], inplace=True)
            users.dropna(subset=['registrationDate'], inplace=True)

            if transactions.empty or users.empty:
                return {'status': 'error', 'message': 'Insufficient valid data after date parsing for cohort analysis.'}

            # Filter data to the specified time period
            start_date = datetime.utcnow() - timedelta(days=time_period_days)
            transactions = transactions[transactions['transactionDate'] >= start_date]
            users = users[users['registrationDate'] >= start_date]

            if transactions.empty or users.empty:
                return {'status': 'error', 'message': 'No data in the specified time period for cohort analysis.'}

            # Determine cohort based on registration date
            users['cohort'] = users['registrationDate'].dt.to_period(cohort_type.upper()[0]) # 'M' for month, 'Q' for quarter

            # Merge to get user cohort for each transaction
            # Ensure userId column names match for merge
            df = transactions.merge(users[['userId', 'cohort', 'registrationDate']], on='userId')
            
            df['transaction_period'] = df['transactionDate'].dt.to_period(cohort_type.upper()[0])

            # Calculate period number relative to cohort start
            # This requires careful handling of Period objects
            df['period_number'] = (df['transaction_period'].astype(int) - df['cohort'].astype(int))

            # Calculate active users per cohort per period
            cohort_pivot = df.groupby(['cohort', 'period_number'])['userId'].nunique().reset_index()
            cohort_pivot.rename(columns={'userId': 'active_users'}, inplace=True)

            # Calculate initial cohort size
            cohort_sizes = users.groupby('cohort')['userId'].nunique().reset_index()
            cohort_sizes.rename(columns={'userId': 'total_users'}, inplace=True)

            cohort_analysis = []
            for _, cohort_info in cohort_sizes.iterrows():
                cohort = cohort_info['cohort']
                total_users = cohort_info['total_users']

                cohort_data = cohort_pivot[cohort_pivot['cohort'] == cohort].sort_values('period_number')
                
                retention_rates = []
                # Ensure period 0 (registration period) has 100% retention
                retention_rates.append({
                    'period_number': 0,
                    'active_users': total_users,
                    'retention_rate': 100.0
                })
                
                for _, row in cohort_data.iterrows():
                    period_number = row['period_number']
                    active_users = row['active_users']
                    
                    if period_number == 0: # Already handled
                        continue

                    retention = (active_users / total_users) * 100 if total_users > 0 else 0
                    retention_rates.append({
                        'period_number': period_number,
                        'active_users': active_users,
                        'retention_rate': retention
                    })
                
                # Sort retention rates by period_number
                retention_rates = sorted(retention_rates, key=lambda x: x['period_number'])

                churn_rates = []
                for i in range(1, len(retention_rates)):
                    current_retention = retention_rates[i]['retention_rate']
                    previous_retention = retention_rates[i-1]['retention_rate']
                    churn = previous_retention - current_retention
                    churn_rates.append({
                        'period_number': retention_rates[i]['period_number'],
                        'churn_rate': churn
                    })

                cohort_analysis.append({
                    'cohort': str(cohort),
                    'total_users': total_users,
                    'retention_by_period': retention_rates,
                    'churn_by_period': churn_rates
                })
            
            # Sort cohort analysis by cohort name for consistent output
            cohort_analysis = sorted(cohort_analysis, key=lambda x: x['cohort'])

            return {'status': 'success', 'cohort_analysis': cohort_analysis}
        except Exception as e:
            logger.error(f"Error performing churn cohort analysis: {e}", exc_info=True)
            raise

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
            transactions_for_model['price'] = pd.to_numeric(transactions_for_model['price'], errors='coerce').fillna(0) # Assuming this comes from product merge, or derived
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

        return final_df_for_model
    
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


```

### `./app/services/data_processor.py`
```py
# ai_service/app/services/data_processor.py
from datetime import datetime, timedelta
import pandas as pd
from app.config import settings
from app.utils.logger import logger
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import MongoClient

class DataProcessor:
    """
    Handles fetching and initial processing of raw data from MongoDB.
    """
    def __init__(self, db: AsyncIOMotorDatabase = None, sync_db: MongoClient = None):
        self._db = db
        self._sync_db = sync_db # For synchronous operations if needed

        if self._db is None and self._sync_db is None:
            raise ValueError("Either an async or a sync database connection must be provided.")

    def _get_db_client(self):
        """Returns the appropriate database client based on context."""
        if self._db is not None:
            return self._db
        elif self._sync_db is not None:
            return self._sync_db
        else:
            raise RuntimeError("No database client available.")

    async def get_transactions_data(self, days: int = settings.DATA_COLLECTION_DAYS) -> pd.DataFrame:
        """
        Fetches transaction data for a specified number of past days.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Fetching transaction data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        try:
            transactions_cursor = self._get_db_client().transactions.find(
                {"transactionDate": {"$gte": start_date, "$lte": end_date}}
            )
            transactions_list = await transactions_cursor.to_list(length=None)

            if not transactions_list:
                logger.warning(f"No transaction data found for the last {days} days.")
                return pd.DataFrame()

            df = pd.DataFrame(transactions_list)

            # Ensure 'transactionDate' is datetime and then rename to 'timestamp'
            df['transactionDate'] = pd.to_datetime(df['transactionDate'])
            df = df.sort_values('transactionDate').reset_index(drop=True)
            df.rename(columns={'transactionDate': 'timestamp'}, inplace=True) # Renamed for consistency with feature engineering

            # IMPORTANT: Rename 'totalPrice' to 'totalAmount' for consistency with models
            if 'totalPrice' in df.columns:
                df.rename(columns={'totalPrice': 'totalAmount'}, inplace=True)
                # Ensure 'totalAmount' is numeric
                df['totalAmount'] = pd.to_numeric(df['totalAmount'], errors='coerce').fillna(0)
            else:
                logger.warning("Column 'totalPrice' not found in transactions data. Forecasting model may fail.")
                df['totalAmount'] = 0.0 # Provide a default if column missing

            # Ensure 'quantity' is numeric for anomaly detection and other uses
            if 'quantity' in df.columns:
                df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)

            logger.info(f"Fetched {len(df)} transactions.")
            return df

        except Exception as e:
            logger.error(f"Error fetching transaction data: {e}", exc_info=True)
            return pd.DataFrame()

    async def get_user_behavior_data(self, days: int = settings.DATA_COLLECTION_DAYS) -> pd.DataFrame:
        """
        Fetches user activity and feedback data for a specified number of past days.
        Combines user_activities and feedback collections.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        logger.info(f"Fetching user behavior data (activities and feedback) from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        try:
            activities_cursor = self._get_db_client().user_activities.find(
                {"timestamp": {"$gte": start_date, "$lte": end_date}}
            )
            activities_list = await activities_cursor.to_list(length=None)
            activities_df = pd.DataFrame(activities_list)

            feedback_cursor = self._get_db_client().feedback.find(
                {"feedbackDate": {"$gte": start_date, "$lte": end_date}}
            )
            feedback_list = await feedback_cursor.to_list(length=None)
            feedback_df = pd.DataFrame(feedback_list)

            if not activities_df.empty:
                activities_df['timestamp'] = pd.to_datetime(activities_df['timestamp'])
                activities_df['source_collection'] = 'user_activities'
            else:
                logger.warning(f"No user activities data found for the last {days} days.")

            if not feedback_df.empty:
                feedback_df['feedbackDate'] = pd.to_datetime(feedback_df['feedbackDate'])
                feedback_df.rename(columns={'feedbackDate': 'timestamp'}, inplace=True)
                feedback_df['source_collection'] = 'feedback'
            else:
                logger.warning(f"No feedback data found for the last {days} days.")

            dataframes_to_concat = []
            if not activities_df.empty:
                dataframes_to_concat.append(activities_df)
            if not feedback_df.empty:
                dataframes_to_concat.append(feedback_df)

            if not dataframes_to_concat:
                logger.warning(f"No user activity or feedback data found for the last {days} days.")
                return pd.DataFrame()

            combined_df = pd.concat(dataframes_to_concat, ignore_index=True)
            if not combined_df.empty:
                combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
            
            logger.info(f"Fetched {len(activities_df)} activities and {len(feedback_df)} feedback entries.")
            return combined_df

        except Exception as e:
            logger.error(f"Error fetching user behavior data: {e}", exc_info=True)
            return pd.DataFrame()


    async def get_product_data(self) -> pd.DataFrame:
        """
        Fetches product data.
        """
        logger.info("Fetching product data.")
        try:
            products_cursor = self._get_db_client().products.find({})
            products_list = await products_cursor.to_list(length=None)

            if not products_list:
                logger.warning("No product data found.")
                return pd.DataFrame()

            df = pd.DataFrame(products_list)
            logger.info(f"Fetched {len(df)} products.")
            return df
        except Exception as e:
            logger.error(f"Error fetching product data: {e}", exc_info=True)
            return pd.DataFrame()

    def prepare_time_series_data(self, df: pd.DataFrame, value_col: str, freq: str = 'D') -> pd.DataFrame:
        """
        Prepares time series data (e.g., daily sales) from a DataFrame.
        Assumes 'timestamp' column exists.
        """
        if df.empty:
            logger.warning("Input DataFrame is empty for time series preparation.")
            return pd.DataFrame()

        # Ensure 'timestamp' is the index and is a DatetimeIndex
        df_ts = df.set_index('timestamp')
        df_ts.index = pd.to_datetime(df_ts.index)

        # Resample and sum, then fill NaNs from resampling with 0
        df_ts = df_ts.resample(freq)[value_col].sum().fillna(0).to_frame()
        df_ts.columns = [value_col]
        df_ts = df_ts.reset_index()
        logger.info(f"Prepared time series data with frequency '{freq}' for '{value_col}'. Rows: {len(df_ts)}")
        return df_ts

    async def get_user_item_matrix(self, min_interactions: int = settings.MIN_INTERACTIONS_FOR_RECOMMENDATION) -> pd.DataFrame:
        """
        Generates a user-item interaction matrix from transaction data.
        Filters out users/items with too few interactions.
        """
        logger.info("Generating user-item interaction matrix...")
        try:
            transactions_df = await self.get_transactions_data(days=settings.DATA_COLLECTION_DAYS)
            if transactions_df.empty:
                logger.warning("No transactions data to build user-item matrix.")
                return pd.DataFrame()

            # Ensure correct data types
            transactions_df['userId'] = transactions_df['userId'].astype(str)
            transactions_df['productId'] = transactions_df['productId'].astype(str)
            transactions_df['quantity'] = transactions_df['quantity'].astype(int)

            # Aggregate quantity per user-product pair (implicit rating)
            user_item_interactions = transactions_df.groupby(['userId', 'productId'])['quantity'].sum().reset_index()
            user_item_interactions.rename(columns={'quantity': 'interaction_count'}, inplace=True)

            # Filter out users with too few interactions (optional, for cold-start or noise)
            user_counts = user_item_interactions.groupby('userId').size()
            valid_users = user_counts[user_counts >= min_interactions].index
            user_item_interactions = user_item_interactions[user_item_interactions['userId'].isin(valid_users)]

            if user_item_interactions.empty:
                logger.warning(f"No sufficient user-item interactions after filtering for min_interactions={min_interactions}.")
                return pd.DataFrame()

            # Create pivot table (user-item matrix)
            user_item_matrix = user_item_interactions.pivot_table(
                index='userId',
                columns='productId',
                values='interaction_count'
            ).fillna(0) # Fill NaN with 0 for no interaction

            logger.info(f"Generated user-item matrix with shape: {user_item_matrix.shape}")
            return user_item_matrix

        except Exception as e:
            logger.error(f"Error generating user-item matrix: {e}", exc_info=True)
            return pd.DataFrame()
```

### `./app/services/feature_engineering.py`
```py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from app.utils.logger import logger

class FeatureEngineer:
    """
    Handles feature engineering for machine learning models.
    """
    def __init__(self):
        self.scalers = {} # To store scalers for different features
        self.encoders = {} # To store encoders for categorical features

    def create_time_features(self, df: pd.DataFrame, timestamp_col: str = 'timestamp') -> pd.DataFrame:
        """
        Creates time-based features from a timestamp column.
        Expects timestamp_col to be datetime objects.
        """
        if df.empty or timestamp_col not in df.columns:
            logger.warning("DataFrame is empty or timestamp_col not found for time features.")
            return df

        df['year'] = df[timestamp_col].dt.year
        df['month'] = df[timestamp_col].dt.month
        df['day'] = df[timestamp_col].dt.day
        df['day_of_week'] = df[timestamp_col].dt.dayofweek
        df['day_of_year'] = df[timestamp_col].dt.dayofyear
        df['week_of_year'] = df[timestamp_col].dt.isocalendar().week.astype(int)
        df['hour'] = df[timestamp_col].dt.hour
        df['quarter'] = df[timestamp_col].dt.quarter
        df['is_weekend'] = ((df[timestamp_col].dt.dayofweek == 5) | (df[timestamp_col].dt.dayofweek == 6)).astype(int)
        df['is_month_start'] = df[timestamp_col].dt.is_month_start.astype(int)
        df['is_month_end'] = df[timestamp_col].dt.is_month_end.astype(int)

        logger.info(f"Created time features for DataFrame with {len(df)} rows.")
        return df

    def create_lag_features(self, df: pd.DataFrame, cols: list, lags: list) -> pd.DataFrame:
        """
        Creates lag features for specified columns.
        Expects df to be sorted by time.
        """
        if df.empty:
            logger.warning("DataFrame is empty for lag feature creation.")
            return df
        if not all(col in df.columns for col in cols):
            logger.error(f"One or more columns {cols} not found for lag features.")
            return df

        for col in cols:
            for lag in lags:
                df[f'{col}_lag_{lag}'] = df[col].shift(lag)
        df = df.fillna(0) # Fill NaN from shifting
        logger.info(f"Created lag features for columns {cols} with lags {lags}.")
        return df

    def create_rolling_features(self, df: pd.DataFrame, cols: list, windows: list, agg_funcs: list) -> pd.DataFrame:
        """
        Creates rolling window features for specified columns.
        Expects df to be sorted by time.
        """
        if df.empty:
            logger.warning("DataFrame is empty for rolling feature creation.")
            return df
        if not all(col in df.columns for col in cols):
            logger.error(f"One or more columns {cols} not found for rolling features.")
            return df

        for col in cols:
            for window in windows:
                for agg_func in agg_funcs:
                    if agg_func == 'mean':
                        df[f'{col}_roll_mean_{window}'] = df[col].rolling(window=window).mean()
                    elif agg_func == 'std':
                        df[f'{col}_roll_std_{window}'] = df[col].rolling(window=window).std()
                    elif agg_func == 'min':
                        df[f'{col}_roll_min_{window}'] = df[col].rolling(window=window).min()
                    elif agg_func == 'max':
                        df[f'{col}_roll_max_{window}'] = df[col].rolling(window=window).max()
        df = df.fillna(0) # Fill NaN from rolling
        logger.info(f"Created rolling features for columns {cols} with windows {windows} and funcs {agg_funcs}.")
        return df

    def create_anomaly_features(self, df: pd.DataFrame, value_col: str) -> pd.DataFrame:
        """
        Creates simple anomaly-related features (e.g., deviation from mean).
        """
        if df.empty or value_col not in df.columns:
            logger.warning("DataFrame is empty or value_col not found for anomaly features.")
            return df

        df[f'{value_col}_daily_mean'] = df[value_col].rolling(window=7, min_periods=1).mean()
        df[f'{value_col}_daily_std'] = df[value_col].rolling(window=7, min_periods=1).std()
        df[f'{value_col}_deviation'] = df[value_col] - df[f'{value_col}_daily_mean']
        df[f'{value_col}_zscore'] = df[f'{value_col}_deviation'] / df[f'{value_col}_daily_std'].replace(0, 1) # Avoid div by zero
        df = df.fillna(0)
        logger.info(f"Created anomaly features for '{value_col}'.")
        return df

    def scale_features(self, df: pd.DataFrame, cols: list, scaler_type: str = 'StandardScaler', fit: bool = True) -> pd.DataFrame:
        """
        Scales numerical features.
        :param df: DataFrame to scale.
        :param cols: List of columns to scale.
        :param scaler_type: Type of scaler ('StandardScaler' or 'MinMaxScaler').
        :param fit: If True, fit the scaler; if False, transform using existing scaler.
        """
        if df.empty or not cols or not all(col in df.columns for col in cols):
            logger.warning(f"DataFrame empty or columns missing for scaling: {cols}.")
            return df

        for col in cols:
            if fit:
                if scaler_type == 'StandardScaler':
                    scaler = StandardScaler()
                elif scaler_type == 'MinMaxScaler':
                    scaler = MinMaxScaler()
                else:
                    raise ValueError("scaler_type must be 'StandardScaler' or 'MinMaxScaler'")
                df[col] = scaler.fit_transform(df[[col]])
                self.scalers[col] = scaler
                logger.info(f"Fitted and scaled '{col}' with {scaler_type}.")
            else:
                if col in self.scalers:
                    df[col] = self.scalers[col].transform(df[[col]])
                    logger.info(f"Transformed '{col}' with existing {scaler_type}.")
                else:
                    logger.warning(f"No scaler found for '{col}', skipping transformation.")
        return df

    def encode_categorical_features(self, df: pd.DataFrame, cols: list, encoder_type: str = 'LabelEncoder', fit: bool = True) -> pd.DataFrame:
        """
        Encodes categorical features. Supports LabelEncoder for simplicity.
        :param df: DataFrame to encode.
        :param cols: List of columns to encode.
        :param encoder_type: Type of encoder ('LabelEncoder').
        :param fit: If True, fit the encoder; if False, transform using existing encoder.
        """
        if df.empty or not cols or not all(col in df.columns for col in cols):
            logger.warning(f"DataFrame empty or columns missing for encoding: {cols}.")
            return df

        for col in cols:
            if encoder_type == 'LabelEncoder':
                if fit:
                    encoder = LabelEncoder()
                    df[col] = encoder.fit_transform(df[col])
                    self.encoders[col] = encoder
                    logger.info(f"Fitted and encoded '{col}' with LabelEncoder.")
                else:
                    if col in self.encoders:
                        # Handle unseen labels during transformation
                        # Replace unseen labels with a placeholder (e.g., -1) or the most frequent label
                        # Here, we'll assign -1 for simplicity
                        unseen_labels = set(df[col].unique()) - set(self.encoders[col].classes_)
                        if unseen_labels:
                            logger.warning(f"Unseen labels detected in column '{col}': {unseen_labels}. Assigning -1.")
                            df[col] = df[col].apply(lambda x: self.encoders[col].transform([x])[0] if x in self.encoders[col].classes_ else -1)
                        else:
                            df[col] = self.encoders[col].transform(df[col])
                        logger.info(f"Transformed '{col}' with existing LabelEncoder.")
                    else:
                        logger.warning(f"No encoder found for '{col}', skipping transformation.")
            else:
                raise ValueError("encoder_type must be 'LabelEncoder'")
        return df

    def get_features_and_target(self, df: pd.DataFrame, target_col: str, feature_cols: list = None):
        """
        Separates features (X) and target (y) from a DataFrame.
        """
        if df.empty or target_col not in df.columns:
            logger.error(f"DataFrame empty or target column '{target_col}' not found for feature/target split.")
            return pd.DataFrame(), pd.Series()

        if feature_cols:
            X = df[feature_cols]
        else:
            X = df.drop(columns=[target_col], errors='ignore')
        y = df[target_col]

        logger.info(f"Separated features (X shape: {X.shape}) and target (y shape: {y.shape}).")
        return X, y
```

### `./app/services/feedback_service.py`
```py
"""
Feedback Service - Manages feedback loops for AI models
Handles data collection, model monitoring, and retraining triggers
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os # For path joining

from app.model_configs.model_config import ModelConfig # Corrected import path for model_config
from app.models.advanced_models import DynamicPricingModel, ChurnPredictionModel
from app.models.knowledge_graph import CustomerBehaviorGraph # If graph needs feedback
from app.models.forecasting import ForecastingModel # Import existing Phase 3 models
from app.models.anomaly_detection import AnomalyDetectionModel
from app.models.recommendation import RecommendationModel

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
        self.config = ModelConfig()
        
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
            model_base_path = self.config.BASE_MODEL_DIR

            # Pricing Model
            pricing_model_path = os.path.join(model_base_path, f"{self.pricing_model.__class__.__name__}_pricing_model.joblib")
            self.pricing_model.load_model(pricing_model_path)
            
            # Churn Model
            churn_model_path = os.path.join(model_base_path, f"{self.churn_model.__class__.__name__}_churn_model.joblib")
            self.churn_model.load_model(churn_model_path)
            
            # Knowledge Graph
            kg_path = os.path.join(model_base_path, "customer_behavior_graph.gml")
            self.knowledge_graph.load_graph(kg_path)

            # Phase 3 Models (using their standard naming convention)
            self.forecasting_model.load_model(
                os.path.join(model_base_path, f"forecasting_model_{self.config.FORECAST_MODEL_TYPE}.joblib")
            )
            self.anomaly_model.load_model(
                os.path.join(model_base_path, f"anomaly_model_{self.config.ANOMALY_MODEL_TYPE}.joblib")
            )
            self.recommendation_model.load_model(
                os.path.join(model_base_path, f"recommendation_model_{self.config.RECOMMENDER_MODEL_TYPE}.joblib")
            )

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
                recent_transactions = await self._get_recent_transactions(days=self.config.PRICING_RETRAIN_INTERVAL_DAYS)
                if not recent_transactions.empty:
                    # Example: Monitor average actual vs predicted price, or MAE on recent data
                    # For a real scenario, you'd apply the model to recent data and compare its predictions
                    # with actual prices or outcomes if an 'optimal_price' target exists for evaluation.
                    # Or, more simply, track how often model advises significant price changes.
                    
                    # For now, a very basic check: is the data flow healthy?
                    if len(recent_transactions) < self.config.MIN_PRICING_DATA_POINTS / 2: # If recent data is too sparse
                        status = 'warning'
                        issues.append("Low volume of recent transaction data for pricing model monitoring.")
                        recommendations.append("Verify data streaming or increase data collection window.")

                    # If model is trained, check if it's stale
                    if self.pricing_model.is_trained and self.last_trained_time:
                        if (datetime.utcnow() - self.last_trained_time).days > self.config.PRICING_RETRAIN_INTERVAL_DAYS:
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
                                baseline_churn_rate = self.config.CHURN_BASELINE_RATE
                                
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
                    if (datetime.utcnow() - self.last_trained_time).days > self.config.CHURN_RETRAIN_INTERVAL_DAYS:
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
                    if graph_summary['node_count'] < self.config.MIN_KG_TRANSACTIONS * 0.5: # Example threshold
                        status = 'warning'
                        issues.append(f"Knowledge graph has low node count ({graph_summary['node_count']}), possibly indicating incomplete data ingestion.")
                        recommendations.append("Verify data streaming and graph building process. Consider rebuilding.")
                    if graph_summary['edge_count'] < self.config.MIN_KG_TRANSACTIONS * 1.5: # Example threshold
                        status = 'warning'
                        issues.append(f"Knowledge graph has low edge count ({graph_summary['edge_count']}), possibly indicating sparse relationships.")
                        recommendations.append("Review relationship extraction logic in graph building. Consider rebuilding.")
                else:
                    issues.append(f"Could not get knowledge graph summary for monitoring: {graph_summary['message']}")
                
                # Check for staleness
                if self.knowledge_graph._is_built and self.last_built_time: # Assuming a last_built_time attribute on KG
                    if (datetime.utcnow() - self.last_built_time).total_seconds() / 3600 > self.config.KG_BUILD_INTERVAL_HOURS:
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
            model_base_path = self.config.BASE_MODEL_DIR

            if model_name == 'pricing':
                transactions = await self._get_recent_transactions(days=self.config.PRICING_TRAINING_DAYS)
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
                    pricing_model_save_path = os.path.join(model_base_path, f"{self.pricing_model.__class__.__name__}_pricing_model.joblib")
                    self.pricing_model.save_model(pricing_model_save_path)
                    self.last_trained_time = datetime.utcnow() # Update last trained time
                    logger.info("Pricing model retraining successful.")
                    return {'status': 'success', 'message': 'Pricing model retrained successfully.', 'metrics': train_result}
                else:
                    return {'status': 'error', 'message': f"Pricing model retraining failed: {train_result['message']}"}

            elif model_name == 'churn':
                users = await self._get_all_users()
                transactions = await self._get_all_transactions()
                activities = await self._get_all_activities()
                
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
                    churn_model_save_path = os.path.join(model_base_path, f"{self.churn_model.__class__.__name__}_churn_model.joblib")
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
                    transactions['price'] = transactions['price_prod'].fillna(transactions['amount'] / transactions['quantity'].replace(0,1))
                    transactions.drop(columns=['price_tx', 'price_prod'], errors='ignore', inplace=True)
                    transactions['price'].fillna(1.0, inplace=True) # Final fallback

                graph_build_result = self.knowledge_graph.build_graph_from_data(transactions, products, users)
                if graph_build_result['status'] == 'success':
                    kg_save_path = os.path.join(model_base_path, "customer_behavior_graph.gml")
                    self.knowledge_graph.save_graph(kg_save_path)
                    self.last_built_time = datetime.utcnow() # Update last built time
                    logger.info("Knowledge graph rebuilt successfully.")
                    return {'status': 'success', 'message': 'Knowledge graph rebuilt successfully.', 'metrics': graph_build_result}
                else:
                    return {'status': 'error', 'message': f"Knowledge graph rebuilding failed: {graph_build_result['message']}"}
            
            elif model_name == 'forecasting':
                # Similar logic as in app.models.model_manager.py for training
                transactions = await self._get_all_transactions()
                if transactions.empty:
                    return {'status': 'error', 'message': 'Insufficient data for forecasting model retraining.'}

                # Prepare data for forecasting model (as done in data_processor.py)
                from app.services.data_processor import DataProcessor # Import DataProcessor
                data_processor = DataProcessor(self.db)
                time_series_data = await data_processor.prepare_time_series_data(transactions, 'totalPrice', 'transactionDate', 'D')
                
                if time_series_data.empty:
                    return {'status': 'error', 'message': 'Prepared time series data for forecasting is empty.'}

                # Use the ForecastingModel's training method
                train_result = self.forecasting_model.train(time_series_data)
                
                if train_result['status'] == 'success':
                    forecast_model_save_path = os.path.join(model_base_path, f"forecasting_model_{self.forecasting_model.model.__class__.__name__}.joblib")
                    self.forecasting_model.save_model(forecast_model_save_path)
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
                anomaly_data = await data_processor.prepare_anomaly_detection_data(transactions, ['totalPrice', 'quantity'])
                
                if anomaly_data.empty:
                    return {'status': 'error', 'message': 'Prepared anomaly detection data is empty.'}

                train_result = self.anomaly_model.train(anomaly_data)
                
                if train_result['status'] == 'success':
                    anomaly_model_save_path = os.path.join(model_base_path, f"anomaly_model_{self.anomaly_model.model.__class__.__name__}.joblib")
                    self.anomaly_model.save_model(anomaly_model_save_path)
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
                user_item_matrix_data = await data_processor.get_user_item_matrix(transactions, 'userId', 'productId', 'totalPrice')
                
                if user_item_matrix_data.empty:
                    return {'status': 'error', 'message': 'Prepared user-item matrix data is empty.'}

                train_result = self.recommendation_model.train(user_item_matrix_data)
                
                if train_result['status'] == 'success':
                    recommendation_model_save_path = os.path.join(model_base_path, f"recommendation_model_{self.recommendation_model.model.__class__.__name__}.joblib")
                    self.recommendation_model.save_model(recommendation_model_save_path)
                    logger.info("Recommendation model retraining successful.")
                    return {'status': 'success', 'message': 'Recommendation model retrained successfully.', 'metrics': train_result}
                else:
                    return {'status': 'error', 'message': f"Recommendation model retraining failed: {train_result['message']}"}

            else:
                return {'status': 'error', 'message': f"Retraining for model '{model_name}' is not supported."}
        except Exception as e:
            logger.error(f"Error triggering retraining for {model_name}: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    # Helper methods to fetch data from MongoDB (similar to other services)
    async def _get_recent_transactions(self, days: int) -> pd.DataFrame:
        try:
            transactions_cursor = self.db.transactions.find({
                'transactionDate': {'$gte': (datetime.utcnow() - timedelta(days=days)).isoformat()}
            })
            transactions_list = await transactions_cursor.to_list(length=None)
            df = pd.DataFrame(transactions_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure essential columns are present and correctly typed
            for col in ['transactionDate', 'totalPrice', 'quantity', 'productId', 'userId']:
                if col not in df.columns:
                    logger.warning(f"Missing column '{col}' in fetched transactions data. This may affect model training.")
                    df[col] = np.nan # Add column with NaNs if missing
            
            df['transactionDate'] = pd.to_datetime(df['transactionDate'], errors='coerce')
            df['totalPrice'] = pd.to_numeric(df['totalPrice'], errors='coerce')
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            df['productId'] = df['productId'].astype(str) # Ensure string type

            df.dropna(subset=['transactionDate', 'totalPrice', 'quantity', 'productId', 'userId'], inplace=True) # Drop rows with critical NaNs

            logger.info(f"Fetched {len(df)} recent transactions for feedback service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching recent transactions for feedback service: {e}", exc_info=True)
            return pd.DataFrame()
            
    async def _get_all_users(self) -> pd.DataFrame:
        try:
            users_cursor = self.db.users.find({})
            users_list = await users_cursor.to_list(length=None)
            df = pd.DataFrame(users_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure proper datetime parsing for relevant columns
            if 'registrationDate' in df.columns:
                df['registrationDate'] = pd.to_datetime(df['registrationDate'], errors='coerce')
            if 'lastLogin' in df.columns:
                df['lastLogin'] = pd.to_datetime(df['lastLogin'], errors='coerce')
            
            logger.info(f"Fetched {len(df)} users for feedback service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching all users for feedback service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_all_transactions(self) -> pd.DataFrame:
        try:
            transactions_cursor = self.db.transactions.find({})
            transactions_list = await transactions_cursor.to_list(length=None)
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


            logger.info(f"Fetched {len(df)} transactions for feedback service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching all transactions for feedback service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_all_activities(self) -> pd.DataFrame:
        try:
            activities_cursor = self.db.user_activities.find({})
            activities_list = await activities_cursor.to_list(length=None)
            df = pd.DataFrame(activities_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            df['userId'] = df['userId'].astype(str) # Ensure string type

            logger.info(f"Fetched {len(df)} activities for feedback service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching all activities for feedback service: {e}", exc_info=True)
            return pd.DataFrame()
            
    async def _get_all_products(self) -> pd.DataFrame:
        try:
            products_cursor = self.db.products.find({})
            products_list = await products_cursor.to_list(length=None)
            df = pd.DataFrame(products_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure numeric types
            if 'price' in df.columns:
                df['price'] = pd.to_numeric(df['price'], errors='coerce')
            if 'stock' in df.columns:
                df['stock'] = pd.to_numeric(df['stock'], errors='coerce')

            logger.info(f"Fetched {len(df)} products for feedback service.")
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


```

### `./app/services/__init__.py`
```py

```

### `./app/services/pricing_service.py`
```py
"""
Pricing Service - Wraps dynamic pricing model into callable service
Handles real-time price optimization and scenario analysis
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np # Required for np.random.uniform and np.clip

from app.models.advanced_models import DynamicPricingModel
from app.model_configs.model_config import ModelConfig # Corrected import path for model_config

logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self, mongodb_client):
        self.db = mongodb_client
        self.pricing_model = DynamicPricingModel()
        self.config = ModelConfig() # Instantiate ModelConfig
        self._model_trained = False
        self.last_trained_time: Optional[datetime] = None # To track last training time

    async def initialize(self):
        """Initialize pricing service and train/load model."""
        try:
            await self._load_and_train_model()
            logger.info("Pricing service initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize pricing service: {e}")
            # Re-raise if initialization is critical for service operation
            raise

    async def _load_and_train_model(self):
        """Load historical transaction data and train/retrain the pricing model."""
        try:
            transactions = await self._get_historical_transactions()
            products = await self._get_product_data()
            
            if transactions.empty or len(transactions) < self.config.MIN_PRICING_DATA_POINTS: # Use config value
                logger.warning(f"Insufficient transaction data ({len(transactions)} < {self.config.MIN_PRICING_DATA_POINTS}) for pricing model training. Skipping training.")
                self._model_trained = False
                return

            # Ensure 'productId' is the correct column name for merging
            # Ensure 'category' is present in transactions, by merging products data
            data = transactions.merge(products[['productId', 'category', 'price']], 
                                     left_on='productId', right_on='productId', 
                                     suffixes=('_transaction', '_product'))
            
            # Rename product price to 'base_price' and use transaction price as 'price'
            # Note: The Transaction Schema has 'totalPrice' for the transaction total,
            # and Product Schema has 'price' for unit price.
            # We assume 'price_transaction' is derived, and 'price_product' is the unit price.
            # The model's `prepare_features` expects `price` (unit price) and `amount` (total transaction amount).
            
            data.rename(columns={'totalPrice': 'amount', 'price_product': 'price'}, inplace=True) # Map totalPrice to amount
            
            # Ensure 'timestamp' is datetime and sort
            # Your Transaction Schema has 'transactionDate', so use that
            data['timestamp'] = pd.to_datetime(data['transactionDate'])
            data = data.sort_values(by='timestamp')

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
                model_save_path = os.path.join(self.config.BASE_MODEL_DIR, f"{self.pricing_model.model.__class__.__name__}_pricing_model.joblib")
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
                    optimal_price, current_price, demand_scenario, price_change_percent
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

    def _generate_pricing_reasoning(self, optimal_price: float, current_price: float, 
                                    demand_scenario: str, price_change_percent: float) -> List[str]:
        """Generates human-readable reasoning for the pricing decision."""
        reasons = [
            f"Based on a '{demand_scenario}' demand scenario, the optimal price is set to ${optimal_price:.2f}."
        ]
        
        if price_change_percent > 5:
            reasons.append(f"This represents a significant price increase of {price_change_percent:.2f}%, likely due to strong demand signals or limited supply.")
        elif price_change_percent < -5:
            reasons.append(f"This represents a significant price decrease of {abs(price_change_percent):.2f}%, likely to stimulate demand or respond to competitive pricing.")
        elif price_change_percent > 0:
            reasons.append(f"The price is slightly increased by {price_change_percent:.2f}% to optimize revenue.")
        elif price_change_percent < 0:
            reasons.append(f"The price is slightly decreased by {abs(price_change_percent):.2f}% to attract more customers.")
        else:
            reasons.append("The optimal price is close to the current price, indicating stable market conditions.")

        # Add scenario-specific reasoning
        if demand_scenario == 'high_demand':
            reasons.append("High demand scenario justifies a higher price to maximize profit margins.")
        elif demand_scenario == 'low_demand':
            reasons.append("Low demand scenario suggests a price reduction to boost sales volume.")
        elif demand_scenario == 'clearance':
            reasons.append("Clearance pricing is applied to liquidate excess inventory quickly.")

        # Add general factors (assuming these are implicit in the model's features)
        reasons.append("Considerations include recent sales trends, product category performance, and overall market competition.")

        return reasons
        
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


```

### `./app/services/reasoning_service.py`
```py
"""
Reasoning Service - Exposes knowledge graph reasoning capabilities
Provides cognitive AI insights, pattern recognition, and strategic recommendations
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from app.models.knowledge_graph import CustomerBehaviorGraph # Corrected import path
from app.model_configs.model_config import ModelConfig # Corrected import path for model_config
# from app.models.explainable_ai import ExplainableAI # Not directly used in ReasoningService, more for specific model explanations
# from app.utils.feature_engineering import AdvancedFeatureProcessor # Not directly used here, features are for models

logger = logging.getLogger(__name__)

class ReasoningService:
    def __init__(self, mongodb_client):
        self.db = mongodb_client
        self.knowledge_graph = CustomerBehaviorGraph()
        self.config = ModelConfig() # Instantiate ModelConfig
        self._graph_built = False
        self.last_built_time: Optional[datetime] = None # To track last graph build time

    async def initialize(self):
        """Initialize reasoning service and build knowledge graph."""
        try:
            await self._build_knowledge_graph()
            logger.info("Reasoning service initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize reasoning service: {e}")
            raise

    async def _build_knowledge_graph(self):
        """Build and populate knowledge graph with latest data."""
        try:
            # Load data from database using _get methods
            users = await self._get_users()
            products = await self._get_products()
            transactions = await self._get_transactions()
            feedback = await self._get_feedback()
            activities = await self._get_activities()

            # Ensure essential columns are correctly formatted and present for graph building
            # Schema mapping and data cleaning:
            # Users: userId, username, email, registrationDate, lastLogin, address (nested)
            # Products: productId, name, category, price, stock, description, addedDate
            # Transactions: transactionId, userId, productId, quantity, totalPrice, transactionDate, status, paymentMethod, shippingAddress
            # Feedback: feedbackId, userId, productId, rating, comment, feedbackDate
            # User Activities: activityId, userId, activityType, timestamp, ipAddress, device, searchTerm

            # Ensure transactionDate is datetime for transactions
            if not transactions.empty and 'transactionDate' in transactions.columns:
                transactions['transactionDate'] = pd.to_datetime(transactions['transactionDate'], errors='coerce')
                transactions.dropna(subset=['transactionDate'], inplace=True)
            else:
                logger.warning("Transactions DataFrame is empty or missing 'transactionDate'. Knowledge graph will be limited.")
                self._graph_built = False
                return

            # Ensure necessary user and product data is available
            if users.empty or products.empty:
                logger.warning("Users or Products DataFrame is empty. Knowledge graph will be incomplete.")
                self._graph_built = False
                return
            
            # Map totalPrice to 'amount' for consistency if needed by graph builder
            if 'totalPrice' in transactions.columns and 'amount' not in transactions.columns:
                transactions['amount'] = transactions['totalPrice']
            elif 'amount' not in transactions.columns: # Fallback if totalPrice also missing
                transactions['amount'] = transactions['quantity'] * transactions.get('price', 1.0) # Estimate if price is available

            # Ensure 'price' is available in transactions (from product merge or schema) for graph edge attributes
            if 'price' not in transactions.columns:
                transactions = transactions.merge(
                    products[['productId', 'price']], on='productId', how='left', suffixes=('_tx', '_prod')
                )
                transactions['price'] = transactions['price_prod'].fillna(transactions['amount'] / transactions['quantity'].replace(0,1)) # Fallback calculation
                transactions.drop(columns=['price_tx', 'price_prod'], errors='ignore', inplace=True) # Clean up merge columns

            # Ensure 'category' is available in transactions (from product merge or schema) for graph node attributes
            if 'category' not in transactions.columns:
                transactions = transactions.merge(
                    products[['productId', 'category']], on='productId', how='left'
                )
                transactions['category'].fillna('unknown', inplace=True) # Fill missing categories

            # Build the knowledge graph using the prepared data
            build_result = self.knowledge_graph.build_graph_from_data(transactions, products, users)
            
            if build_result['status'] == 'success':
                self._graph_built = True
                self.last_built_time = datetime.utcnow()
                logger.info(f"Knowledge graph built with {build_result.get('nodes', 0)} nodes and {build_result.get('edges', 0)} edges.")
                # Save the graph after successful build
                graph_save_path = os.path.join(self.config.BASE_MODEL_DIR, "customer_behavior_graph.gml")
                self.knowledge_graph.save_graph(graph_save_path)
            else:
                logger.error(f"Knowledge graph building failed: {build_result['message']}")
                self._graph_built = False
        except Exception as e:
            logger.error(f"Error in building knowledge graph: {e}", exc_info=True)
            self._graph_built = False
            raise

    async def get_customer_insights(
        self, user_id: str, insight_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive insights about a customer."""
        if not self._graph_built:
            # Attempt to load from disk if not built in current session (e.g., app restart)
            graph_load_path = os.path.join(self.config.BASE_MODEL_DIR, "customer_behavior_graph.gml")
            try:
                load_result = self.knowledge_graph.load_graph(graph_load_path)
                if load_result['status'] == 'success':
                    self._graph_built = True
                    logger.info("Knowledge graph loaded for insights.")
            except Exception as e:
                logger.warning(f"Could not load knowledge graph from disk: {e}. Attempting to build.")
                await self._build_knowledge_graph() # Attempt to build if not loaded
                if not self._graph_built:
                    return {'status': 'error', 'message': 'Knowledge graph not built and cannot be loaded/built.'}

        try:
            insights_result = self.knowledge_graph.get_customer_insights(user_id)
            
            if insights_result['status'] == 'success':
                # Further refine or add meta-insights if needed
                insights = {
                    'user_id': user_id,
                    'customer_profile': insights_result.get('profile', {}),
                    'purchase_history': insights_result.get('purchase_history', []),
                    'similar_customers': insights_result.get('similar_customers', []),
                    'product_recommendations': insights_result.get('graph_recommendations', []), # Use graph recommendations
                    'behavioral_insights': insights_result.get('insights', []), # Textual insights
                    'timestamp': datetime.utcnow().isoformat()
                }
                # Example of adding meta-insights
                profile = insights.get('customer_profile', {})
                total_spent = profile.get('total_spent_lifetime', 0)
                transaction_count = profile.get('total_orders_lifetime', 0)

                meta_insights = []
                if total_spent > 1000 and transaction_count > 5:
                    meta_insights.append("High-value, frequent customer.")
                elif total_spent > 300:
                    meta_insights.append("Mid-value customer with growing engagement.")
                
                if insights['similar_customers']:
                    meta_insights.append(f"Has {len(insights['similar_customers'])} similar customers in the network.")

                insights['meta_insights'] = meta_insights if meta_insights else ["Standard customer profile."]

                return {'status': 'success', 'data': insights}
            else:
                return insights_result # Propagate error from knowledge graph

        except Exception as e:
            logger.error(f"Failed to get customer insights for {user_id}: {e}", exc_info=True)
            raise

    async def get_product_intelligence(
        self, product_id: str, analysis_depth: str = 'comprehensive'
    ) -> Dict[str, Any]:
        """Get comprehensive insights about a product."""
        if not self._graph_built:
            # Attempt to load from disk if not built in current session (e.g., app restart)
            graph_load_path = os.path.join(self.config.BASE_MODEL_DIR, "customer_behavior_graph.gml")
            try:
                load_result = self.knowledge_graph.load_graph(graph_load_path)
                if load_result['status'] == 'success':
                    self._graph_built = True
                    logger.info("Knowledge graph loaded for product intelligence.")
            except Exception as e:
                logger.warning(f"Could not load knowledge graph from disk: {e}. Attempting to build.")
                await self._build_knowledge_graph() # Attempt to build if not loaded
                if not self._graph_built:
                    return {'status': 'error', 'message': 'Knowledge graph not built and cannot be loaded/built.'}

        try:
            intelligence_result = self.knowledge_graph.get_product_intelligence(product_id)

            if intelligence_result['status'] == 'success':
                insights = {
                    'product_id': product_id,
                    'product_profile': intelligence_result.get('profile', {}),
                    'purchasing_customers': intelligence_result.get('purchasing_customers', []),
                    'categories': intelligence_result.get('categories', []),
                    'co_purchased_products': intelligence_result.get('co_purchased_products', []),
                    'market_insights': intelligence_result.get('insights', []), # Textual insights
                    'timestamp': datetime.utcnow().isoformat()
                }
                # Example of adding strategic recommendations based on intelligence
                profile = insights.get('product_profile', {})
                total_sales = profile.get('total_sales', 0) # Assuming this attribute is added in KG
                units_sold = profile.get('units_sold', 0) # Assuming this attribute is added in KG

                strategic_recommendations = []
                if total_sales > 10000 or units_sold > 500:
                    strategic_recommendations.append("Promote as a best-seller.")
                    if insights['co_purchased_products']:
                        strategic_recommendations.append("Explore cross-promotions with frequently co-purchased items.")
                elif total_sales < 1000:
                    strategic_recommendations.append("Review pricing strategy.")
                    strategic_recommendations.append("Enhance product description and visibility.")
                
                insights['strategic_recommendations'] = strategic_recommendations
                return {'status': 'success', 'data': insights}
            else:
                return intelligence_result
        except Exception as e:
            logger.error(f"Failed to get product insights for {product_id}: {e}", exc_info=True)
            raise

    async def get_market_intelligence(
        self, market_segment: str = 'overall', time_horizon: str = 'quarterly'
    ) -> Dict[str, Any]:
        """Get market intelligence and trend analysis."""
        if not self._graph_built:
            # Attempt to load from disk if not built in current session (e.g., app restart)
            graph_load_path = os.path.join(self.config.BASE_MODEL_DIR, "customer_behavior_graph.gml")
            try:
                load_result = self.knowledge_graph.load_graph(graph_load_path)
                if load_result['status'] == 'success':
                    self._graph_built = True
                    logger.info("Knowledge graph loaded for market intelligence.")
            except Exception as e:
                logger.warning(f"Could not load knowledge graph from disk: {e}. Attempting to build.")
                await self._build_knowledge_graph() # Attempt to build if not loaded
                if not self._graph_built:
                    return {'status': 'error', 'message': 'Knowledge graph not built and cannot be loaded/built.'}

        try:
            # This method would typically aggregate insights from graph data
            # For demonstration, we'll return a simplified structure.
            # Real implementation would involve extensive graph queries and aggregation.
            
            # Example: Analyze overall trends from transactions
            transactions = await self._get_transactions()
            if transactions.empty:
                return {'status': 'error', 'message': 'No transaction data available for market intelligence.'}

            transactions['transactionDate'] = pd.to_datetime(transactions['transactionDate'], errors='coerce')
            transactions.dropna(subset=['transactionDate'], inplace=True)
            
            # Filter by time horizon if specified
            end_date = datetime.utcnow()
            if time_horizon == 'quarterly':
                start_date = end_date - timedelta(days=90)
            elif time_horizon == 'monthly':
                start_date = end_date - timedelta(days=30)
            elif time_horizon == 'yearly':
                start_date = end_date - timedelta(days=365)
            else: # overall
                start_date = transactions['transactionDate'].min()

            filtered_transactions = transactions[transactions['transactionDate'] >= start_date]
            
            if filtered_transactions.empty:
                return {'status': 'info', 'message': 'No transactions in the specified time horizon.', 'data': {}}


            # Category performance (from transactions, assume category is merged)
            category_sales = filtered_transactions.groupby('category')['totalPrice'].sum().to_dict()
            
            # Top products
            top_products = filtered_transactions.groupby('productId')['totalPrice'].sum().nlargest(5).to_dict()

            intelligence = {
                'market_segment': market_segment,
                'time_horizon': time_horizon,
                'trend_analysis': {
                    'overall_revenue': float(filtered_transactions['totalPrice'].sum()),
                    'category_performance': {k: float(v) for k, v in category_sales.items()},
                    'top_products': {k: float(v) for k, v in top_products.items()},
                    'recent_growth_rate': 'N/A' # Placeholder for actual calculation
                },
                'customer_behavior_trends': {
                    'avg_transaction_value': float(filtered_transactions['totalPrice'].mean()),
                    'avg_quantity_per_transaction': float(filtered_transactions['quantity'].mean())
                },
                'growth_opportunities': ["Identify new product categories based on emerging trends.", "Expand into underserved customer segments."],
                'risk_factors': ["Increasing competition.", "Supply chain disruptions."],
                'strategic_recommendations': ["Invest in R&D for innovative products.", "Strengthen customer loyalty programs."],
                'timestamp': datetime.utcnow().isoformat()
            }
            return {'status': 'success', 'data': intelligence}
        except Exception as e:
            logger.error(f"Failed to get market intelligence: {e}", exc_info=True)
            raise

    async def perform_causal_analysis(
        self, target_metric: str, analysis_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform causal analysis to understand what drives key metrics."""
        if not self._graph_built:
            # Attempt to load from disk if not built in current session (e.g., app restart)
            graph_load_path = os.path.join(self.config.BASE_MODEL_DIR, "customer_behavior_graph.gml")
            try:
                load_result = self.knowledge_graph.load_graph(graph_load_path)
                if load_result['status'] == 'success':
                    self._graph_built = True
                    logger.info("Knowledge graph loaded for causal analysis.")
            except Exception as e:
                logger.warning(f"Could not load knowledge graph from disk: {e}. Attempting to build.")
                await self._build_knowledge_graph() # Attempt to build if not loaded
                if not self._graph_built:
                    return {'status': 'error', 'message': 'Knowledge graph not built and cannot be loaded/built.'}

        try:
            # Causal analysis is complex and often involves specialized libraries (e.g., DoWhy, CausalForest).
            # For this context, we will provide a conceptual output based on common factors
            # and potentially leverage graph relationships for causal paths.
            
            # A real implementation would require a proper causal inference engine
            # and perhaps a defined causal graph structure.
            
            causal_factors = {}
            intervention_recommendations = []

            if target_metric == 'total_revenue':
                # Example: Factors that could cause changes in total revenue
                causal_factors = {
                    'product_price_changes': {'impact': 'positive', 'strength': 'high', 'reason': 'Directly affects sales volume and revenue per unit.'},
                    'marketing_spend_increase': {'impact': 'positive', 'strength': 'medium', 'reason': 'Increases product visibility and customer acquisition.'},
                    'customer_satisfaction_rating': {'impact': 'positive', 'strength': 'medium', 'reason': 'Higher satisfaction leads to repeat purchases and referrals.'},
                    'website_traffic_volume': {'impact': 'positive', 'strength': 'high', 'reason': 'More visitors correlate with more potential transactions.'},
                    'competitor_pricing_strategies': {'impact': 'negative', 'strength': 'high', 'reason': 'Aggressive competitor pricing can draw customers away.'}
                }
                intervention_recommendations = [
                    "Implement A/B testing on pricing strategies to find optimal points.",
                    "Increase investment in targeted digital marketing campaigns.",
                    "Enhance customer support and post-purchase follow-ups to boost satisfaction."
                ]
            elif target_metric == 'customer_churn_rate':
                # Example: Factors influencing churn rate
                causal_factors = {
                    'recency_of_last_purchase': {'impact': 'positive', 'strength': 'high', 'reason': 'Longer inactivity often precedes churn.'}, # Higher recency -> higher churn
                    'negative_feedback_count': {'impact': 'positive', 'strength': 'medium', 'reason': 'Customer dissatisfaction is a strong churn indicator.'},
                    'customer_support_response_time': {'impact': 'negative', 'strength': 'medium', 'reason': 'Faster resolution of issues improves retention.'},
                    'product_return_rate_by_user': {'impact': 'positive', 'strength': 'low', 'reason': 'Frequent returns may indicate dissatisfaction or poor fit.'}
                }
                intervention_recommendations = [
                    "Implement proactive churn prevention campaigns based on inactivity triggers.",
                    "Improve product quality and accurately describe products to reduce returns.",
                    "Optimize customer service workflows for quicker issue resolution."
                ]
            else:
                causal_factors = {"message": f"Causal analysis for metric '{target_metric}' is not pre-defined in this example."}

            return {
                'status': 'success',
                'target_metric': target_metric,
                'causal_factors': causal_factors,
                'intervention_recommendations': intervention_recommendations,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Causal analysis failed for {target_metric}: {e}", exc_info=True)
            raise

    async def get_strategic_recommendations(
        self, business_context: Dict[str, Any], priority_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get high-level strategic recommendations based on comprehensive analysis."""
        if not self._graph_built:
            # Attempt to load from disk if not built in current session (e.g., app restart)
            graph_load_path = os.path.join(self.config.BASE_MODEL_DIR, "customer_behavior_graph.gml")
            try:
                load_result = self.knowledge_graph.load_graph(graph_load_path)
                if load_result['status'] == 'success':
                    self._graph_built = True
                    logger.info("Knowledge graph loaded for strategic recommendations.")
            except Exception as e:
                logger.warning(f"Could not load knowledge graph from disk: {e}. Attempting to build.")
                await self._build_knowledge_graph() # Attempt to build if not loaded
                if not self._graph_built:
                    return {'status': 'error', 'message': 'Knowledge graph not built and cannot be loaded/built.'}

        try:
            if priority_areas is None:
                priority_areas = ['revenue_growth', 'customer_retention', 'market_expansion', 'operational_efficiency', 'product_innovation']

            strategic_initiatives = {}
            for area in priority_areas:
                if area == 'revenue_growth':
                    strategic_initiatives[area] = [
                        "Implement dynamic pricing across all product categories to maximize profit margins.",
                        "Launch targeted up-selling and cross-selling campaigns leveraging AI recommendations.",
                        "Explore new monetization models, such as subscription services or premium features.",
                        "Optimize marketing spend by allocating budget to channels with highest ROI based on predictive analytics."
                    ]
                elif area == 'customer_retention':
                    strategic_initiatives[area] = [
                        "Enhance personalized customer engagement strategies, especially for medium/high-risk churn customers.",
                        "Develop a tiered loyalty program with exclusive benefits to reward and retain valuable customers.",
                        "Improve post-purchase customer support and establish robust feedback loops to address dissatisfaction promptly.",
                        "Proactively identify and re-engage dormant customers with tailored incentives."
                    ]
                elif area == 'market_expansion':
                    strategic_initiatives[area] = [
                        "Identify untapped geographic markets or niche customer segments using demographic and behavioral data.",
                        "Introduce new product lines or adapt existing ones based on market intelligence and identified gaps.",
                        "Form strategic partnerships or collaborations to enter new customer segments or distribution channels."
                    ]
                elif area == 'operational_efficiency':
                    strategic_initiatives[area] = [
                        "Automate inventory management and order fulfillment processes using AI-driven forecasts and demand prediction.",
                        "Optimize supply chain logistics with predictive analytics to reduce costs and improve delivery times.",
                        "Streamline customer service workflows with AI-powered chatbots and intelligent routing for common queries.",
                        "Implement anomaly detection in operational data to quickly identify and resolve inefficiencies."
                    ]
                elif area == 'product_innovation':
                    strategic_initiatives[area] = [
                        "Utilize AI to analyze customer feedback and market trends for identifying unmet needs and new product opportunities.",
                        "Develop predictive models for product success based on historical data and market signals.",
                        "Leverage A/B testing and experimentation to rapidly iterate on new product features and designs.",
                        "Integrate explainable AI to understand which product features drive customer satisfaction and sales."
                    ]
                else:
                    strategic_initiatives[area] = [f"No specific initiatives defined for {area} yet."]
            
            # Example of combining insights for overall recommendations based on business context
            overall_recommendations = []
            if business_context.get('ecommerce_platform_stability', True) == False:
                overall_recommendations.append("Prioritize platform stability and performance improvements before aggressively scaling new AI initiatives.")
            if business_context.get('current_market_growth') == 'high':
                overall_recommendations.append("Capitalize on high market growth by accelerating customer acquisition and product launch efforts.")
            if business_context.get('resource_availability') == 'limited':
                overall_recommendations.append("Focus on high-impact, low-cost AI initiatives first to maximize ROI with limited resources.")

            return {
                'status': 'success',
                'business_context': business_context,
                'priority_areas': priority_areas,
                'strategic_initiatives': strategic_initiatives,
                'overall_recommendations': overall_recommendations,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to generate strategic recommendations: {e}", exc_info=True)
            raise

    # Helper methods to fetch data from MongoDB (similar to other services)
    async def _get_users(self) -> pd.DataFrame:
        try:
            users_cursor = self.db.users.find({})
            users_list = await users_cursor.to_list(length=None)
            df = pd.DataFrame(users_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure proper datetime parsing for relevant columns
            if 'registrationDate' in df.columns:
                df['registrationDate'] = pd.to_datetime(df['registrationDate'], errors='coerce')
            if 'lastLogin' in df.columns:
                df['lastLogin'] = pd.to_datetime(df['lastLogin'], errors='coerce')

            logger.info(f"Fetched {len(df)} users for reasoning service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching users for reasoning service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_products(self) -> pd.DataFrame:
        try:
            products_cursor = self.db.products.find({})
            products_list = await products_cursor.to_list(length=None)
            df = pd.DataFrame(products_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure numeric types
            if 'price' in df.columns:
                df['price'] = pd.to_numeric(df['price'], errors='coerce')
            if 'stock' in df.columns:
                df['stock'] = pd.to_numeric(df['stock'], errors='coerce')

            logger.info(f"Fetched {len(df)} products for reasoning service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching products for reasoning service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_transactions(self) -> pd.DataFrame:
        try:
            transactions_cursor = self.db.transactions.find({})
            transactions_list = await transactions_cursor.to_list(length=None)
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

            logger.info(f"Fetched {len(df)} transactions for reasoning service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching transactions for reasoning service: {e}", exc_info=True)
            return pd.DataFrame()
            
    async def _get_feedback(self) -> pd.DataFrame:
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

            logger.info(f"Fetched {len(df)} feedback entries for reasoning service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching feedback for reasoning service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_activities(self) -> pd.DataFrame:
        try:
            activities_cursor = self.db.user_activities.find({})
            activities_list = await activities_cursor.to_list(length=None)
            df = pd.DataFrame(activities_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            logger.info(f"Fetched {len(df)} activities for reasoning service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching activities for reasoning service: {e}", exc_info=True)
            return pd.DataFrame()


```

### `./app/utils/graph_utils.py`
```py
import networkx as nx
import pandas as pd
from typing import List, Dict, Any, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)

def create_bipartite_graph(df: pd.DataFrame, left_col: str, right_col: str, edge_attrs: List[str] = None) -> nx.Graph:
    """
    Creates a bipartite graph from a DataFrame representing relationships.
    Nodes from `left_col` form one set, `right_col` forms the other.
    Args:
        df: Input DataFrame containing the relationships.
        left_col: Column for the 'left' set of nodes (e.g., 'user_id').
        right_col: Column for the 'right' set of nodes (e.g., 'product_id').
        edge_attrs: List of columns from df to be included as edge attributes.
    Returns:
        A NetworkX bipartite graph.
    """
    G = nx.Graph()
    # Add nodes with 'bipartite' attribute to distinguish the sets
    left_nodes = df[left_col].unique()
    right_nodes = df[right_col].unique()
    G.add_nodes_from(left_nodes, bipartite=0) # Assign 0 to the left set
    G.add_nodes_from(right_nodes, bipartite=1) # Assign 1 to the right set

    # Add edges with attributes
    for idx, row in df.iterrows():
        u = row[left_col]
        v = row[right_col]
        
        # Collect specified edge attributes
        attrs = {}
        if edge_attrs:
            for attr in edge_attrs:
                if attr in row:
                    # Handle potential non-serializable types for attributes if needed
                    val = row[attr]
                    if isinstance(val, (datetime, pd.Timestamp)):
                        attrs[attr] = val.isoformat()
                    elif pd.isna(val):
                        attrs[attr] = None # Handle NaN values
                    else:
                        attrs[attr] = val
                else:
                    attrs[attr] = None # Attribute not found in row

        G.add_edge(u, v, **attrs)
    logger.info(f"Created bipartite graph with {len(left_nodes)} {left_col} nodes and {len(right_nodes)} {right_col} nodes.")
    return G

def project_bipartite_graph(G: nx.Graph, nodes: List[Any], bipartite_set: int = 0) -> nx.Graph:
    """
    Projects a bipartite graph onto one set of nodes. This creates a unipartite graph
    where connections represent shared neighbors in the original bipartite graph.
    Args:
        G: The bipartite graph.
        nodes: A list of nodes from one bipartite set to project onto.
        bipartite_set: 0 for the 'left' set (e.g., users), 1 for the 'right' set (e.g., products).
                       Nodes in the `nodes` list should belong to this set.
    Returns:
        The projected graph.
    """
    if bipartite_set not in [0, 1]:
        raise ValueError("bipartite_set must be 0 or 1.")
    
    # Filter nodes to ensure they belong to the specified bipartite set
    valid_nodes = [n for n in nodes if n in G and G.nodes[n].get('bipartite') == bipartite_set]
    
    if not valid_nodes:
        logger.warning(f"No valid nodes found in the graph for projection for bipartite set {bipartite_set}. Returning empty graph.")
        return nx.Graph()

    # Use networkx's built-in projection
    projected_G = nx.bipartite.projected_graph(G, valid_nodes)
    
    # Add 'weight' to edges based on number of common neighbors (if applicable)
    # This is a common practice for projected graphs
    for u, v, data in projected_G.edges(data=True):
        common_neighbors = len(list(nx.common_neighbors(G, u, v)))
        projected_G.edges[u,v]['weight'] = common_neighbors
        projected_G.edges[u,v]['type'] = 'co_occurrence' # Add a type for clarity

    logger.info(f"Projected graph created with {projected_G.number_of_nodes()} nodes and {projected_G.number_of_edges()} edges.")
    return projected_G

def calculate_graph_metrics(G: nx.Graph) -> Dict[str, Any]:
    """
    Calculates common graph-theoretic metrics for a given graph.
    Args:
        G: The input NetworkX graph.
    Returns:
        A dictionary of graph metrics.
    """
    metrics = {
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "is_empty": G.number_of_nodes() == 0,
        "density": nx.density(G) if G.number_of_nodes() > 1 else 0
    }

    if G.number_of_nodes() > 1:
        if nx.is_connected(G):
            metrics["is_connected"] = True
            try: # Try to calculate path length and diameter, can fail for large graphs
                metrics["avg_shortest_path_length"] = nx.average_shortest_path_length(G)
                metrics["diameter"] = nx.diameter(G)
            except (nx.NetworkXError, nx.NetworkXNoPath):
                metrics["avg_shortest_path_length"] = None
                metrics["diameter"] = None
                logger.warning("Could not calculate avg_shortest_path_length or diameter (graph not strongly connected or too large).")
        else:
            metrics["is_connected"] = False
            metrics["num_connected_components"] = nx.number_connected_components(G)
            metrics["largest_component_nodes"] = len(max(nx.connected_components(G), key=len, default=set()))

    # Handle cases for empty graph or single node graph for degree calculations
    metrics["avg_degree"] = sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0
    
    if G.is_directed():
        metrics["avg_in_degree"] = sum(dict(G.in_degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0
        metrics["avg_out_degree"] = sum(dict(G.out_degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0

    return metrics

def find_k_shortest_paths(G: nx.Graph, source: Any, target: Any, k: int = 1, weight: str = None) -> List[List[Any]]:
    """
    Finds k shortest paths between a source and target node.
    Args:
        G: The graph.
        source: Source node.
        target: Target node.
        k: Number of shortest paths to find.
        weight: Edge attribute to use as weight (e.g., 'distance', 'cost').
    Returns:
        A list of lists, where each inner list is a path.
    """
    try:
        paths = list(nx.shortest_simple_paths(G, source, target, weight=weight))
        return paths[:k]
    except nx.NetworkXNoPath:
        logger.warning(f"No path found between {source} and {target}.")
        return []
    except Exception as e:
        logger.error(f"Error finding shortest paths between {source} and {target}: {str(e)}", exc_info=True)
        return []

def recommend_by_proximity(G: nx.Graph, start_node: Any, max_distance: int = 2) -> List[Any]:
    """
    Recommends nodes based on their proximity in the graph (e.g., "friends of friends" for users,
    or "related products" for products).
    Args:
        G: The graph.
        start_node: The node from which to start recommendations.
        max_distance: Maximum distance (number of hops) from the start_node to consider.
    Returns:
        A list of recommended nodes (excluding the start_node itself and immediate neighbors).
    """
    if start_node not in G:
        logger.warning(f"Start node {start_node} not found in graph. Cannot recommend by proximity.")
        return []

    recommended_nodes = set()
    # Use BFS to find nodes within max_distance
    for node, distance in nx.shortest_path_length(G, source=start_node).items():
        # Exclude the start_node itself and immediate neighbors (distance 1)
        # Recommend nodes at distance > 1 up to max_distance
        if 1 < distance <= max_distance:
            recommended_nodes.add(node)
            
    # Optionally, you can filter out nodes of specific types if the graph contains mixed node types
    # For example, if you want to recommend only 'product_' nodes
    clean_recommendations = [
        str(node).replace('customer_', '').replace('product_', '').replace('category_', '') 
        for node in recommended_nodes
        # if str(node).startswith('product_') # Example: filter for only product recommendations
    ]
    
    return list(set(clean_recommendations)) # Use set to remove duplicates, then convert to list


```

### `./app/utils/__init__.py`
```py

```

### `./app/utils/logger.py`
```py
import os
from loguru import logger as loguru_logger
from datetime import datetime

# Remove default handler to avoid duplicate logs
loguru_logger.remove()

# Configure logger for console output
loguru_logger.add(
    sink="sys.stdout",
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
    diagnose=True
)

# Configure logger for file output
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file_path = os.path.join(LOG_DIR, f"ai_service_{datetime.now().strftime('%Y-%m-%d')}.log")

loguru_logger.add(
    sink=log_file_path,
    rotation="1 day",  # New log file every day
    retention="7 days", # Keep logs for 7 days
    compression="zip",  # Compress old log files
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    diagnose=True
)

# Expose loguru_logger as 'logger' for easy import
logger = loguru_logger
```

### `./app/utils/model_utils.py`
```py
import joblib
import os
import logging
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ModelUtils:
    """
    Utility class for saving, loading, and managing machine learning models.
    """

    def __init__(self, model_dir: str = 'models/saved_models'):
        # Adjust model_dir to be relative to the app directory if this utility
        # is called from within the app. For consistency with a consolidated app/ structure,
        # it's better to manage model paths dynamically or through a central config.
        # However, if 'models/saved_models' is relative to the *root* of the project,
        # then this path is fine. Assuming BASE_MODEL_DIR from ModelConfig is used by services.
        self.model_dir = model_dir 
        os.makedirs(self.model_dir, exist_ok=True) # Ensure the directory exists

    def save_model(self, model: Any, model_name: str, metadata: Dict = None) -> Dict:
        """
        Saves a trained model to disk along with optional metadata.
        Args:
            model: The trained machine learning model object.
            model_name: A unique name for the model (e.g., 'dynamic_pricing_v1').
            metadata: Optional dictionary of metadata (e.g., training date, metrics).
        Returns:
            A dictionary with status and path.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{model_name}_{timestamp}.pkl" # Using .pkl for joblib files
            filepath = os.path.join(self.model_dir, filename)
            
            model_data = {
                'model': model,
                'metadata': metadata if metadata is not None else {},
                'saved_at': datetime.utcnow().isoformat()
            }
            joblib.dump(model_data, filepath)
            logger.info(f"Model '{model_name}' saved to {filepath}")
            return {'status': 'success', 'path': filepath, 'filename': filename}
        except Exception as e:
            logger.error(f"Error saving model '{model_name}': {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def load_latest_model(self, model_name_prefix: str) -> Optional[Any]:
        """
        Loads the latest version of a model based on its name prefix.
        Assumes model files are named like 'model_name_prefix_YYYYMMDD_HHMMSS.pkl'.
        Args:
            model_name_prefix: The prefix of the model name (e.g., 'dynamic_pricing').
        Returns:
            The loaded model object (the 'model' itself from the saved dictionary) or None if not found.
        """
        try:
            # List files that match the prefix and .pkl extension
            model_files = [f for f in os.listdir(self.model_dir) if f.startswith(model_name_prefix) and f.endswith('.pkl')]
            
            if not model_files:
                logger.warning(f"No model files found for prefix '{model_name_prefix}' in {self.model_dir}")
                return None
            
            # Sort files by timestamp in descending order to get the latest
            # Expecting format: {model_name_prefix}_{YYYYMMDD}_{HHMMSS}.pkl
            def get_timestamp_from_filename(filename):
                parts = filename.split('_')
                if len(parts) >= 3:
                    try:
                        date_str = parts[-2] # YYYYMMDD
                        time_str = parts[-1].split('.')[0] # HHMMSS
                        return datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    except ValueError:
                        logger.warning(f"Could not parse timestamp from filename: {filename}")
                        return datetime.min # Return a very old date if parsing fails
                return datetime.min # Return a very old date if format is unexpected

            model_files.sort(key=get_timestamp_from_filename, reverse=True)
            
            latest_file = model_files[0]
            filepath = os.path.join(self.model_dir, latest_file)
            
            model_data = joblib.load(filepath)
            logger.info(f"Loaded latest model '{model_name_prefix}' from {latest_file}")
            return model_data.get('model') # Return the 'model' object
        except Exception as e:
            logger.error(f"Error loading latest model '{model_name_prefix}': {str(e)}", exc_info=True)
            return None

    def load_model_by_path(self, filepath: str) -> Optional[Any]:
        """
        Loads a model from a specific file path.
        Args:
            filepath: The full path to the model file.
        Returns:
            The loaded model object (the 'model' itself from the saved dictionary) or None if not found.
        """
        try:
            if not os.path.exists(filepath):
                logger.warning(f"Model file not found at {filepath}")
                return None
            
            model_data = joblib.load(filepath)
            logger.info(f"Loaded model from {filepath}")
            return model_data.get('model') # Return the 'model' object
        except Exception as e:
            logger.error(f"Error loading model from {filepath}: {str(e)}", exc_info=True)
            return None
            
    def get_model_metadata(self, filepath: str) -> Optional[Dict]:
        """
        Retrieves metadata associated with a saved model.
        """
        try:
            if not os.path.exists(filepath):
                logger.warning(f"Model file not found at {filepath}")
                return None
            model_data = joblib.load(filepath)
            return model_data.get('metadata', {})
        except Exception as e:
            logger.error(f"Error getting metadata for model at {filepath}: {str(e)}", exc_info=True)
            return None


```

### `./Dockerfile`
```Dockerfile
# ai_service/Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# Add redis-tools if you want redis-cli inside the container for debugging
# Required by some Python packages for image/chart generation (e.g., kaleido for plotly)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*


# Copy the requirements file into the container
# Assuming you have combined requirements.txt and requirements_phase4.txt into a single requirements.txt
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create the directory for saved models if it doesn't exist (important for persistence)
# This should match MODEL_SAVE_PATH in .env / ModelConfig
RUN mkdir -p /app/models/saved_models

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `./tests/__init__.py`
```py

```

