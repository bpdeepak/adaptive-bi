#!/usr/bin/env python3
"""
Test script to verify Phase 4 models with correct schema.
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.append('/home/deepak/Dev/ABI-v3/ai_service')

from app.models.advanced_models import DynamicPricingModel, ChurnPredictionModel

def test_dynamic_pricing_model():
    """Test DynamicPricingModel with correct schema."""
    print("=== Testing DynamicPricingModel ===")
    
    # Create sample data with schema matching data_streaming output
    np.random.seed(42)
    sample_data = pd.DataFrame({
        'product_id': [f'prod_{i}' for i in range(100)],
        'user_id': [f'user_{i%20}' for i in range(100)],
        'amount': np.random.uniform(10, 1000, 100),
        'quantity': np.random.randint(1, 10, 100), 
        'category': np.random.choice(['electronics', 'clothing', 'books'], 100),
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='D'),
        'price': np.random.uniform(5, 500, 100)
    })
    sample_data['optimal_price'] = sample_data['price'] * 1.05
    
    print("Data columns:", list(sample_data.columns))
    print("Sample data shape:", sample_data.shape)
    print("First few rows:")
    print(sample_data.head())
    
    # Test training
    print("\nTraining pricing model...")
    pricing_model = DynamicPricingModel()
    result = pricing_model.train(sample_data, target_col='optimal_price')
    print(f"Training result: {result}")
    
    if result['status'] == 'success':
        # Test saving
        os.makedirs('models/saved_models', exist_ok=True)
        save_path = 'models/saved_models/dynamic_pricing_model.pkl'
        pricing_model.save_model(save_path)
        print(f"Model saved to: {save_path}")
        
        # Test prediction
        test_data = sample_data.head(5)
        pred_result = pricing_model.predict_optimal_price(test_data)
        print(f"Prediction result: {pred_result}")
        
        return True
    else:
        print("Training failed!")
        return False

def test_churn_prediction_model():
    """Test ChurnPredictionModel with correct schema."""
    print("\n=== Testing ChurnPredictionModel ===")
    
    # Create sample data for churn prediction with some churned users
    np.random.seed(42)
    sample_data = pd.DataFrame({
        'user_id': [f'user_{i}' for i in range(50)],
        'product_id': [f'prod_{i%10}' for i in range(50)],
        'transaction_id': [f'txn_{i}' for i in range(50)],
        'amount': np.random.uniform(10, 500, 50),
        'quantity': np.random.randint(1, 5, 50),
        'category': np.random.choice(['electronics', 'clothing', 'books'], 50),
        'timestamp': pd.date_range('2024-01-01', periods=50, freq='D')
    })
    
    # Add some older transactions for churned users simulation
    old_data = pd.DataFrame({
        'user_id': [f'old_user_{i}' for i in range(20)],
        'product_id': [f'prod_{i%10}' for i in range(20)],
        'transaction_id': [f'old_txn_{i}' for i in range(20)],
        'amount': np.random.uniform(10, 500, 20),
        'quantity': np.random.randint(1, 5, 20),
        'category': np.random.choice(['electronics', 'clothing', 'books'], 20),
        'timestamp': pd.date_range('2023-06-01', periods=20, freq='D')  # Old transactions
    })
    
    # Combine data
    sample_data = pd.concat([sample_data, old_data], ignore_index=True)
    
    print("Data columns:", list(sample_data.columns))
    print("Sample data shape:", sample_data.shape)
    
    # Test training
    print("\nTraining churn model...")
    churn_model = ChurnPredictionModel()
    result = churn_model.train(sample_data)
    print(f"Training result: {result}")
    
    if result['status'] == 'success':
        # Test saving
        save_path = 'models/saved_models/churn_model.pkl'
        churn_model.save_model(save_path)
        print(f"Model saved to: {save_path}")
        return True
    else:
        print("Training failed!")
        return False

if __name__ == "__main__":
    print("Testing Phase 4 models with correct schema...")
    
    pricing_success = test_dynamic_pricing_model()
    churn_success = test_churn_prediction_model()
    
    print(f"\n=== Summary ===")
    print(f"DynamicPricingModel: {'SUCCESS' if pricing_success else 'FAILED'}")
    print(f"ChurnPredictionModel: {'SUCCESS' if churn_success else 'FAILED'}")
    
    if pricing_success and churn_success:
        print("All Phase 4 models tested successfully!")
    else:
        print("Some models failed. Check the logs above.")
