#!/usr/bin/env python3
"""
Final verification that Phase 4 models can be saved and loaded correctly.
"""

import os
import sys
import pandas as pd
import numpy as np

# Add the ai_service directory to Python path
sys.path.append('/home/deepak/Dev/ABI-v3/ai_service')

def test_phase4_model_saving():
    """Test that all Phase 4 models can be saved and loaded."""
    print("=== Testing Phase 4 Model Saving and Loading ===")
    
    # Ensure models directory exists
    models_dir = 'models/saved_models'
    os.makedirs(models_dir, exist_ok=True)
    
    # Test 1: DynamicPricingModel
    print("\n1. Testing DynamicPricingModel...")
    from app.models.advanced_models import DynamicPricingModel
    
    # Create sample data
    np.random.seed(42)
    pricing_data = pd.DataFrame({
        'product_id': [f'prod_{i}' for i in range(50)],
        'user_id': [f'user_{i%10}' for i in range(50)],
        'amount': np.random.uniform(10, 1000, 50),
        'quantity': np.random.randint(1, 10, 50),
        'category': np.random.choice(['electronics', 'clothing', 'books'], 50),
        'timestamp': pd.date_range('2024-01-01', periods=50, freq='D'),
        'price': np.random.uniform(5, 500, 50)
    })
    pricing_data['optimal_price'] = pricing_data['price'] * 1.05
    
    # Train and save
    pricing_model = DynamicPricingModel()
    train_result = pricing_model.train(pricing_data, target_col='optimal_price')
    print(f"  Training result: {train_result['status']}")
    
    if train_result['status'] == 'success':
        save_path = f'{models_dir}/dynamic_pricing_model_test.pkl'
        pricing_model.save_model(save_path)
        
        # Verify file exists
        if os.path.exists(save_path):
            print(f"  ✓ Model saved successfully: {save_path}")
            
            # Test loading
            new_pricing_model = DynamicPricingModel()
            if new_pricing_model.load_model(save_path):
                print(f"  ✓ Model loaded successfully")
            else:
                print(f"  ✗ Model loading failed")
        else:
            print(f"  ✗ Model file not found: {save_path}")
    else:
        print(f"  ✗ Training failed: {train_result.get('message', 'Unknown error')}")
    
    # Test 2: ChurnPredictionModel
    print("\n2. Testing ChurnPredictionModel...")
    from app.models.advanced_models import ChurnPredictionModel
    
    # Create sample data with mixed recency for churn detection
    recent_data = pd.DataFrame({
        'user_id': [f'user_{i}' for i in range(30)],
        'product_id': [f'prod_{i%10}' for i in range(30)],
        'transaction_id': [f'txn_{i}' for i in range(30)],
        'amount': np.random.uniform(10, 500, 30),
        'quantity': np.random.randint(1, 5, 30),
        'category': np.random.choice(['electronics', 'clothing', 'books'], 30),
        'timestamp': pd.date_range('2024-06-01', periods=30, freq='D')
    })
    
    old_data = pd.DataFrame({
        'user_id': [f'old_user_{i}' for i in range(20)],
        'product_id': [f'prod_{i%10}' for i in range(20)],
        'transaction_id': [f'old_txn_{i}' for i in range(20)],
        'amount': np.random.uniform(10, 500, 20),
        'quantity': np.random.randint(1, 5, 20),
        'category': np.random.choice(['electronics', 'clothing', 'books'], 20),
        'timestamp': pd.date_range('2023-01-01', periods=20, freq='D')
    })
    
    churn_data = pd.concat([recent_data, old_data], ignore_index=True)
    
    # Train and save
    churn_model = ChurnPredictionModel()
    train_result = churn_model.train(churn_data)
    print(f"  Training result: {train_result['status']}")
    
    if train_result['status'] == 'success':
        save_path = f'{models_dir}/churn_model_test.pkl'
        churn_model.save_model(save_path)
        
        # Verify file exists
        if os.path.exists(save_path):
            print(f"  ✓ Model saved successfully: {save_path}")
            
            # Test loading
            new_churn_model = ChurnPredictionModel()
            if new_churn_model.load_model(save_path):
                print(f"  ✓ Model loaded successfully")
            else:
                print(f"  ✗ Model loading failed")
        else:
            print(f"  ✗ Model file not found: {save_path}")
    else:
        print(f"  ✗ Training failed: {train_result.get('message', 'Unknown error')}")
    
    # Test 3: CustomerBehaviorGraph (Knowledge Graph)
    print("\n3. Testing CustomerBehaviorGraph...")
    from app.models.knowledge_graph import CustomerBehaviorGraph
    
    # Create sample data
    users_df = pd.DataFrame({
        'user_id': [f'user_{i}' for i in range(20)],
        'username': [f'user{i}' for i in range(20)]
    })
    
    products_df = pd.DataFrame({
        'product_id': [f'prod_{i}' for i in range(10)],
        'category': np.random.choice(['electronics', 'clothing', 'books'], 10),
        'name': [f'Product {i}' for i in range(10)]
    })
    
    transactions_df = pd.DataFrame({
        'user_id': [f'user_{i%20}' for i in range(100)],
        'product_id': [f'prod_{i%10}' for i in range(100)],
        'amount': np.random.uniform(10, 500, 100),
        'category': np.random.choice(['electronics', 'clothing', 'books'], 100),
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='D')
    })
    
    # Build and save
    kg = CustomerBehaviorGraph()
    build_result = kg.build_graph_from_data(transactions_df, products_df, users_df)
    print(f"  Building result: {build_result['status']}")
    
    if build_result['status'] == 'success':
        save_path = f'{models_dir}/knowledge_graph_test.gml'
        kg.save_graph(save_path)
        
        # Verify file exists
        if os.path.exists(save_path):
            print(f"  ✓ Graph saved successfully: {save_path}")
            
            # Test loading
            new_kg = CustomerBehaviorGraph()
            if new_kg.load_graph(save_path):
                print(f"  ✓ Graph loaded successfully")
            else:
                print(f"  ✗ Graph loading failed")
        else:
            print(f"  ✗ Graph file not found: {save_path}")
    else:
        print(f"  ✗ Building failed: {build_result.get('message', 'Unknown error')}")
    
    print("\n=== Phase 4 Model Saving Test Complete ===")

if __name__ == "__main__":
    test_phase4_model_saving()
