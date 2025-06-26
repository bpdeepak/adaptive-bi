# adaptive-bi-system/data_streaming/streaming_etl.py

import pymongo # type: ignore
import time
import random
from datetime import datetime, timedelta
import traceback
import math # For math.ceil
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
                try:
                    self.db.create_collection(col_name)
                    print(f"Created collection: {col_name}")
                except pymongo.errors.CollectionInvalid as e:
                    print(f"Warning: Could not create collection '{col_name}', it might already exist or be in a pending state: {e}")
            else:
                print(f"Collection '{col_name}' already exists.")

    def insert_data(self, collection_name, data_list):
        """Inserts a list of documents into the specified collection."""
        if not data_list:
            return 0
        try:
            collection = self.db[collection_name]
            result = collection.insert_many(data_list, ordered=False) # ordered=False for better performance
            return len(result.inserted_ids)
        except pymongo.errors.BulkWriteError as bwe:
            # Handle cases where some inserts fail (e.g., duplicate _id if not generating unique)
            print(f"Warning: Some data failed to insert into {collection_name} due to BulkWriteError: {bwe.details}")
            return bwe.details.get('nInserted', 0)
        except pymongo.errors.PyMongoError as e:
            print(f"Error inserting data into {collection_name}: {e}")
            return 0

    def get_existing_data_for_generators(self):
        """Fetches existing users and products for relationship generation."""
        users = []
        products = []
        try:
            # Fetch all users, but only required fields
            users = list(self.db.users.find({}, {"_id": 0, "userId": 1, "address": 1}))
            # Fetch all products, but only required fields
            products = list(self.db.products.find({}, {"_id": 0, "productId": 1, "price": 1}))

            # Filter out users/products missing required fields
            users = [u for u in users if "userId" in u and "address" in u]
            products = [p for p in products if "productId" in p and "price" in p]

            print(f"Loaded {len(users)} existing users and {len(products)} existing products.")
        except pymongo.errors.PyMongoError as e:
            print(f"Error fetching existing users/products: {e}")
            traceback.print_exc()
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

        print("Populating initial data if collections are empty...")
        
        all_users = []
        all_products = []

        # Initial population of users
        initial_user_count = data_loader.db.users.count_documents({})
        if initial_user_count < config.NUM_INITIAL_USERS:
            num_to_add = config.NUM_INITIAL_USERS - initial_user_count
            print(f"Generating and inserting {num_to_add} initial users...")
            users_batch = []
            for _ in range(num_to_add):
                users_batch.append(generate_user_data())
                if len(users_batch) >= config.INSERT_BATCH_SIZE:
                    data_loader.insert_data("users", users_batch)
                    all_users.extend(users_batch)
                    users_batch = []
            if users_batch: # Insert remaining
                data_loader.insert_data("users", users_batch)
                all_users.extend(users_batch)
            print(f"Initial users population complete. Total: {data_loader.db.users.count_documents({})}")
        
        # Load existing users if not just populated (or if already existed)
        if not all_users: # Only load if not populated in this run
            all_users = list(data_loader.db.users.find({}, {"_id": 0, "userId": 1, "address": 1}))
            all_users = [u for u in all_users if "userId" in u and "address" in u]
            print(f"Loaded {len(all_users)} existing users.")


        # Initial population of products
        initial_product_count = data_loader.db.products.count_documents({})
        if initial_product_count < config.NUM_INITIAL_PRODUCTS:
            num_to_add = config.NUM_INITIAL_PRODUCTS - initial_product_count
            print(f"Generating and inserting {num_to_add} initial products...")
            products_batch = []
            for _ in range(num_to_add):
                products_batch.append(generate_product_data())
                if len(products_batch) >= config.INSERT_BATCH_SIZE:
                    data_loader.insert_data("products", products_batch)
                    all_products.extend(products_batch)
                    products_batch = []
            if products_batch: # Insert remaining
                data_loader.insert_data("products", products_batch)
                all_products.extend(products_batch)
            print(f"Initial products population complete. Total: {data_loader.db.products.count_documents({})}")
        
        # Load existing products if not just populated
        if not all_products: # Only load if not populated in this run
            all_products = list(data_loader.db.products.find({}, {"_id": 0, "productId": 1, "price": 1}))
            all_products = [p for p in all_products if "productId" in p and "price" in p]
            print(f"Loaded {len(all_products)} existing products.")


        if not all_users or not all_products:
            print("ERROR: Not enough initial users or products available to start streaming. Please check configuration and database.")
            return

        print("\nStarting real-time data streaming simulation with dynamic velocity...")
        print(f"Targeting: {config.STREAMING_VELOCITY_CONFIG['transactions_per_second']} transactions/s, {config.STREAMING_VELOCITY_CONFIG['user_activities_per_second']} activities/s, {config.STREAMING_VELOCITY_CONFIG['feedback_per_minute']} feedback/min.")

        last_report_time = time.time()
        
        # Counters for cumulative records generated since last report
        current_report_transactions = 0
        current_report_activities = 0
        current_report_feedback = 0

        # Cumulative counters for the entire streaming session (since start_streaming_time)
        total_session_transactions = 0
        total_session_activities = 0
        total_session_feedback = 0

        start_streaming_time = time.time() # This marks the true beginning of continuous streaming

        while True:
            current_time = time.time()
            elapsed_time_since_start = current_time - start_streaming_time
            
            # --- Generate Transactions ---
            target_transactions = math.ceil(config.STREAMING_VELOCITY_CONFIG["transactions_per_second"] * elapsed_time_since_start)
            num_transactions_to_generate = target_transactions - total_session_transactions
            
            if num_transactions_to_generate > 0:
                transactions_batch = []
                for _ in range(num_transactions_to_generate):
                    tx = generate_transaction_data(all_users, all_products)
                    if tx:
                        transactions_batch.append(tx)
                if transactions_batch:
                    inserted_count = data_loader.insert_data("transactions", transactions_batch)
                    current_report_transactions += inserted_count
                    total_session_transactions += inserted_count

            # --- Generate User Activities ---
            target_activities = math.ceil(config.STREAMING_VELOCITY_CONFIG["user_activities_per_second"] * elapsed_time_since_start)
            num_activities_to_generate = target_activities - total_session_activities

            if num_activities_to_generate > 0:
                activities_batch = []
                for _ in range(num_activities_to_generate):
                    activity = generate_user_activity_data(all_users, all_products) # Pass products for realism
                    if activity:
                        activities_batch.append(activity)
                if activities_batch:
                    inserted_count = data_loader.insert_data("user_activities", activities_batch)
                    current_report_activities += inserted_count
                    total_session_activities += inserted_count

            # --- Generate Feedback (less frequent) ---
            target_feedback = math.ceil((config.STREAMING_VELOCITY_CONFIG["feedback_per_minute"] / 60) * elapsed_time_since_start)
            num_feedback_to_generate = target_feedback - total_session_feedback

            if num_feedback_to_generate > 0:
                feedback_batch = []
                for _ in range(num_feedback_to_generate):
                    fb = generate_feedback_data(all_users, all_products)
                    if fb:
                        feedback_batch.append(fb)
                if feedback_batch:
                    inserted_count = data_loader.insert_data("feedback", feedback_batch)
                    current_report_feedback += inserted_count
                    total_session_feedback += inserted_count
            
            # --- Occasionally add new users or products to simulate growth ---
            # These are generated and inserted immediately if their probability hits
            if random.random() < config.STREAMING_VELOCITY_CONFIG["new_user_probability_per_batch"]:
                new_user = generate_user_data()
                if "userId" in new_user:
                    data_loader.insert_data("users", [new_user])
                    all_users.append(new_user) # Add to our in-memory list for future relationships
                    # print(f"[{datetime.now().strftime('%H:%M:%S')}] Added a new user: {new_user['userId']}")

            if random.random() < config.STREAMING_VELOCITY_CONFIG["new_product_probability_per_batch"]:
                new_product = generate_product_data()
                if "productId" in new_product:
                    data_loader.insert_data("products", [new_product])
                    all_products.append(new_product) # Add to our in-memory list for future relationships
                    # print(f"[{datetime.now().strftime('%H:%M:%S')}] Added a new product: {new_product['productId']}")
            
            # --- Reporting ---
            if (current_time - last_report_time) >= config.REPORTING_INTERVAL_SECONDS:
                report_interval = current_time - last_report_time
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"T/s: {current_report_transactions / report_interval:.2f} | "
                      f"A/s: {current_report_activities / report_interval:.2f} | "
                      f"F/min: {current_report_feedback / (report_interval / 60):.2f}")
                
                # Reset counters for the next reporting interval
                current_report_transactions = 0
                current_report_activities = 0
                current_report_feedback = 0
                last_report_time = current_time

            # Small sleep to prevent busy-waiting and allow other processes to run
            time.sleep(0.01)

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