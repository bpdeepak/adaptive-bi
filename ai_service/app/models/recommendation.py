import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
import joblib
import os
from typing import Optional
from app.config import settings
from app.utils.logger import logger
from app.services.data_processor import DataProcessor

class RecommendationModel:
    """
    Implements a recommendation system using collaborative filtering (SVD).
    """
    def __init__(self, model_type: str = settings.RECOMMENDER_MODEL_TYPE, n_components: int = 50):
        self.model = None
        self.model_type = model_type
        self.n_components = n_components
        self.user_item_matrix = None # Stores the user-item interaction matrix
        self.user_mapper = {} # Map original user IDs to matrix indices
        self.item_mapper = {} # Map original item IDs to matrix indices
        self.user_inverse_mapper = {} # Map matrix indices back to original user IDs
        self.item_inverse_mapper = {} # Map matrix indices back to original item IDs
        self.model_path = os.path.join(settings.MODEL_SAVE_PATH, f"recommendation_model_{model_type}.joblib")
        self.is_trained = False

    async def train(self, data_processor: DataProcessor) -> dict:
        """
        Trains the recommendation model.
        Expects a DataProcessor instance to fetch user-item interaction data.
        """
        logger.info("Starting training for recommendation model...")
        self.user_item_matrix = await data_processor.get_user_item_matrix()

        if self.user_item_matrix.empty:
            logger.warning("No user-item interaction data to train recommendation model.")
            return {"status": "failed", "message": "No data for training."}

        # Log matrix dimensions for debugging
        logger.info(f"User-item matrix shape: {self.user_item_matrix.shape} (users: {self.user_item_matrix.shape[0]}, items: {self.user_item_matrix.shape[1]})")

        # Create mappers for user and item IDs
        self.user_mapper = {user_id: idx for idx, user_id in enumerate(self.user_item_matrix.index)}
        self.item_mapper = {item_id: idx for idx, item_id in enumerate(self.user_item_matrix.columns)}
        self.user_inverse_mapper = {idx: user_id for user_id, idx in self.user_mapper.items()}
        self.item_inverse_mapper = {idx: item_id for item_id, idx in self.item_mapper.items()}

        # Convert to sparse matrix for SVD
        sparse_user_item = csr_matrix(self.user_item_matrix.values)

        if self.model_type == "SVD":
            # Adjust n_components based on matrix dimensions to avoid errors
            max_components = min(self.user_item_matrix.shape) - 1
            actual_components = min(self.n_components, max_components, 50)  # Cap at 50 for performance
            
            if actual_components <= 0:
                logger.warning(f"Cannot create SVD model: insufficient data dimensions {self.user_item_matrix.shape}")
                return {"status": "failed", "message": "Insufficient data dimensions for SVD."}
            
            self.model = TruncatedSVD(n_components=actual_components, random_state=42)
            logger.info(f"Initialized TruncatedSVD with {actual_components} components (requested {self.n_components}, max possible {max_components}).")
        # elif self.model_type == "KNNWithMeans":
            # For KNN based models, you'd typically use surprise library or custom implementation
            # self.model = ...
        else:
            raise ValueError(f"Unsupported recommendation model type: {self.model_type}")

        try:
            self.model.fit(sparse_user_item)
            self.is_trained = True
            logger.info(f"Recommendation model training complete. Matrix sparsity: {(sparse_user_item.nnz / (sparse_user_item.shape[0] * sparse_user_item.shape[1]) * 100):.2f}%")
            self.save_model()
            
            # Return training metrics
            return {
                "status": "success", 
                "message": "Recommendation model trained successfully.",
                "metrics": {
                    "users": self.user_item_matrix.shape[0],
                    "items": self.user_item_matrix.shape[1],
                    "components": actual_components,
                    "total_interactions": int(sparse_user_item.nnz),
                    "sparsity_percentage": round((sparse_user_item.nnz / (sparse_user_item.shape[0] * sparse_user_item.shape[1]) * 100), 2)
                }
            }
        except Exception as e:
            logger.error(f"Error during recommendation model training: {e}")
            return {"status": "failed", "message": f"Training error: {str(e)}"}

    def _get_popular_recommendations(self, num_recommendations: int = 10, product_data: Optional[pd.DataFrame] = None):
        """
        Provides general popular recommendations (e.g., for cold-start users).
        """
        logger.info("Providing popular recommendations (cold-start strategy).")
        if self.user_item_matrix is not None and not self.user_item_matrix.empty:
            # Sum interactions for each item
            item_popularity = self.user_item_matrix.sum(axis=0).sort_values(ascending=False)
            popular_item_ids = item_popularity.index.tolist()[:num_recommendations]
            
            # If product_data is available, try to get names
            if product_data is not None and not product_data.empty:
                popular_products_info = product_data[product_data['productId'].isin(popular_item_ids)]
                return popular_products_info[['productId', 'name']].to_dict(orient='records')
            return [{"productId": pid} for pid in popular_item_ids]
        
        logger.warning("No user-item matrix available to determine popularity. Returning empty list.")
        return []

    async def get_user_recommendations(self, user_id: str, num_recommendations: int = 10, product_data: Optional[pd.DataFrame] = None):
        """
        Generates personalized product recommendations for a given user.
        """
        if not self.is_trained or self.model is None or self.user_item_matrix is None:
            logger.warning("Recommendation model not trained or data not loaded. Providing popular recommendations.")
            return self._get_popular_recommendations(num_recommendations, product_data)

        if user_id not in self.user_mapper:
            logger.warning(f"User {user_id} not found in training data. Providing popular recommendations.")
            return self._get_popular_recommendations(num_recommendations, product_data)

        user_idx = self.user_mapper[user_id]
        user_vector = self.user_item_matrix.iloc[user_idx]

        # Reconstruct the original matrix from SVD components (approximation)
        if self.model_type == "SVD":
            reconstructed_matrix = np.dot(self.model.transform(csr_matrix(self.user_item_matrix.values)), self.model.components_)
            # Convert back to DataFrame for easy indexing
            reconstructed_df = pd.DataFrame(reconstructed_matrix, index=self.user_item_matrix.index, columns=self.user_item_matrix.columns)
            
            # Get predicted ratings for the user
            user_predicted_ratings = reconstructed_df.loc[user_id]

            # Filter out items the user has already interacted with
            user_interacted_items = user_vector[user_vector > 0].index
            recommendations_series = user_predicted_ratings.drop(user_interacted_items, errors='ignore')

            # Sort and get top N recommendations
            if isinstance(recommendations_series, pd.Series):
                top_recommendations = recommendations_series.sort_values(ascending=False).head(num_recommendations).index.tolist()
            else:
                # Convert to Series if not already
                # If recommendations_series is a DataFrame, select the first row as a Series
                if isinstance(recommendations_series, pd.DataFrame):
                    recommendations_series = recommendations_series.iloc[0]
                top_recommendations = recommendations_series.sort_values(ascending=False).head(num_recommendations).index.tolist()
        else:
            logger.warning(f"Recommendation type {self.model_type} not fully implemented for prediction logic. Returning popular.")
            return self._get_popular_recommendations(num_recommendations, product_data)

        logger.info(f"Generated {len(top_recommendations)} recommendations for user {user_id}.")
        
        # Fetch product details if product_data is available
        if product_data is not None and not product_data.empty:
            recommended_products_info = product_data[product_data['productId'].isin(top_recommendations)]
            # Ensure order based on ranking
            product_dict = recommended_products_info.set_index('productId').T.to_dict('list')
            ordered_recommendations = []
            for prod_id in top_recommendations:
                if prod_id in product_dict:
                    ordered_recommendations.append({"productId": prod_id, "name": product_dict[prod_id][0]}) # Assuming name is first item
            return ordered_recommendations
        
        return [{"productId": pid} for pid in top_recommendations]


    def save_model(self):
        """Saves the trained model, user-item matrix, and mappers."""
        if self.model:
            os.makedirs(settings.MODEL_SAVE_PATH, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.user_item_matrix, os.path.join(settings.MODEL_SAVE_PATH, "user_item_matrix.joblib"))
            joblib.dump(self.user_mapper, os.path.join(settings.MODEL_SAVE_PATH, "user_mapper.joblib"))
            joblib.dump(self.item_mapper, os.path.join(settings.MODEL_SAVE_PATH, "item_mapper.joblib"))
            joblib.dump(self.user_inverse_mapper, os.path.join(settings.MODEL_SAVE_PATH, "user_inverse_mapper.joblib"))
            joblib.dump(self.item_inverse_mapper, os.path.join(settings.MODEL_SAVE_PATH, "item_inverse_mapper.joblib"))
            logger.info(f"Recommendation model and associated data saved to {self.model_path}")
        else:
            logger.warning("No recommendation model to save.")

    def load_model(self):
        """Loads the trained model, user-item matrix, and mappers."""
        try:
            self.model = joblib.load(self.model_path)
            self.user_item_matrix = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "user_item_matrix.joblib"))
            self.user_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "user_mapper.joblib"))
            self.item_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "item_mapper.joblib"))
            self.user_inverse_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "user_inverse_mapper.joblib"))
            self.item_inverse_mapper = joblib.load(os.path.join(settings.MODEL_SAVE_PATH, "item_inverse_mapper.joblib"))
            self.is_trained = True
            logger.info(f"Recommendation model and associated data loaded from {self.model_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Recommendation model not found at {self.model_path}. Model needs to be trained.")
            self.is_trained = False
            return False
        except Exception as e:
            logger.error(f"Error loading recommendation model: {e}", exc_info=True)
            self.is_trained = False
            return False