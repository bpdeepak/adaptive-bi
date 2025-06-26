import pandas as pd
import numpy as np
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
        X_scaled = self.feature_engineer.scale_features(X, features, scaler_type='MinMaxScaler', fit=True)
        # Store original feature names for prediction consistency
        self._trained_features = X_scaled.columns.tolist()

        self._initialize_model()
        logger.info(f"Starting training for {self.model_type} model with {len(X_scaled)} samples and {len(features)} features.")
        self.model.fit(X_scaled)

        # No traditional "metrics" for unsupervised anomaly detection,
        # but we can infer some statistics like the number of outliers detected on training data
        # For IsolationForest, -1 indicates outlier, 1 indicates inlier
        if self.model_type == "IsolationForest":
            predictions = self.model.predict(X_scaled)
            n_outliers = list(predictions).count(-1)
            outlier_percentage = (n_outliers / len(predictions)) * 100 if len(predictions) > 0 else 0
            self.metrics = {"outliers_in_training_data": n_outliers, "outlier_percentage": f"{outlier_percentage:.2f}%"}
        elif self.model_type == "OneClassSVM":
            predictions = self.model.predict(X_scaled)
            n_outliers = list(predictions).count(-1)
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

    def get_anomaly_details(self, df: pd.DataFrame, anomaly_features: list) -> list:
        """
        Extracts details for detected anomalies.
        """
        anomalies_df = df[df['is_anomaly'] == True]
        if anomalies_df.empty:
            return []

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