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