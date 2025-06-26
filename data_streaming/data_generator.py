# adaptive-bi-system/data_streaming/data_generator.py
import uuid
import random
from datetime import datetime, timedelta
from faker import Faker # type: ignore

fake = Faker()

def generate_user_data(existing_user_ids=None):
    """Generates a synthetic user record."""
    if existing_user_ids is None:
        existing_user_ids = set()

    user_id = str(uuid.uuid4())
    while user_id in existing_user_ids: # Ensure unique ID
        user_id = str(uuid.uuid4())

    registration_date = fake.date_time_between(start_date="-2y", end_date="now")
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

def generate_product_data(existing_product_ids=None):
    """Generates a synthetic product record."""
    if existing_product_ids is None:
        existing_product_ids = set()

    product_id = str(uuid.uuid4())
    while product_id in existing_product_ids: # Ensure unique ID
        product_id = str(uuid.uuid4())

    categories = ["Electronics", "Books", "Home & Kitchen", "Apparel", "Sports", "Beauty", "Automotive"]
    product_base_names = {
        "Electronics": ["Smartphone", "Laptop", "Headphones", "Smartwatch", "Camera"],
        "Books": ["Fiction Novel", "Textbook", "Cookbook", "Mystery Thriller", "Biography"],
        "Home & Kitchen": ["Coffee Maker", "Blender", "Toaster", "Vacuum Cleaner", "Air Fryer"],
        "Apparel": ["T-Shirt", "Jeans", "Jacket", "Sneakers", "Dress"],
        "Sports": ["Dumbbells", "Yoga Mat", "Basketball", "Running Shoes", "Tent"],
        "Beauty": ["Moisturizer", "Perfume", "Lipstick", "Shampoo", "Face Mask"],
        "Automotive": ["Car Charger", "Dash Cam", "Tire Inflator", "Jump Starter", "Seat Cover"]
    }

    category = random.choice(categories)
    name = random.choice(product_base_names.get(category, ["Generic Item"]))

    return {
        "productId": product_id,
        "name": f"{name} {fake.word().capitalize()}", # Add a random word for more variety
        "category": category,
        "price": round(random.uniform(10.0, 1500.0), 2),
        "stock": random.randint(0, 500),
        "description": fake.paragraph(nb_sentences=2),
        "imageUrl": fake.image_url(),
        "addedDate": fake.date_time_between(start_date="-1y", end_date="now"),
        "lastUpdated": datetime.now()
    }

def generate_transaction_data(users, products):
    """Generates a synthetic transaction record."""
    if not users or not products:
        return None # Cannot generate transaction without users or products

    user = random.choice(users)
    product = random.choice(products)
    quantity = random.randint(1, 5)
    total_price = round(product['price'] * quantity, 2)
    transaction_date = fake.date_time_between(start_date="-1m", end_date="now")

    return {
        "transactionId": str(uuid.uuid4()),
        "userId": user['userId'],
        "productId": product['productId'],
        "quantity": quantity,
        "totalPrice": total_price,
        "transactionDate": transaction_date,
        "status": random.choice(["completed", "pending", "failed", "returned"]),
        "paymentMethod": random.choice(["credit_card", "paypal", "bank_transfer", "crypto"]),
        "shippingAddress": user['address'],
        "createdAt": datetime.now()
    }

def generate_feedback_data(users, products):
    """Generates a synthetic feedback record."""
    if not users or not products:
        return None # Cannot generate feedback without users or products

    user = random.choice(users)
    product = random.choice(products)

    comments = [
        "Great product, highly recommend!",
        "Good value for money. Arrived quickly.",
        "Could be better, but acceptable for the price.",
        "Very satisfied with the purchase. Works as expected.",
        "Disappointed with the quality. Broke after a week.",
        "Fast shipping and excellent customer service.",
        "The best product in its category!",
        "Not bad, but saw similar for cheaper.",
        "Exactly what I needed. Five stars!",
        "Poor packaging, but the item itself is fine."
    ]

    return {
        "feedbackId": str(uuid.uuid4()),
        "userId": user['userId'],
        "productId": product['productId'],
        "rating": random.randint(1, 5),
        "comment": random.choice(comments),
        "feedbackDate": fake.date_time_between(start_date="-2w", end_date="now"),
        "createdAt": datetime.now()
    }

def generate_user_activity_data(users):
    """Generates a synthetic user activity record."""
    if not users:
        return None
    user = random.choice(users)
    activity_type = random.choice(["viewed_product", "added_to_cart", "removed_from_cart", "searched", "logged_in", "logged_out"])
    
    activity_data = {
        "activityId": str(uuid.uuid4()),
        "userId": user['userId'],
        "activityType": activity_type,
        "timestamp": datetime.now(),
        "ipAddress": fake.ipv4(),
        "device": random.choice(["mobile", "desktop", "tablet"])
    }

    # Add context specific to activity type
    if activity_type in ["viewed_product", "added_to_cart", "removed_from_cart"]:
        # Assuming product IDs are available in the main script for lookup
        activity_data["productId"] = str(uuid.uuid4()) # Placeholder, actual product ID would come from existing products
    elif activity_type == "searched":
        activity_data["searchTerm"] = fake.word()
    
    return activity_data

if __name__ == "__main__":
    # Example usage:
    print("Generating a sample user:")
    print(generate_user_data())
    print("\nGenerating a sample product:")
    print(generate_product_data())
    
    # Need some dummy users and products for transactions/feedback
    dummy_users = [{'userId': str(uuid.uuid4()), 'address': {'city': 'TestCity'}} for _ in range(5)]
    dummy_products = [{'productId': str(uuid.uuid4()), 'price': random.uniform(10, 100)} for _ in range(5)]

    print("\nGenerating a sample transaction:")
    print(generate_transaction_data(dummy_users, dummy_products))
    print("\nGenerating a sample feedback:")
    print(generate_feedback_data(dummy_users, dummy_products))
    print("\nGenerating a sample user activity:")
    print(generate_user_activity_data(dummy_users))