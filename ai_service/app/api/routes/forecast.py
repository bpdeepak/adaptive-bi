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