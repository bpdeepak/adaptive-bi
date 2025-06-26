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