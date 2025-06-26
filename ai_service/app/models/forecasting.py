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

    def train(self, df: pd.DataFrame, target_col: str = 'daily_revenue') -> dict:
        """
        Trains the forecasting model.
        Expects df to be prepared with time series and feature engineering.
        """
        if df.empty:
            logger.warning("No data to train forecasting model.")
            return {"status": "failed", "message": "No data for training."}

        # Ensure 'timestamp' is datetime and sort
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Create time features
        df = self.feature_engineer.create_time_features(df, 'timestamp')

        # Create lag features for the target column
        # Lags are important for time series forecasting
        df = self.feature_engineer.create_lag_features(df, cols=[target_col], lags=[1, 2, 3, 7, 14])

        # Create rolling features
        df = self.feature_engineer.create_rolling_features(df, cols=[target_col], windows=[7, 14], agg_funcs=['mean', 'std'])

        # Drop rows with NaN values that result from lag/rolling features (typically at the beginning)
        df = df.dropna().reset_index(drop=True)
        if df.empty:
            logger.warning("DataFrame became empty after feature engineering and dropping NaNs.")
            return {"status": "failed", "message": "DataFrame empty after feature engineering."}

        # Define features and target
        features = [col for col in df.columns if col not in [target_col, 'timestamp', '_id']]
        X, y = self.feature_engineer.get_features_and_target(df, target_col, feature_cols=features)

        if X.empty or y.empty:
            logger.error("Features or target are empty after preparation for forecasting model training.")
            return {"status": "failed", "message": "Empty features or target after preparation."}

        # Split data (time-based split is crucial for time series)
        split_point = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_point], X.iloc[split_point:]
        y_train, y_test = y.iloc[:split_point], y.iloc[split_point:]

        if X_train.empty or y_train.empty:
            logger.warning("Training data is empty for forecasting model.")
            return {"status": "failed", "message": "Empty training data."}

        self._initialize_model() # Ensure model is initialized before training
        logger.info(f"Starting training for {self.model_type} model with {len(X_train)} samples.")
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        self.metrics = {"rmse": rmse, "r2_score": r2, "trained_on_samples": len(X_train)}
        self.is_trained = True
        logger.info(f"Forecasting model training complete. Metrics: {self.metrics}")

        self.save_model()
        return {"status": "success", "metrics": self.metrics}

    def predict(self, df: pd.DataFrame, target_col: str = 'daily_revenue') -> np.ndarray:
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

        # Ensure 'timestamp' is datetime and sort
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Apply same feature engineering as training
        df = self.feature_engineer.create_time_features(df, 'timestamp')
        df = self.feature_engineer.create_lag_features(df, cols=[target_col], lags=[1, 2, 3, 7, 14])
        df = self.feature_engineer.create_rolling_features(df, cols=[target_col], windows=[7, 14], agg_funcs=['mean', 'std'])
        df = df.dropna().reset_index(drop=True) # Drop rows with NaN from lag/rolling features

        if df.empty:
            logger.warning("DataFrame became empty after feature engineering for prediction.")
            return np.array([])

        features = [col for col in df.columns if col not in [target_col, 'timestamp', '_id']]
        # Ensure features match what the model was trained on
        # This is a critical step for deployment: ensure consistency in feature columns
        # For simplicity, we assume the input df has all necessary features or can be engineered.
        # In a real system, you'd save feature names during training and validate here.
        # For now, let's just make sure we only select features that exist in the test data
        X = df[features]
        # Align columns if necessary (e.g., if some features are missing in prediction data)
        # For a robust solution, store trained features and reindex X here.
        # Example: X = X.reindex(columns=self.trained_features, fill_value=0)

        predictions = self.model.predict(X)
        logger.info(f"Generated {len(predictions)} predictions.")
        return predictions

    def forecast_future(self, historical_df: pd.DataFrame, horizon: int = settings.FORECAST_HORIZON, target_col: str = 'daily_revenue'):
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

        # Ensure 'timestamp' is datetime and sort
        historical_df['timestamp'] = pd.to_datetime(historical_df['timestamp'])
        historical_df = historical_df.sort_values('timestamp').reset_index(drop=True)

        # Get the last known values for starting the forecast
        last_date = historical_df['timestamp'].max()
        last_target_value = historical_df[target_col].iloc[-1]

        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, horizon + 1)]
        forecast_df = pd.DataFrame({'timestamp': future_dates, target_col: 0.0}) # Placeholder target

        # Combine historical and future to create features for future predictions
        combined_df = pd.concat([historical_df, forecast_df], ignore_index=True)
        combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)

        # Apply same feature engineering as training
        combined_df = self.feature_engineer.create_time_features(combined_df, 'timestamp')
        combined_df = self.feature_engineer.create_lag_features(combined_df, cols=[target_col], lags=[1, 2, 3, 7, 14])
        combined_df = self.feature_engineer.create_rolling_features(combined_df, cols=[target_col], windows=[7, 14], agg_funcs=['mean', 'std'])

        # Replace NaN from lags with appropriate values for prediction (e.g., last known value)
        # For the very first rows, fill with 0 or a sensible default.
        combined_df = combined_df.fillna(0) # Or more sophisticated imputation

        # Identify rows for actual forecasting (the future dates)
        future_X = combined_df[combined_df['timestamp'].isin(future_dates)]
        
        if future_X.empty:
            logger.warning("Future data frame is empty after feature engineering for forecasting.")
            return pd.DataFrame()

        # Select features for prediction, ensuring they match training
        features = [col for col in future_X.columns if col not in [target_col, 'timestamp', '_id']]
        
        # This is where a more robust feature management would be needed.
        # For now, let's filter X to only contain features present in the original historical_df training set (minus target, timestamp, _id).
        # We need to ensure that the features array passed to predict contains *all* columns the model was trained on, in the correct order.
        # A common practice is to store the list of features used during training and reindex prediction data.
        
        # For this example, let's extract the feature columns from the future_X dataframe:
        X_predict = future_X[features] # This assumes `features` list contains all needed columns.
        
        # Make predictions
        future_predictions = self.model.predict(X_predict)

        # Assign predictions to the target column in the forecast_df
        forecast_df[target_col] = future_predictions

        logger.info(f"Generated {horizon} day forecast for '{target_col}'.")
        return forecast_df[['timestamp', target_col]]


    def save_model(self):
        """Saves the trained model and feature engineer (scalers/encoders)."""
        if self.model:
            os.makedirs(settings.MODEL_SAVE_PATH, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.feature_engineer, os.path.join(settings.MODEL_SAVE_PATH, f"forecasting_feature_engineer_{self.model_type}.joblib"))
            logger.info(f"Forecasting model and feature engineer saved to {self.model_path}")
        else:
            logger.warning("No forecasting model to save.")

    def load_model(self):
        """Loads the trained model and feature engineer."""
        try:
            self.model = joblib.load(self.model_path)
            self.feature_engineer = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, f"forecasting_feature_engineer_{self.model_type}.joblib"))
            self.is_trained = True
            logger.info(f"Forecasting model and feature engineer loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Forecasting model not found at {self.model_path}. Model needs to be trained.")
            self.is_trained = False
            return False
        except Exception as e:
            logger.error(f"Error loading forecasting model: {e}", exc_info=True)
            self.is_trained = False
            return False