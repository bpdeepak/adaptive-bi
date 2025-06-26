# adaptive-bi-system/data_streaming/data_generator.py

import uuid
import random
from datetime import datetime, timedelta
from faker import Faker # type: ignore

# --- Configuration Constants for Data Generation Realism ---
NUM_USERS_TO_GENERATE = 500         # Initial pool of users
NUM_PRODUCTS_TO_GENERATE = 300      # Initial pool of products
TRANSACTION_HISTORY_DAYS = 180      # Transactions span last 6 months
FEEDBACK_HISTORY_DAYS = 60          # Feedback for last 2 months (more recent)
ACTIVITY_HISTORY_DAYS = 30          # User activities for last 1 month (very recent)

# Probability distribution for transaction quantity (biased towards lower quantities)
TRANSACTION_QUANTITY_DIST = {1: 0.5, 2: 0.3, 3: 0.15, 4: 0.04, 5: 0.01}
# Ensure sum is 1.0, and map to actual quantities
TRANSACTION_QUANTITIES = list(TRANSACTION_QUANTITY_DIST.keys())
TRANSACTION_WEIGHTS = list(TRANSACTION_QUANTITY_DIST.values())

fake = Faker()

def generate_user_data(existing_user_ids: set = None):
    """Generates a synthetic user record."""
    if existing_user_ids is None:
        existing_user_ids = set()

    user_id = str(uuid.uuid4())
    # In a high-velocity scenario, this loop for uniqueness might be a bottleneck
    # If using a database, check uniqueness at DB level or pre-generate IDs.
    # For now, it's fine for initial generation.
    while user_id in existing_user_ids:
        user_id = str(uuid.uuid4())

    # User registration and last login dates spread over a wider period
    registration_date = fake.date_time_between(start_date="-3y", end_date="-1y")
    last_login = fake.date_time_between(start_date=registration_date, end_date="now")

    return {
        "userId": user_id,
        "username": fake.user_name(),
        "email": fake.email(),
        "registrationDate": registration_date,
        "lastLogin": last_login,
        "address": {
            "street": fake.street_address(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "zipCode": fake.postcode(),
            "country": fake.country_code()
        },
        "createdAt": datetime.now(),
        "updatedAt": datetime.now()
    }

def generate_product_data(existing_product_ids: set = None):
    """Generates a synthetic product record."""
    if existing_product_ids is None:
        existing_product_ids = set()

    product_id = str(uuid.uuid4())
    while product_id in existing_product_ids:
        product_id = str(uuid.uuid4())

    categories = ["Electronics", "Books", "Home & Kitchen", "Apparel", "Sports", "Beauty", "Automotive", "Food & Beverage", "Toys", "Health"]
    product_base_names = {
        "Electronics": ["Smartphone", "Laptop", "Headphones", "Smartwatch", "Camera", "Drone", "Tablet", "Gaming Console"],
        "Books": ["Fiction Novel", "Textbook", "Cookbook", "Mystery Thriller", "Biography", "Science Fiction", "Self-Help"],
        "Home & Kitchen": ["Coffee Maker", "Blender", "Toaster", "Vacuum Cleaner", "Air Fryer", "Microwave", "Dishwasher", "Cookware Set"],
        "Apparel": ["T-Shirt", "Jeans", "Jacket", "Sneakers", "Dress", "Hoodie", "Socks", "Hat"],
        "Sports": ["Dumbbells", "Yoga Mat", "Basketball", "Running Shoes", "Tent", "Bicycle", "Swim Goggles", "Football"],
        "Beauty": ["Moisturizer", "Perfume", "Lipstick", "Shampoo", "Face Mask", "Sunscreen", "Hair Dryer", "Nail Polish"],
        "Automotive": ["Car Charger", "Dash Cam", "Tire Inflator", "Jump Starter", "Seat Cover", "Floor Mats", "Windshield Wipers"],
        "Food & Beverage": ["Organic Coffee", "Herbal Tea", "Protein Bar", "Gourmet Snacks", "Energy Drink", "Fruit Juice"],
        "Toys": ["Building Blocks", "Action Figure", "Doll", "Remote Control Car", "Board Game", "Puzzle"],
        "Health": ["Vitamins", "Protein Powder", "Bandages", "Thermometer", "Hand Sanitizer", "First Aid Kit"]
    }

    category = random.choice(categories)
    name_pool = product_base_names.get(category, ["Generic Item"])
    base_name = random.choice(name_pool)

    # Generate more realistic prices (e.g., log-normal distribution for some items)
    # Most prices around 100-500, but some can be higher.
    if category in ["Electronics", "Automotive"]:
        price = round(random.lognormvariate(mu=5.5, sigma=0.8), 2) # Higher prices
    else:
        price = round(random.lognormvariate(mu=4.5, sigma=0.5), 2) # More common prices

    price = max(10.0, min(price, 2500.0)) # Cap prices

    return {
        "productId": product_id,
        "name": f"{base_name} {fake.color_name()} Edition" if random.random() < 0.3 else f"{base_name} {fake.word().capitalize()}",
        "category": category,
        "price": price,
        "stock": random.randint(0, 1000) if random.random() < 0.9 else random.randint(0, 20), # Most are well stocked, some low
        "description": fake.paragraph(nb_sentences=random.randint(1, 3)),
        "imageUrl": f"https://placehold.co/150x150/{random.choice(['FF0000', '00FF00', '0000FF'])}/{random.choice(['FFFFFF', '000000'])}?text={category[:3]}-{base_name.split(' ')[0]}", # More generic placeholders
        "addedDate": fake.date_time_between(start_date="-2y", end_date="-6m"), # Products are not all new
        "lastUpdated": datetime.now()
    }

def generate_transaction_data(users: list, products: list):
    """Generates a synthetic transaction record."""
    if not users or not products:
        return None

    user = random.choice(users)
    product = random.choice(products)
    
    # Random quantity based on predefined distribution
    quantity = random.choices(TRANSACTION_QUANTITIES, weights=TRANSACTION_WEIGHTS, k=1)[0]
    total_price = round(product['price'] * quantity, 2)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=TRANSACTION_HISTORY_DAYS)
    transaction_date = fake.date_time_between(start_date=start_date, end_date=end_date)
    
    status_choices = ["completed", "completed", "completed", "pending", "failed", "returned"] # Completed is more common
    payment_methods = ["credit_card", "paypal", "bank_transfer", "google_pay", "apple_pay", "crypto"]

    return {
        "transactionId": str(uuid.uuid4()),
        "userId": user['userId'],
        "productId": product['productId'],
        "quantity": quantity,
        "totalPrice": total_price,
        "transactionDate": transaction_date,
        "status": random.choice(status_choices),
        "paymentMethod": random.choice(payment_methods),
        "shippingAddress": user['address'], # Reuse user's address for realism
        "createdAt": datetime.now()
    }

def generate_feedback_data(users: list, products: list):
    """Generates a synthetic feedback record."""
    if not users or not products:
        return None

    user = random.choice(users)
    product = random.choice(products)

    comments = [
        "Absolutely love it! Exceeded my expectations.",
        "Solid product for the price. Works as advertised.",
        "It's okay, but there are better options out there.",
        "Highly disappointed, not worth the money.",
        "Fast delivery and great customer support, product is decent.",
        "Perfect for my needs, simple and effective.",
        "The quality feels cheap, I regret buying this.",
        "Surprisingly good, a hidden gem!",
        "Could use some improvements, but overall not bad.",
        "Exactly what I was looking for, highly satisfied.",
        "Came damaged, had to return.",
        "Intuitive to use, a pleasure to own.",
        "The color is not what I expected.",
        "Battery life is terrible.",
        "Worth every penny!"
    ]
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=FEEDBACK_HISTORY_DAYS)
    feedback_date = fake.date_time_between(start_date=start_date, end_date=end_date)

    return {
        "feedbackId": str(uuid.uuid4()),
        "userId": user['userId'],
        "productId": product['productId'],
        "rating": random.choices([5, 4, 3, 2, 1], weights=[0.5, 0.3, 0.1, 0.05, 0.05], k=1)[0], # Biased towards higher ratings
        "comment": random.choice(comments),
        "feedbackDate": feedback_date,
        "createdAt": datetime.now()
    }

def generate_user_activity_data(users: list, products: list = None):
    """Generates a synthetic user activity record."""
    if not users:
        return None
    user = random.choice(users)
    
    activity_types_weights = {
        "viewed_product": 0.4,
        "added_to_cart": 0.2,
        "removed_from_cart": 0.05,
        "searched": 0.15,
        "logged_in": 0.1,
        "logged_out": 0.05,
        "purchased": 0.05 # Add a 'purchased' activity type
    }
    activity_type = random.choices(list(activity_types_weights.keys()), weights=list(activity_types_weights.values()), k=1)[0]
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=ACTIVITY_HISTORY_DAYS)
    timestamp = fake.date_time_between(start_date=start_date, end_date=end_date)

    activity_data = {
        "activityId": str(uuid.uuid4()),
        "userId": user['userId'],
        "activityType": activity_type,
        "timestamp": timestamp,
        "ipAddress": fake.ipv4(),
        "device": random.choice(["mobile", "desktop", "tablet", "wearable"])
    }

    if products: # Ensure products list is available for product-related activities
        if activity_type in ["viewed_product", "added_to_cart", "removed_from_cart", "purchased"]:
            product = random.choice(products)
            activity_data["productId"] = product['productId']
            if activity_type == "purchased":
                activity_data["purchase_value"] = round(product['price'] * random.randint(1, 3), 2)
        elif activity_type == "searched":
            search_terms = ["laptop", "headphones", "book", "shirt", "gaming", "fitness", "beauty", "car", "coffee", "toy"]
            activity_data["searchTerm"] = random.choice(search_terms) + " " + fake.word() # More complex search terms
    
    return activity_data

# For initial population or single item testing
if __name__ == "__main__":
    Faker.seed(0) # For reproducible results in example

    print("--- Sample Generated Data ---")
    
    print("\nSample User:")
    user_sample = generate_user_data()
    print(user_sample)

    print("\nSample Product:")
    product_sample = generate_product_data()
    print(product_sample)
    
    # For transactions, feedback, activities, we need actual lists
    # In streaming_etl, these will come from the pre-generated pool
    dummy_users_list = [generate_user_data() for _ in range(5)]
    dummy_products_list = [generate_product_data() for _ in range(5)]

    print("\nSample Transaction:")
    transaction_sample = generate_transaction_data(dummy_users_list, dummy_products_list)
    if transaction_sample:
        print(transaction_sample)

    print("\nSample Feedback:")
    feedback_sample = generate_feedback_data(dummy_users_list, dummy_products_list)
    if feedback_sample:
        print(feedback_sample)

    print("\nSample User Activity:")
    activity_sample = generate_user_activity_data(dummy_users_list, dummy_products_list)
    if activity_sample:
        print(activity_sample)
    
    print("\n--- End Sample Data ---")