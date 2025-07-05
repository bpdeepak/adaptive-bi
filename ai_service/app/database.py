import motor.motor_asyncio
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
# Corrected Import: 'settings' should come from the 'app.config' file
from app.config import settings
from app.utils.logger import logger
from typing import Optional, Any

# Async MongoDB client for FastAPI  
client: Optional[Any] = None  # AsyncIOMotorClient
db: Optional[Any] = None  # AsyncIOMotorDatabase

# Synchronous MongoDB client for model training scripts (if needed outside FastAPI context)
sync_client: Optional[MongoClient] = None
sync_db: Optional[Any] = None  # Database object


async def connect_to_mongo(): # Renamed from connect_to_database for consistency with main.py
    """
    Establishes an asynchronous connection to MongoDB.
    """
    global client, db
    try:
        mongo_uri = settings.MONGODB_URL
        logger.info(f"Attempting to connect to MongoDB at: {mongo_uri.split('@')[-1]}") # Log without credentials
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        if client is not None:
            db = client[settings.DATABASE_NAME] # Get the database instance
        
        # Test the connection with a simple ping
        if db is not None:
            await db.command('ping') # Ping the database, not the client directly
        logger.info("MongoDB connection successful!")
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed (ConnectionFailure): {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during MongoDB connection: {e}", exc_info=True)
        raise

async def close_mongo_connection(): # Renamed from close_database_connection
    """
    Closes the asynchronous MongoDB connection.
    """
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")

def get_database() -> Any:
    """
    Returns the asynchronous MongoDB database instance.
    This is used as a FastAPI dependency.
    """
    if db is None: # Check if db (database instance) is none
        logger.error("MongoDB database instance is not initialized. Call connect_to_mongo first.")
        raise ConnectionFailure("MongoDB database instance is not initialized.")
    return db

# --- Synchronous connection functions (if needed, otherwise can be removed) ---
def connect_to_sync_database():
    """
    Establishes a synchronous connection to MongoDB.
    Used for scripts that might not run within an async context directly.
    """
    global sync_client, sync_db
    try:
        sync_client = MongoClient(settings.MONGODB_URL)
        sync_db = sync_client[settings.DATABASE_NAME]
        sync_db.command('ping') # Test connection
        logger.info(f"Successfully connected to synchronous MongoDB at {settings.MONGODB_URL.split('@')[-1]}")
    except ConnectionFailure as e:
        logger.error(f"Synchronous MongoDB connection failed (ConnectionFailure): {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during synchronous MongoDB connection: {e}", exc_info=True)
        raise

def close_sync_database_connection():
    """
    Closes the synchronous MongoDB connection.
    """
    global sync_client
    if sync_client:
        sync_client.close()
        logger.info("Synchronous MongoDB connection closed.")

def get_sync_database():
    """
    Returns the synchronous MongoDB database instance.
    """
    return sync_db

if __name__ == "__main__":
    import asyncio

    # Test async connection
    async def test_async_db():
        try:
            await connect_to_mongo() # Use connect_to_mongo
            if db is not None:
                logger.info("Async DB connection test successful.")
                collections = await db.list_collection_names()
                logger.info(f"Collections: {collections}")
            else:
                logger.error("Async DB connection test failed: db object is None.")
        except Exception as e:
            logger.error(f"Async DB connection test encountered an error: {e}")
        finally:
            await close_mongo_connection() # Use close_mongo_connection

    asyncio.run(test_async_db())

    # Test sync connection
    try:
        connect_to_sync_database()
        if sync_db:
            logger.info("Sync DB connection test successful.")
            collections = sync_db.list_collection_names()
            logger.info(f"Collections: {collections}")
        else:
            logger.error("Sync DB connection test failed: sync_db object is None.")
    except Exception as e:
        logger.error(f"Sync DB connection test encountered an error: {e}")
    finally:
        close_sync_database_connection()
