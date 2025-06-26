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

        # Calculate minimum samples needed based on lags and rolling windows
        max_lag = max(settings.FORECASTING_LAG_FEATURES) if hasattr(settings, 'FORECASTING_LAG_FEATURES') and settings.FORECASTING_LAG_FEATURES else 14
        max_window = max(settings.FORECASTING_ROLLING_WINDOW_FEATURES) if hasattr(settings, 'FORECASTING_ROLLING_WINDOW_FEATURES') and settings.FORECASTING_ROLLING_WINDOW_FEATURES else 14
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