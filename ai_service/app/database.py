import motor.motor_asyncio
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import settings
from app.utils.logger import logger

# Async MongoDB client for FastAPI
client = None
db = None

# Synchronous MongoDB client for model training scripts (if needed outside FastAPI context)
sync_client = None
sync_db = None

async def connect_to_database():
    """
    Establishes an asynchronous connection to MongoDB.
    """
    global client, db
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        # The ping command is cheap and does not require auth.
        await db.command('ping')
        logger.info(f"Successfully connected to MongoDB at {settings.MONGODB_URL.split('@')[-1]}")
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed (ConnectionFailure): {e}")
        # Optionally re-raise or exit if DB is critical for startup
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during MongoDB connection: {e}")
        raise

async def close_database_connection():
    """
    Closes the asynchronous MongoDB connection.
    """
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    """
    Returns the asynchronous MongoDB database instance.
    """
    return db

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
        logger.error(f"Synchronous MongoDB connection failed (ConnectionFailure): {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during synchronous MongoDB connection: {e}")
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
            await connect_to_database()
            if db is not None:
                logger.info("Async DB connection test successful.")
                collections = await db.list_collection_names()
                logger.info(f"Collections: {collections}")
            else:
                logger.error("Async DB connection test failed: db object is None.")
        except Exception as e:
            logger.error(f"Async DB connection test encountered an error: {e}")
        finally:
            await close_database_connection()

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