# adaptive-bi-system/data_streaming/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration settings for the data streaming service.
    Loads values from environment variables defined in .env.
    """
    MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')
    MONGO_HOST = os.getenv('MONGO_HOST', 'localhost') # Use 'mongodb' if running in Docker network
    MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'adaptive_bi')
    
    # Construct MONGO_URI based on whether it's a Docker internal call or external
    # If MONGO_HOST is 'mongodb' (docker service name), it implies internal Docker communication
    if MONGO_HOST == 'mongodb':
        MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource=admin"
    else: # Assume localhost or external IP
        MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource=admin"

    STREAM_INTERVAL_SECONDS = float(os.getenv('STREAM_INTERVAL_SECONDS', 0.5))

    # Data generation parameters
    NUM_INITIAL_USERS = int(os.getenv('NUM_INITIAL_USERS', 100))
    NUM_INITIAL_PRODUCTS = int(os.getenv('NUM_INITIAL_PRODUCTS', 50))
    MAX_TRANSACTIONS_PER_STREAM = int(os.getenv('MAX_TRANSACTIONS_PER_STREAM', 10))
    MAX_FEEDBACK_PER_STREAM = int(os.getenv('MAX_FEEDBACK_PER_STREAM', 3))
    NEW_USER_PROBABILITY = float(os.getenv('NEW_USER_PROBABILITY', 0.05)) # 5% chance
    NEW_PRODUCT_PROBABILITY = float(os.getenv('NEW_PRODUCT_PROBABILITY', 0.02)) # 2% chance

# Instantiate config
config = Config()

if __name__ == "__main__":
    print("--- Current Configuration ---")
    print(f"MONGO_URI: {config.MONGO_URI}")
    print(f"STREAM_INTERVAL_SECONDS: {config.STREAM_INTERVAL_SECONDS}")
    print(f"NUM_INITIAL_USERS: {config.NUM_INITIAL_USERS}")
    print(f"NUM_INITIAL_PRODUCTS: {config.NUM_INITIAL_PRODUCTS}")
    print("-----------------------------")