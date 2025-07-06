#!/usr/bin/env python3
"""
Test script to examine the explainable_ai.pkl model file and understand its functionality.
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any

# Add the app directory to Python path
sys.path.append('/home/deepak/Dev/ABI-v3/ai_service')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def examine_explainable_model():
    """Examine the explainable AI model file and understand its structure."""
    
    model_path = '/home/deepak/Dev/ABI-v3/ai_service/models/saved_models/explainable_ai.pkl'
    
    print("=" * 80)
    print("🔍 EXAMINING EXPLAINABLE AI MODEL")
    print("=" * 80)
    
    # Check if file exists
    if not os.path.exists(model_path):
        print(f"❌ Model file not found at: {model_path}")
        return False
    
    # Get file size and info
    file_size = os.path.getsize(model_path)
    print(f"📁 File path: {model_path}")
    print(f"📊 File size: {file_size:,} bytes ({file_size/1024:.2f} KB)")
    
    try:
        # Load the explainable AI model metadata
        print("\n🔬 Loading explainable AI metadata...")
        explainer_data = joblib.load(model_path)
        
        print(f"✅ Successfully loaded explainable AI metadata")
        print(f"📋 Data type: {type(explainer_data)}")
        
        if isinstance(explainer_data, dict):
            print(f"\n📂 Available keys in explainer data:")
            for key in explainer_data.keys():
                print(f"  • {key}: {type(explainer_data[key])}")
            
            # Examine feature names
            if 'feature_names' in explainer_data:
                feature_names = explainer_data['feature_names']
                print(f"\n🎯 Feature Names Structure:")
                print(f"  Type: {type(feature_names)}")
                if isinstance(feature_names, dict):
                    for model_name, features in feature_names.items():
                        print(f"  Model '{model_name}': {len(features) if features else 0} features")
                        if features:
                            print(f"    Sample features: {features[:5]}...")
            
            # Examine available models
            if 'available_models' in explainer_data:
                available_models = explainer_data['available_models']
                print(f"\n🤖 Available Models: {available_models}")
            
            # Examine SHAP model types
            if 'shap_model_types' in explainer_data:
                shap_types = explainer_data['shap_model_types']
                print(f"\n🧠 SHAP Model Types:")
                for model, explainer_type in shap_types.items():
                    print(f"  • {model}: {explainer_type}")
            
            # Examine LIME model types
            if 'lime_model_types' in explainer_data:
                lime_types = explainer_data['lime_model_types']
                print(f"\n🍋 LIME Model Types:")
                for model, explainer_type in lime_types.items():
                    print(f"  • {model}: {explainer_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading explainable AI model: {e}")
        return False

def test_explainable_ai_functionality():
    """Test the ExplainableAI class functionality."""
    
    print("\n" + "=" * 80)
    print("🧪 TESTING EXPLAINABLE AI FUNCTIONALITY")
    print("=" * 80)
    
    try:
        # Import the ExplainableAI class
        from app.models.explainable_ai import ExplainableAI
        
        # Initialize the explainable AI
        explainer = ExplainableAI()
        print("✅ ExplainableAI class imported and initialized successfully")
        
        # Test loading explainers metadata
        print("\n🔄 Testing explainer metadata loading...")
        load_result = explainer.load_explainers()
        print(f"Load result: {load_result}")
        
        if load_result:
            print("✅ Explainer metadata loaded successfully")
            
            # Print feature names for available models
            if explainer.feature_names:
                print(f"\n📋 Feature names loaded for models:")
                for model_name, features in explainer.feature_names.items():
                    print(f"  • {model_name}: {len(features) if features else 0} features")
                    if features:
                        print(f"    Features: {features[:10]}...")  # Show first 10 features
        else:
            print("⚠️ No explainer metadata found or failed to load")
        
        # Test with sample data
        print("\n🧪 Testing with sample data...")
        
        # Create sample data that matches typical features
        sample_data = create_sample_data()
        print(f"Created sample data with shape: {sample_data.shape}")
        print(f"Sample features: {list(sample_data.columns)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import ExplainableAI: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing ExplainableAI functionality: {e}")
        return False

def create_sample_data():
    """Create sample data for testing explainable AI."""
    
    # Create realistic sample data that might be used in the system
    np.random.seed(42)
    n_samples = 100
    
    # Common features that might be used in business analytics
    data = {
        'user_id': range(1, n_samples + 1),
        'total_amount': np.random.uniform(10, 1000, n_samples),
        'transaction_count': np.random.randint(1, 50, n_samples),
        'unique_users': np.random.randint(1, 100, n_samples),
        'hour': np.random.randint(0, 24, n_samples),
        'day_of_week': np.random.randint(0, 7, n_samples),
        'is_weekend': np.random.choice([0, 1], n_samples),
        'customer_age': np.random.randint(18, 80, n_samples),
        'days_since_last_purchase': np.random.randint(0, 365, n_samples),
        'avg_purchase_amount': np.random.uniform(5, 500, n_samples),
        'purchase_frequency': np.random.uniform(0.1, 10.0, n_samples),
    }
    
    return pd.DataFrame(data)

def test_explanation_methods():
    """Test different explanation methods available."""
    
    print("\n" + "=" * 80)
    print("🔬 TESTING EXPLANATION METHODS")
    print("=" * 80)
    
    try:
        from app.models.explainable_ai import ExplainableAI
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        
        # Create sample data for training
        sample_data = create_sample_data()
        
        # Create a target variable (e.g., high value customer)
        sample_data['high_value'] = (sample_data['total_amount'] > sample_data['total_amount'].median()).astype(int)
        
        # Prepare features and target
        feature_cols = ['total_amount', 'transaction_count', 'hour', 'day_of_week', 
                       'is_weekend', 'customer_age', 'days_since_last_purchase']
        X = sample_data[feature_cols]
        y = sample_data['high_value']
        
        # Train a simple model
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        print(f"✅ Trained sample RandomForest model")
        print(f"📊 Model accuracy: {model.score(X, y):.3f}")
        
        # Initialize explainer
        explainer = ExplainableAI()
        
        # Setup explainer for the model
        setup_result = explainer.setup_explainer(model, X, 'test_model', 'shap')
        print(f"\n🔧 Setup explainer result: {setup_result}")
        
        if setup_result.get('status') == 'success':
            # Test single prediction explanation
            single_instance = X.head(1)
            print(f"\n🔍 Testing single prediction explanation...")
            print(f"Instance shape: {single_instance.shape}")
            
            # Test SHAP explanation
            shap_result = explainer.explain_prediction_shap(model, single_instance, 'test_model')
            print(f"\n🧠 SHAP Explanation Result:")
            print(f"  Status: {shap_result.get('status')}")
            if shap_result.get('status') == 'success':
                print(f"  Prediction: {shap_result.get('prediction')}")
                print(f"  Base value: {shap_result.get('base_value')}")
                print(f"  Feature contributions: {len(shap_result.get('feature_contributions', []))}")
                
                # Show top 3 feature contributions
                contributions = shap_result.get('feature_contributions', [])
                if contributions:
                    print(f"  Top 3 contributions:")
                    for i, contrib in enumerate(contributions[:3]):
                        print(f"    {i+1}. {contrib['feature']}: {contrib['contribution']:.4f}")
            else:
                print(f"  Error: {shap_result.get('message')}")
            
            # Test global explanations
            print(f"\n🌍 Testing global explanations...")
            global_result = explainer.generate_global_explanations(model, X.head(20), 'test_model')
            print(f"Global Explanation Result:")
            print(f"  Status: {global_result.get('status')}")
            if global_result.get('status') == 'success':
                feature_ranking = global_result.get('feature_ranking', [])
                if feature_ranking:
                    print(f"  Top 3 important features:")
                    for i, feat in enumerate(feature_ranking[:3]):
                        print(f"    {i+1}. {feat['feature']}: importance {feat['importance']:.4f}")
            
            # Test feature importance
            print(f"\n📈 Testing feature importance...")
            importance_result = explainer.generate_feature_importance(model, X, 'test_model', 'shap')
            print(f"Feature Importance Result:")
            print(f"  Status: {importance_result.get('status')}")
            if importance_result.get('status') == 'success':
                print(f"  Method: {importance_result.get('method')}")
                importance_data = importance_result.get('feature_importance', [])
                if importance_data:
                    print(f"  Top features by importance:")
                    for feat in importance_data[:5]:
                        print(f"    • {feat['feature']}: {feat['importance']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing explanation methods: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_request_response_format():
    """Analyze the expected request and response formats for the explainable AI."""
    
    print("\n" + "=" * 80)
    print("📋 REQUEST/RESPONSE FORMAT ANALYSIS")
    print("=" * 80)
    
    print("""
🔍 EXPLAINABLE AI REQUEST FORMATS:

1. SETUP EXPLAINER:
   Input: {
     "model": <trained_model_object>,
     "X_train": <pandas_DataFrame>,
     "model_name": "string",
     "explainer_type": "shap" | "lime" | "both"
   }
   
2. SINGLE PREDICTION EXPLANATION:
   Input: {
     "model": <trained_model_object>,
     "X_instance": <single_row_DataFrame>,
     "model_name": "string",
     "method": "shap" | "lime"
   }
   
3. GLOBAL EXPLANATIONS:
   Input: {
     "model": <trained_model_object>,
     "X_data": <pandas_DataFrame>,
     "model_name": "string",
     "sample_size": <integer>
   }
   
4. FEATURE IMPORTANCE:
   Input: {
     "model": <trained_model_object>,
     "X_data": <pandas_DataFrame>,
     "model_name": "string",
     "method": "shap" | "permutation"
   }

📤 EXPLAINABLE AI RESPONSE FORMATS:

1. SHAP EXPLANATION RESPONSE:
   {
     "status": "success" | "error",
     "model_name": "string",
     "prediction": <float>,
     "prediction_proba": [<float>, ...] | null,
     "base_value": <float>,
     "feature_contributions": [
       {
         "feature": "string",
         "value": <float>,
         "contribution": <float>,
         "abs_contribution": <float>
       }
     ],
     "top_positive_features": [...],
     "top_negative_features": [...]
   }

2. GLOBAL EXPLANATION RESPONSE:
   {
     "status": "success" | "error",
     "model_name": "string",
     "feature_ranking": [
       {
         "feature": "string",
         "importance": <float>,
         "mean_impact": <float>,
         "impact_std": <float>
       }
     ],
     "summary_stats": {
       "most_important_feature": "string",
       "least_important_feature": "string",
       "total_features": <int>,
       "top_5_features": [...]
     },
     "sample_size": <int>
   }

3. VISUALIZATION RESPONSE:
   {
     "status": "success" | "error",
     "chart_data": <plotly_chart_json>,
     "chart_type": "feature_importance" | "waterfall" | "feature_comparison",
     "visualization_type": "string"
   }
""")

def main():
    """Main test function."""
    
    print("🚀 Starting Explainable AI Model Analysis")
    print("=" * 80)
    
    # Step 1: Examine the model file
    success1 = examine_explainable_model()
    
    # Step 2: Test the functionality
    success2 = test_explainable_ai_functionality()
    
    # Step 3: Test explanation methods
    success3 = test_explanation_methods()
    
    # Step 4: Show request/response formats
    analyze_request_response_format()
    
    print("\n" + "=" * 80)
    print("📊 ANALYSIS SUMMARY")
    print("=" * 80)
    
    print(f"📁 Model file examination: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"🔧 Functionality test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    print(f"🧪 Explanation methods test: {'✅ PASSED' if success3 else '❌ FAILED'}")
    
    if all([success1, success2, success3]):
        print("\n🎉 All tests passed! The explainable AI model is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
