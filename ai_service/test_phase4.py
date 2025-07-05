#!/usr/bin/env python3
"""
Phase 4 Testing Script
Tests all Phase 4 components and dependencies
"""

import sys
import os
sys.path.append('.')

def test_dependencies():
    """Test all Phase 4 dependencies"""
    print("🔍 Testing Phase 4 dependencies...")
    
    try:
        import shap
        print("✅ SHAP imported successfully")
    except ImportError as e:
        print(f"❌ SHAP import failed: {e}")
        return False
    
    try:
        import lime
        print("✅ LIME imported successfully")
    except ImportError as e:
        print(f"❌ LIME import failed: {e}")
        return False
    
    try:
        import networkx as nx
        print("✅ NetworkX imported successfully")
    except ImportError as e:
        print(f"❌ NetworkX import failed: {e}")
        return False
    
    try:
        import lightgbm as lgb
        print("✅ LightGBM imported successfully")
    except ImportError as e:
        print(f"❌ LightGBM import failed: {e}")
        return False
    
    try:
        import xgboost as xgb
        print("✅ XGBoost imported successfully")
    except ImportError as e:
        print(f"❌ XGBoost import failed: {e}")
        return False
    
    return True

def test_models():
    """Test Phase 4 model imports"""
    print("\n🔍 Testing Phase 4 model imports...")
    
    try:
        from app.models.advanced_models import DynamicPricingModel, ChurnPredictionModel
        print("✅ Advanced models imported successfully")
    except ImportError as e:
        print(f"❌ Advanced models import failed: {e}")
        return False
    
    try:
        from app.models.knowledge_graph import CustomerBehaviorGraph
        print("✅ Knowledge graph imported successfully")
    except ImportError as e:
        print(f"❌ Knowledge graph import failed: {e}")
        return False
    
    try:
        from app.models.explainable_ai import ExplainableAI
        print("✅ Explainable AI imported successfully")
    except ImportError as e:
        print(f"❌ Explainable AI import failed: {e}")
        return False
    
    return True

def test_services():
    """Test Phase 4 service imports"""
    print("\n🔍 Testing Phase 4 service imports...")
    
    try:
        from app.services.pricing_service import PricingService
        print("✅ Pricing service imported successfully")
    except ImportError as e:
        print(f"❌ Pricing service import failed: {e}")
        return False
    
    try:
        from app.services.churn_service import ChurnService
        print("✅ Churn service imported successfully")
    except ImportError as e:
        print(f"❌ Churn service import failed: {e}")
        return False
    
    try:
        from app.services.reasoning_service import ReasoningService
        print("✅ Reasoning service imported successfully")
    except ImportError as e:
        print(f"❌ Reasoning service import failed: {e}")
        return False
    
    try:
        from app.services.feedback_service import FeedbackService
        print("✅ Feedback service imported successfully")
    except ImportError as e:
        print(f"❌ Feedback service import failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Phase 4 Comprehensive Test")
    print("=" * 50)
    
    deps_ok = test_dependencies()
    models_ok = test_models()
    services_ok = test_services()
    
    print("\n" + "=" * 50)
    if deps_ok and models_ok and services_ok:
        print("🎉 ALL TESTS PASSED! Phase 4 is ready!")
        print("✅ You can now restart the AI service to see Phase 4 models load")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    print("=" * 50)
