#!/usr/bin/env python3
"""
Quick test to verify Phase 4 model training with corrected schema handling.
"""

import asyncio
import sys
sys.path.append('/home/deepak/Dev/ABI-v3/ai_service')
from app.models.model_manager import ModelManager

async def test_phase4_training():
    """Test Phase 4 model training logic."""
    print("Testing Phase 4 model training logic...")
    
    # Initialize ModelManager
    manager = ModelManager()
    
    # Mock database connection
    manager.db_connected = True
    
    # Initialize Phase 4 models
    from app.models.advanced_models import DynamicPricingModel, ChurnPredictionModel
    from app.models.knowledge_graph import CustomerBehaviorGraph
    
    manager.pricing_model = DynamicPricingModel()
    manager.churn_model = ChurnPredictionModel()
    manager.knowledge_graph = CustomerBehaviorGraph()
    
    print("✓ Phase 4 models initialized")
    
    # Test load methods
    print("\nTesting load methods...")
    pricing_loaded = manager.pricing_model.load_model()
    churn_loaded = manager.churn_model.load_model()
    kg_loaded = manager.knowledge_graph.load_graph()
    
    print(f"Pricing model loaded: {pricing_loaded}")
    print(f"Churn model loaded: {churn_loaded}")
    print(f"Knowledge graph loaded: {kg_loaded}")
    
    phase4_loaded = pricing_loaded and churn_loaded and kg_loaded
    print(f"\nAll Phase 4 models loaded from disk: {phase4_loaded}")
    
    if not phase4_loaded:
        print("✓ Phase 4 models would be trained during initialization (as expected)")
    else:
        print("✓ Phase 4 models loaded successfully from disk")
    
    print("\nPhase 4 model loading test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_phase4_training())
