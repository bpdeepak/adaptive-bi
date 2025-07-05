# adaptive-bi-system/data_streaming/config.py

import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class Config:
    """
    Configuration settings for the data streaming service.
    Loads values from environment variables defined in .env.
    """
    # MongoDB Connection Details (consistent with docker-compose.yml for host/port)
    MONGO_USERNAME: str = os.getenv('MONGO_USERNAME', 'admin')
    MONGO_PASSWORD: str = os.getenv('MONGO_PASSWORD', 'admin123')
    # Use 'mongodb' for Docker internal communication, 'localhost' for host-based execution
    # Clean the MONGO_HOST to remove any comments or extra text
    MONGO_HOST: str = os.getenv('MONGO_HOST', 'mongodb').split('#')[0].strip()
    MONGO_PORT: int = int(os.getenv('MONGO_PORT', 27017))
    MONGO_DB_NAME: str = os.getenv('MONGO_DB_NAME', 'adaptive_bi')
    
    # Construct MONGO_URI from components for clarity
    MONGO_URI: str = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource=admin"

    # --- Initial Data Population Settings ---
    # These numbers determine the initial size of the user and product pools.
    NUM_INITIAL_USERS: int = int(os.getenv("NUM_INITIAL_USERS", 5000)) # Increased for more users
    NUM_INITIAL_PRODUCTS: int = int(os.getenv("NUM_INITIAL_PRODUCTS", 1000)) # Increased for more products

    # --- Streaming Velocity Control (Records per unit of time) ---
    # These define the AVERAGE rate of generation.
    # Adjust these values to control the overall data velocity.
    STREAMING_VELOCITY_CONFIG = {
        "transactions_per_second": int(os.getenv("TRANSACTIONS_PER_SECOND", 100)), # E.g., 100 transactions per second
        "user_activities_per_second": int(os.getenv("USER_ACTIVITIES_PER_SECOND", 250)), # E.g., 250 user activities per second
        "feedback_per_minute": int(os.getenv("FEEDBACK_PER_MINUTE", 15)), # E.g., 15 feedback entries per minute
        "new_user_probability_per_batch": float(os.getenv("NEW_USER_PROBABILITY_PER_BATCH", 0.0005)), # Probability of adding a new user per generation cycle
        "new_product_probability_per_batch": float(os.getenv("NEW_PRODUCT_PROBABILITY_PER_BATCH", 0.0002)), # Probability of adding a new product per generation cycle
    }
    
    # Batch size for inserting data into MongoDB
    # Larger batches are generally more efficient for high velocity.
    INSERT_BATCH_SIZE: int = int(os.getenv("INSERT_BATCH_SIZE", 1000))

    # How often to print streaming statistics (in seconds)
    REPORTING_INTERVAL_SECONDS: int = int(os.getenv("REPORTING_INTERVAL_SECONDS", 10))


# Instantiate config
config = Config()

if __name__ == "__main__":
    print("--- Streaming Config ---")
    print(f"MongoDB URI: {config.MONGO_URI.split('@')[-1] if '@' in config.MONGO_URI else config.MONGO_URI}")
    print(f"DB Name: {config.MONGO_DB_NAME}")
    print(f"Initial Users: {config.NUM_INITIAL_USERS}")
    print(f"Initial Products: {config.NUM_INITIAL_PRODUCTS}")
    print("\n--- Velocity Settings ---")
    for k, v in config.STREAMING_VELOCITY_CONFIG.items():
        print(f"  {k}: {v}")
    print(f"Insert Batch Size: {config.INSERT_BATCH_SIZE}")
    print(f"Reporting Interval: {config.REPORTING_INTERVAL_SECONDS} seconds")
    print("------------------------")