import joblib
import os
import logging
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ModelUtils:
    """
    Utility class for saving, loading, and managing machine learning models.
    """

    def __init__(self, model_dir: str = 'models/saved_models'):
        # Adjust model_dir to be relative to the app directory if this utility
        # is called from within the app. For consistency with a consolidated app/ structure,
        # it's better to manage model paths dynamically or through a central config.
        # However, if 'models/saved_models' is relative to the *root* of the project,
        # then this path is fine. Assuming BASE_MODEL_DIR from ModelConfig is used by services.
        self.model_dir = model_dir 
        os.makedirs(self.model_dir, exist_ok=True) # Ensure the directory exists

    def save_model(self, model: Any, model_name: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Saves a trained model to disk along with optional metadata.
        Args:
            model: The trained machine learning model object.
            model_name: A unique name for the model (e.g., 'dynamic_pricing_v1').
            metadata: Optional dictionary of metadata (e.g., training date, metrics).
        Returns:
            A dictionary with status and path.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{model_name}_{timestamp}.pkl" # Using .pkl for joblib files
            filepath = os.path.join(self.model_dir, filename)
            
            model_data = {
                'model': model,
                'metadata': metadata if metadata is not None else {},
                'saved_at': datetime.utcnow().isoformat()
            }
            joblib.dump(model_data, filepath)
            logger.info(f"Model '{model_name}' saved to {filepath}")
            return {'status': 'success', 'path': filepath, 'filename': filename}
        except Exception as e:
            logger.error(f"Error saving model '{model_name}': {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def load_latest_model(self, model_name_prefix: str) -> Optional[Any]:
        """
        Loads the latest version of a model based on its name prefix.
        Assumes model files are named like 'model_name_prefix_YYYYMMDD_HHMMSS.pkl'.
        Args:
            model_name_prefix: The prefix of the model name (e.g., 'dynamic_pricing').
        Returns:
            The loaded model object (the 'model' itself from the saved dictionary) or None if not found.
        """
        try:
            # List files that match the prefix and .pkl extension
            model_files = [f for f in os.listdir(self.model_dir) if f.startswith(model_name_prefix) and f.endswith('.pkl')]
            
            if not model_files:
                logger.warning(f"No model files found for prefix '{model_name_prefix}' in {self.model_dir}")
                return None
            
            # Sort files by timestamp in descending order to get the latest
            # Expecting format: {model_name_prefix}_{YYYYMMDD}_{HHMMSS}.pkl
            def get_timestamp_from_filename(filename):
                parts = filename.split('_')
                if len(parts) >= 3:
                    try:
                        date_str = parts[-2] # YYYYMMDD
                        time_str = parts[-1].split('.')[0] # HHMMSS
                        return datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    except ValueError:
                        logger.warning(f"Could not parse timestamp from filename: {filename}")
                        return datetime.min # Return a very old date if parsing fails
                return datetime.min # Return a very old date if format is unexpected

            model_files.sort(key=get_timestamp_from_filename, reverse=True)
            
            latest_file = model_files[0]
            filepath = os.path.join(self.model_dir, latest_file)
            
            model_data = joblib.load(filepath)
            logger.info(f"Loaded latest model '{model_name_prefix}' from {latest_file}")
            return model_data.get('model') # Return the 'model' object
        except Exception as e:
            logger.error(f"Error loading latest model '{model_name_prefix}': {str(e)}", exc_info=True)
            return None

    def load_model_by_path(self, filepath: str) -> Optional[Any]:
        """
        Loads a model from a specific file path.
        Args:
            filepath: The full path to the model file.
        Returns:
            The loaded model object (the 'model' itself from the saved dictionary) or None if not found.
        """
        try:
            if not os.path.exists(filepath):
                logger.warning(f"Model file not found at {filepath}")
                return None
            
            model_data = joblib.load(filepath)
            logger.info(f"Loaded model from {filepath}")
            return model_data.get('model') # Return the 'model' object
        except Exception as e:
            logger.error(f"Error loading model from {filepath}: {str(e)}", exc_info=True)
            return None
            
    def get_model_metadata(self, filepath: str) -> Optional[Dict]:
        """
        Retrieves metadata associated with a saved model.
        """
        try:
            if not os.path.exists(filepath):
                logger.warning(f"Model file not found at {filepath}")
                return None
            model_data = joblib.load(filepath)
            return model_data.get('metadata', {})
        except Exception as e:
            logger.error(f"Error getting metadata for model at {filepath}: {str(e)}", exc_info=True)
            return None

