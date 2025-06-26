# adaptive-bi-system/data_streaming/streaming_etl.py
import pymongo # type: ignore
import time
import random
from datetime import datetime, timedelta
import traceback
from data_generator import (
    generate_user_data,
    generate_product_data,
    generate_transaction_data,
    generate_feedback_data,
    generate_user_activity_data
)
from config import config # Import configuration settings

class MongoDBDataLoader:
    """
    Handles connection to MongoDB and loading of synthetic e-commerce data.
    """
    def __init__(self, mongo_uri, db_name):
        self.client = None
        self.db = None
        try:
            self.client = pymongo.MongoClient(mongo_uri)
            self.db = self.client[db_name]
            # The ping command is cheap and does not require auth.
            self.client.admin.command('ping') 
            print("Successfully connected to MongoDB!")
        except pymongo.errors.ConnectionFailure as e:
            print(f"Could not connect to MongoDB: {e}")
            raise

    def create_collections_if_not_exists(self, collections_list):
        """Ensures that specified collections exist in the database."""
        for col_name in collections_list:
            if col_name not in self.db.list_collection_names():
                self.db.create_collection(col_name)
                print(f"Created collection: {col_name}")
            else:
                print(f"Collection '{col_name}' already exists.")

    def insert_data(self, collection_name, data_list):
        """Inserts a list of documents into the specified collection."""
        if not data_list:
            return 0
        try:
            collection = self.db[collection_name]
            result = collection.insert_many(data_list)
            return len(result.inserted_ids)
        except pymongo.errors.PyMongoError as e:
            print(f"Error inserting data into {collection_name}: {e}")
            return 0

    def get_existing_ids(self, collection_name, id_field):
        """Fetches existing IDs from a collection."""
        collection = self.db[collection_name]
        return set(doc[id_field] for doc in collection.find({}, {id_field: 1}))
        
    def get_sample_users_products(self):
        """Fetches a sample of users and products for transaction/feedback generation."""
        users = list(self.db.users.find({}, {"_id": 0, "userId": 1, "address": 1}).limit(1000))
        products = list(self.db.products.find({}, {"_id": 0, "productId": 1, "price": 1}).limit(1000))

        # Filter out users/products missing required fields
        users = [u for u in users if "userId" in u and "address" in u]
        products = [p for p in products if "productId" in p and "price" in p]

        return users, products


    def close(self):
        """Closes the MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")

def run_streaming():
    """
    Main function to run the data streaming process.
    Generates synthetic data and inserts it into MongoDB continuously.
    """
    collections_to_manage = ["users", "products", "transactions", "feedback", "user_activities"]
    data_loader = None
    try:
        data_loader = MongoDBDataLoader(config.MONGO_URI, config.MONGO_DB_NAME)
        data_loader.create_collections_if_not_exists(collections_to_manage)

        print("Checking for initial data population...")
        
        # Initial population of users and products
        initial_user_count = data_loader.db.users.count_documents({})
        initial_product_count = data_loader.db.products.count_documents({})

        if initial_user_count < config.NUM_INITIAL_USERS:
            num_to_add = config.NUM_INITIAL_USERS - initial_user_count
            print(f"Populating {num_to_add} initial users...")
            users_to_insert = [generate_user_data() for _ in range(num_to_add)]
            inserted_count = data_loader.insert_data("users", users_to_insert)
            print(f"Inserted {inserted_count} initial users.")
        else:
            print("Enough initial users exist.")

        if initial_product_count < config.NUM_INITIAL_PRODUCTS:
            num_to_add = config.NUM_INITIAL_PRODUCTS - initial_product_count
            print(f"Populating {num_to_add} initial products...")
            products_to_insert = [generate_product_data() for _ in range(num_to_add)]
            inserted_count = data_loader.insert_data("products", products_to_insert)
            print(f"Inserted {inserted_count} initial products.")
        else:
            print("Enough initial products exist.")

        print("\nStarting real-time data streaming...")
        print(f"Streaming interval: {config.STREAM_INTERVAL_SECONDS} seconds.")
        print("Press Ctrl+C to stop the streaming.")

        while True:
            current_users, current_products = data_loader.get_sample_users_products()

            # --- Stream new transactions ---
            num_transactions = random.randint(1, config.MAX_TRANSACTIONS_PER_STREAM)
            transactions_to_insert = []
            for _ in range(num_transactions):
                tx = generate_transaction_data(current_users, current_products)
                if tx:
                    transactions_to_insert.append(tx)
            if transactions_to_insert:
                inserted_count = data_loader.insert_data("transactions", transactions_to_insert)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Inserted {inserted_count} transactions.")

            # --- Stream new feedback (optional) ---
            num_feedback = random.randint(0, config.MAX_FEEDBACK_PER_STREAM)
            feedback_to_insert = []
            for _ in range(num_feedback):
                fb = generate_feedback_data(current_users, current_products)
                if fb:
                    feedback_to_insert.append(fb)
            if feedback_to_insert:
                inserted_count = data_loader.insert_data("feedback", feedback_to_insert)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Inserted {inserted_count} feedback entries.")

            # --- Stream new user activities ---
            num_user_activities = random.randint(1, config.MAX_TRANSACTIONS_PER_STREAM + config.MAX_FEEDBACK_PER_STREAM)
            user_activities_to_insert = []
            for _ in range(num_user_activities):
                activity = generate_user_activity_data(current_users)
                if activity:
                    user_activities_to_insert.append(activity)
            if user_activities_to_insert:
                inserted_count = data_loader.insert_data("user_activities", user_activities_to_insert)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Inserted {inserted_count} user activities.")

            # --- Occasionally add new users or products to simulate growth ---
            if random.random() < config.NEW_USER_PROBABILITY:
                new_user = generate_user_data()
                if "userId" in new_user:
                    data_loader.insert_data("users", [new_user])
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Added a new user: {new_user['userId']}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Warning: Generated user missing 'userId': {new_user}")

            if random.random() < config.NEW_PRODUCT_PROBABILITY:
                new_product = generate_product_data()
                if "productId" in new_product:
                    data_loader.insert_data("products", [new_product])
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Added a new product: {new_product['productId']}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Warning: Generated product missing 'productId': {new_product}")

            time.sleep(config.STREAM_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nStreaming stopped by user.")
    except Exception as e:
        print("An unexpected error occurred during streaming:")
        traceback.print_exc()
    finally:
        if data_loader:
            data_loader.close()

if __name__ == "__main__":
    print("Starting Data Streaming Service for Adaptive BI System...")
    run_streaming()