from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.models.model_manager import ModelManager
from app.services.data_processor import DataProcessor
from app.utils.logger import logger
from app.api.dependencies import get_db, get_model_manager
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta

router = APIRouter()

class AnomalyDetectionRequest(BaseModel):
    data_points: List[Dict[str, Any]] = Field(
        ...,
        description="List of data points to check for anomalies. Each dict should contain features used for training (e.g., 'totalAmount', 'quantity')."
    )
    # You might want to allow specifying features dynamically or assume they are pre-defined
    # For now, let's assume they are predefined in the model's training process
    features: List[str] = Field(
        ["totalAmount", "quantity"], # Default example features
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
        anomaly_features = ["totalAmount", "quantity"]
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
                # You might want to raise an error or fill with a default value
                df[col] = 0 # Add missing feature with default 0


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