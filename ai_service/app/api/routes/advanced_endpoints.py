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

# Placeholder dependency functions (will call actual dependency functions)
async def get_pricing_service_dependency():
    if hasattr(get_pricing_service_dependency, 'actual_func'):
        return await get_pricing_service_dependency.actual_func()
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Pricing service dependency not initialized")

async def get_churn_service_dependency():
    if hasattr(get_churn_service_dependency, 'actual_func'):
        return await get_churn_service_dependency.actual_func()
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Churn service dependency not initialized")

async def get_reasoning_service_dependency():
    if hasattr(get_reasoning_service_dependency, 'actual_func'):
        return await get_reasoning_service_dependency.actual_func()
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Reasoning service dependency not initialized")

async def get_feedback_service_dependency():
    if hasattr(get_feedback_service_dependency, 'actual_func'):
        return await get_feedback_service_dependency.actual_func()
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Feedback service dependency not initialized")


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
        optimal_price = await pricing_service.predict_optimal_price_simple(
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

# --- Explainer Status and Testing Endpoints ---
@router.get("/explainers/status", response_model=Dict[str, Any], summary="Get ExplainableAI Status",
            description="Returns the current status of all SHAP and LIME explainers.")
async def get_explainer_status_endpoint():
    try:
        logger.info("Getting ExplainableAI explainer status")
        from app.models.model_manager import model_manager
        explainer_status = model_manager.get_explainer_status()
        logger.info(f"ExplainableAI status retrieved: {explainer_status.get('total_explainers', 0)} explainers")
        return explainer_status
    except Exception as e:
        logger.error(f"Error getting explainer status: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

@router.post("/explainers/test", response_model=Dict[str, Any], summary="Test ExplainableAI Explainers",
             description="Tests all available explainers with sample data to ensure they are working correctly.")
async def test_explainers_endpoint():
    try:
        logger.info("Testing ExplainableAI explainers")
        from app.models.model_manager import model_manager
        test_results = await model_manager.test_explainers()
        logger.info(f"ExplainableAI testing completed: {test_results.get('summary', {}).get('passed_tests', 0)}/{test_results.get('summary', {}).get('total_tests', 0)} tests passed")
        return test_results
    except Exception as e:
        logger.error(f"Error testing explainers: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

# --- System Status Endpoint ---
@router.get("/system/status", response_model=Dict[str, Any], summary="Get Complete System Status",
            description="Returns comprehensive status of all models, explainers, and AI capabilities.")
async def get_system_status_endpoint():
    try:
        logger.info("Getting comprehensive system status")
        from app.models.model_manager import model_manager
        
        # Get explainer status
        explainer_status = model_manager.get_explainer_status()
        
        # Build comprehensive status
        system_status = {
            "timestamp": datetime.now().isoformat(),
            "phase3_models": {
                "loaded": model_manager.models_loaded,
                "forecasting": bool(hasattr(model_manager, 'forecasting_model') and 
                                  model_manager.forecasting_model and 
                                  hasattr(model_manager.forecasting_model, 'model') and 
                                  model_manager.forecasting_model.model),
                "anomaly_detection": bool(hasattr(model_manager, 'anomaly_model') and 
                                        model_manager.anomaly_model and 
                                        hasattr(model_manager.anomaly_model, 'model') and 
                                        model_manager.anomaly_model.model),
                "recommendation": bool(hasattr(model_manager, 'recommendation_model') and 
                                     model_manager.recommendation_model and 
                                     hasattr(model_manager.recommendation_model, 'model') and 
                                     model_manager.recommendation_model.model)
            },
            "phase4_models": {
                "loaded": model_manager.phase4_models_loaded,
                "dynamic_pricing": bool(hasattr(model_manager, 'pricing_model') and 
                                      model_manager.pricing_model and 
                                      hasattr(model_manager.pricing_model, 'model') and 
                                      model_manager.pricing_model.model),
                "churn_prediction": bool(hasattr(model_manager, 'churn_model') and 
                                       model_manager.churn_model and 
                                       hasattr(model_manager.churn_model, 'model') and 
                                       model_manager.churn_model.model),
                "knowledge_graph": bool(hasattr(model_manager, 'knowledge_graph') and 
                                      model_manager.knowledge_graph and 
                                      hasattr(model_manager.knowledge_graph, '_is_built') and 
                                      model_manager.knowledge_graph._is_built)
            },
            "explainable_ai": {
                "status": explainer_status['status'],
                "total_explainers": explainer_status.get('total_explainers', 0),
                "available_explainers": [name for name, info in explainer_status.get('explainers', {}).items() 
                                       if info.get('available', False)]
            },
            "cognitive_reasoning": {
                "available": bool(hasattr(model_manager, 'knowledge_graph') and 
                                model_manager.knowledge_graph and 
                                hasattr(model_manager.knowledge_graph, '_is_built') and 
                                model_manager.knowledge_graph._is_built)
            },
            "services": {
                "pricing_service": "initialized",
                "churn_service": "initialized", 
                "reasoning_service": "initialized",
                "feedback_service": "initialized"
            }
        }
        
        logger.info(f"System status retrieved - Phase 3: {system_status['phase3_models']['loaded']}, Phase 4: {system_status['phase4_models']['loaded']}, Explainers: {system_status['explainable_ai']['total_explainers']}")
        return system_status
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
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
