# ai_service/app/services/data_processor.py
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Optional
from app.config import settings
from app.utils.logger import logger
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import MongoClient

class DataProcessor:
    """
    Handles fetching and initial processing of raw data from MongoDB.
    """
    def __init__(self, db=None, sync_db=None):
        self._db = db  # Expected to be AsyncIOMotorDatabase
        self._sync_db = sync_db  # For synchronous operations if needed

        if self._db is None and self._sync_db is None:
            raise ValueError("Either an async or a sync database connection must be provided.")

    def _get_async_db(self):
        """Returns the async database client."""
        if self._db is not None:
            return self._db
        else:
            raise RuntimeError("No async database client available.")

    def _get_sync_db(self):
        """Returns the sync database client."""
        if self._sync_db is not None:
            return self._sync_db
        else:
            raise RuntimeError("No sync database client available.")

    async def get_transactions_data(self, days: int = settings.DATA_COLLECTION_DAYS, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Fetches transaction data for a specified number of past days.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Apply memory-safe limit for Phase 3 model training
        if limit is None:
            limit = getattr(settings, 'MAX_TRANSACTIONS_CHUNK', 2000)  # Default from config

        logger.info(f"Fetching transaction data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} (limit: {limit})")

        try:
            transactions_cursor = self._get_async_db().transactions.find(
                {"transactionDate": {"$gte": start_date, "$lte": end_date}}
            ).sort("transactionDate", -1).limit(limit)  # Sort by newest first and apply limit
            transactions_list = await transactions_cursor.to_list(length=limit)

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

    async def get_transactions_data_chunked(self, days: int = settings.DATA_COLLECTION_DAYS, 
                                          chunk_size: int = 1000, max_records: Optional[int] = None) -> pd.DataFrame:
        """
        Memory-efficient version that loads data in chunks to prevent RAM overload.
        DRASTICALLY reduced chunk size and max records for memory conservation.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Limit days and max_records for memory conservation
        days = min(days, 3)  # Maximum 3 days
        max_records = min(max_records or 2000, 2000)  # Maximum 2000 records

        logger.info(f"Fetching transaction data in chunks (size: {chunk_size}) from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}, max_records: {max_records}")

        try:
            # Count total records first
            total_count = await self._get_async_db().transactions.count_documents(
                {"transactionDate": {"$gte": start_date, "$lte": end_date}}
            )
            
            if total_count > max_records:
                logger.warning(f"Limiting data to {max_records} records (found {total_count})")
                total_count = max_records

            if total_count == 0:
                logger.warning(f"No transaction data found for the last {days} days.")
                return pd.DataFrame()

            # Process data in chunks
            dfs = []
            skip = 0
            
            while skip < total_count:
                current_chunk_size = min(chunk_size, total_count - skip)
                
                cursor = self._get_async_db().transactions.find(
                    {"transactionDate": {"$gte": start_date, "$lte": end_date}}
                ).skip(skip).limit(current_chunk_size)
                
                chunk_data = await cursor.to_list(length=current_chunk_size)
                
                if chunk_data:
                    chunk_df = pd.DataFrame(chunk_data)
                    
                    # Remove MongoDB _id to save memory
                    if '_id' in chunk_df.columns:
                        chunk_df = chunk_df.drop(columns=['_id'])
                    
                    # Process chunk immediately to save memory
                    chunk_df['transactionDate'] = pd.to_datetime(chunk_df['transactionDate'])
                    
                    # Keep totalPrice column name for compatibility with pricing service
                    if 'totalPrice' in chunk_df.columns:
                        chunk_df['totalPrice'] = pd.to_numeric(chunk_df['totalPrice'], errors='coerce').fillna(0)
                    
                    if 'quantity' in chunk_df.columns:
                        chunk_df['quantity'] = pd.to_numeric(chunk_df['quantity'], errors='coerce').fillna(0)
                    
                    dfs.append(chunk_df)
                
                skip += current_chunk_size
                
                # Log progress for large datasets
                if skip % (chunk_size * 10) == 0:
                    logger.info(f"Processed {skip}/{total_count} records...")

            # Combine chunks efficiently
            if dfs:
                df = pd.concat(dfs, ignore_index=True)
                df = df.sort_values('transactionDate').reset_index(drop=True)
                df.rename(columns={'transactionDate': 'timestamp'}, inplace=True)
                
                logger.info(f"Fetched {len(df)} transactions in chunks.")
                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching chunked transaction data: {e}", exc_info=True)
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
            activities_cursor = self._get_async_db().user_activities.find(
                {"timestamp": {"$gte": start_date, "$lte": end_date}}
            )
            activities_list = await activities_cursor.to_list(length=None)
            activities_df = pd.DataFrame(activities_list)

            feedback_cursor = self._get_async_db().feedback.find(
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
            products_cursor = self._get_async_db().products.find({})
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

        logger.info(f"Preparing time series from {len(df)} transactions spanning {df['timestamp'].dt.date.nunique()} unique dates")

        # Ensure 'timestamp' is the index and is a DatetimeIndex
        df_ts = df.set_index('timestamp')
        df_ts.index = pd.to_datetime(df_ts.index)

        # Resample and sum, then fill NaNs from resampling with 0
        df_ts = df_ts.resample(freq)[value_col].sum().fillna(0).to_frame()
        df_ts.columns = [value_col]
        df_ts = df_ts.reset_index()
        
        logger.info(f"Prepared time series data with frequency '{freq}' for '{value_col}'. Rows: {len(df_ts)} (need 16+ for forecasting)")
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

            # Filter out users with too few interactions (with fallback strategy)
            user_counts = user_item_interactions.groupby('userId').size()
            valid_users = user_counts[user_counts >= min_interactions].index
            
            # If no users meet the minimum threshold, try with a lower threshold
            if len(valid_users) == 0:
                fallback_min = max(1, min_interactions - 2)
                logger.warning(f"No users with {min_interactions}+ interactions. Trying fallback with {fallback_min}+ interactions.")
                valid_users = user_counts[user_counts >= fallback_min].index
                
                # If still no users, use all users with at least 1 interaction
                if len(valid_users) == 0:
                    logger.warning("Using all users with at least 1 interaction for recommendation model.")
                    valid_users = user_counts[user_counts >= 1].index
            
            user_item_interactions = user_item_interactions[user_item_interactions['userId'].isin(valid_users)]

            if user_item_interactions.empty:
                logger.warning(f"No user-item interactions found even with fallback strategy.")
                return pd.DataFrame()
            
            logger.info(f"Using {len(valid_users)} users for recommendation model training.")

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

    def prepare_anomaly_detection_data(self, df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
        """
        Prepare data for anomaly detection by selecting and processing features.
        
        Args:
            df: DataFrame containing the data
            feature_cols: List of column names to use as features
            
        Returns:
            DataFrame with selected features ready for anomaly detection
        """
        try:
            if df.empty:
                logger.warning("Empty DataFrame provided for anomaly detection preparation")
                return pd.DataFrame()
            
            # Select only the required feature columns
            available_cols = [col for col in feature_cols if col in df.columns]
            if not available_cols:
                logger.warning(f"None of the requested feature columns {feature_cols} found in DataFrame")
                return pd.DataFrame()
            
            anomaly_data = df[available_cols].copy()
            
            # Handle missing values
            anomaly_data = anomaly_data.fillna(anomaly_data.mean())
            
            logger.info(f"Prepared anomaly detection data with shape: {anomaly_data.shape}")
            return anomaly_data
            
        except Exception as e:
            logger.error(f"Error preparing anomaly detection data: {e}", exc_info=True)
            return pd.DataFrame()

    async def get_transactions_data_for_forecasting(self, days: int = 180, limit: int = 5000) -> pd.DataFrame:
        """
        Get transactions data specifically for forecasting model training.
        Uses a sampling strategy to get distributed data across the entire date range
        rather than just the most recent transactions.
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"Fetching distributed transaction data for forecasting from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} (limit: {limit})")

            # Get a random sample distributed across the date range to ensure we get data from multiple days
            # This uses MongoDB's $sample to get a random distribution rather than just recent data
            transactions_cursor = self._get_async_db().transactions.aggregate([
                {"$match": {"transactionDate": {"$gte": start_date, "$lte": end_date}}},
                {"$sample": {"size": limit}}  # Random sample instead of most recent
            ])
            transactions_list = await transactions_cursor.to_list(length=limit)

            if not transactions_list:
                logger.warning(f"No transaction data found for the last {days} days for forecasting.")
                return pd.DataFrame()

            df = pd.DataFrame(transactions_list)

            # Ensure 'transactionDate' is datetime and then rename to 'timestamp'
            df['transactionDate'] = pd.to_datetime(df['transactionDate'])
            df = df.sort_values('transactionDate').reset_index(drop=True)
            df.rename(columns={'transactionDate': 'timestamp'}, inplace=True)

            # IMPORTANT: Rename 'totalPrice' to 'totalAmount' for consistency with models
            if 'totalPrice' in df.columns:
                df.rename(columns={'totalPrice': 'totalAmount'}, inplace=True)
                df['totalAmount'] = pd.to_numeric(df['totalAmount'], errors='coerce').fillna(0)
            else:
                logger.warning("Column 'totalPrice' not found in transactions data. Forecasting model may fail.")
                df['totalAmount'] = 0.0

            # Ensure 'quantity' is numeric
            if 'quantity' in df.columns:
                df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)

            unique_dates = df['timestamp'].dt.date.nunique()
            logger.info(f"Fetched {len(df)} transactions for forecasting spanning {unique_dates} unique dates.")
            return df

        except Exception as e:
            logger.error(f"Error fetching distributed transaction data for forecasting: {e}", exc_info=True)
            return pd.DataFrame()