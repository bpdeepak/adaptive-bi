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