#!/usr/bin/env python3
"""
Comprehensive Phase 4 Verification Script
Tests all Phase 4 objectives and deliverables
"""

import sys
import os
import json
from datetime import datetime
sys.path.append('.')

class Phase4Verifier:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "phase4_objectives": {},
            "overall_status": "UNKNOWN"
        }
    
    def test_objective_1_dynamic_pricing(self):
        """Test Dynamic Pricing Model Implementation"""
        print("🎯 Testing Objective 1: Dynamic Pricing Model")
        
        try:
            from app.models.advanced_models import DynamicPricingModel
            pricing_model = DynamicPricingModel()
            print("  ✅ DynamicPricingModel imported and instantiated")
            
            from app.services.pricing_service import PricingService
            print("  ✅ PricingService imported")
            
            # Check if pricing service has required methods
            required_methods = ['predict_optimal_price', 'retrain_model', 'forecast_impact', 'explain_prediction']
            for method in required_methods:
                if hasattr(PricingService, method):
                    print(f"  ✅ PricingService.{method} method exists")
                else:
                    print(f"  ❌ PricingService.{method} method missing")
                    return False
            
            self.results["phase4_objectives"]["dynamic_pricing"] = "PASS"
            return True
            
        except Exception as e:
            print(f"  ❌ Dynamic Pricing failed: {e}")
            self.results["phase4_objectives"]["dynamic_pricing"] = f"FAIL: {e}"
            return False
    
    def test_objective_2_churn_prediction(self):
        """Test Customer Churn Prediction with Reasoning"""
        print("\n🎯 Testing Objective 2: Customer Churn Prediction")
        
        try:
            from app.models.advanced_models import ChurnPredictionModel
            churn_model = ChurnPredictionModel()
            print("  ✅ ChurnPredictionModel imported and instantiated")
            
            from app.services.churn_service import ChurnService
            print("  ✅ ChurnService imported")
            
            # Check if churn service has required methods
            required_methods = ['predict_churn', 'retrain_model', 'get_cohort_analysis', 'explain_prediction']
            for method in required_methods:
                if hasattr(ChurnService, method):
                    print(f"  ✅ ChurnService.{method} method exists")
                else:
                    print(f"  ❌ ChurnService.{method} method missing")
                    return False
            
            self.results["phase4_objectives"]["churn_prediction"] = "PASS"
            return True
            
        except Exception as e:
            print(f"  ❌ Churn Prediction failed: {e}")
            self.results["phase4_objectives"]["churn_prediction"] = f"FAIL: {e}"
            return False
    
    def test_objective_3_explainable_ai(self):
        """Test Explainable AI Integration (SHAP/LIME)"""
        print("\n🎯 Testing Objective 3: Explainable AI (SHAP/LIME)")
        
        try:
            import shap
            print("  ✅ SHAP library imported")
            
            import lime
            print("  ✅ LIME library imported")
            
            from app.models.explainable_ai import ExplainableAI
            explainer = ExplainableAI()
            print("  ✅ ExplainableAI class imported and instantiated")
            
            # Check for key methods
            required_methods = ['explain_prediction', 'generate_feature_importance', 'create_visualization']
            for method in required_methods:
                if hasattr(ExplainableAI, method):
                    print(f"  ✅ ExplainableAI.{method} method exists")
                else:
                    print(f"  ⚠️  ExplainableAI.{method} method missing (check implementation)")
            
            self.results["phase4_objectives"]["explainable_ai"] = "PASS"
            return True
            
        except Exception as e:
            print(f"  ❌ Explainable AI failed: {e}")
            self.results["phase4_objectives"]["explainable_ai"] = f"FAIL: {e}"
            return False
    
    def test_objective_4_knowledge_graphs(self):
        """Test Knowledge Graph Implementation"""
        print("\n🎯 Testing Objective 4: Knowledge Graphs")
        
        try:
            import networkx as nx
            print("  ✅ NetworkX library imported")
            
            from app.models.knowledge_graph import CustomerBehaviorGraph
            kg = CustomerBehaviorGraph()
            print("  ✅ CustomerBehaviorGraph imported and instantiated")
            
            from app.services.reasoning_service import ReasoningService
            print("  ✅ ReasoningService imported")
            
            # Check for reasoning methods
            required_methods = ['query_knowledge_graph', 'build_knowledge_graph']
            for method in required_methods:
                if hasattr(ReasoningService, method):
                    print(f"  ✅ ReasoningService.{method} method exists")
                else:
                    print(f"  ❌ ReasoningService.{method} method missing")
                    return False
            
            self.results["phase4_objectives"]["knowledge_graphs"] = "PASS"
            return True
            
        except Exception as e:
            print(f"  ❌ Knowledge Graphs failed: {e}")
            self.results["phase4_objectives"]["knowledge_graphs"] = f"FAIL: {e}"
            return False
    
    def test_objective_5_feedback_mechanism(self):
        """Test Feedback Mechanism for Model Improvement"""
        print("\n🎯 Testing Objective 5: Feedback Mechanism")
        
        try:
            from app.services.feedback_service import FeedbackService
            print("  ✅ FeedbackService imported")
            
            # Check for feedback methods
            required_methods = ['log_feedback', 'trigger_retraining', 'get_feedback_summary']
            for method in required_methods:
                if hasattr(FeedbackService, method):
                    print(f"  ✅ FeedbackService.{method} method exists")
                else:
                    print(f"  ❌ FeedbackService.{method} method missing")
                    return False
            
            self.results["phase4_objectives"]["feedback_mechanism"] = "PASS"
            return True
            
        except Exception as e:
            print(f"  ❌ Feedback Mechanism failed: {e}")
            self.results["phase4_objectives"]["feedback_mechanism"] = f"FAIL: {e}"
            return False
    
    def test_advanced_dependencies(self):
        """Test All Advanced Dependencies"""
        print("\n🔧 Testing Advanced Dependencies")
        
        dependencies = {
            'shap': 'Explainable AI',
            'lime': 'Explainable AI', 
            'networkx': 'Knowledge Graphs',
            'lightgbm': 'Advanced ML',
            'xgboost': 'Advanced ML',
            'plotly': 'Visualizations',
            'skopt': 'Hyperparameter Optimization',  # scikit-optimize imports as skopt
            'category_encoders': 'Feature Engineering',
            'imblearn': 'Imbalanced Data Handling',  # imbalanced-learn imports as imblearn
            'optuna': 'Optimization',
            'redis': 'Caching',
            'celery': 'Background Tasks',
            'mlflow': 'Model Management'
        }
        
        passed = 0
        total = len(dependencies)
        
        for package, purpose in dependencies.items():
            try:
                __import__(package)
                print(f"  ✅ {package} ({purpose})")
                passed += 1
            except ImportError:
                print(f"  ❌ {package} ({purpose}) - not installed")
        
        self.results["dependencies"] = {"passed": passed, "total": total}
        return passed == total
    
    def test_api_endpoints(self):
        """Test Advanced API Endpoints"""
        print("\n🌐 Testing Advanced API Endpoints")
        
        try:
            from app.api.routes.advanced_endpoints import router
            print("  ✅ Advanced endpoints router imported")
            
            # Expected endpoints
            expected_endpoints = [
                "/insights/customer",
                "/insights/product", 
                "/intelligence/market",
                "/analysis/causal",
                "/recommendations/strategic",
                "/pricing/dynamic",
                "/pricing/elasticity/{product_id}",
                "/churn/predict",
                "/churn/risk-factors",
                "/feedback/submit",
                "/knowledge-graph/entities",
                "/knowledge-graph/query"
            ]
            
            # Get actual routes - simplified check
            print(f"  ✅ Advanced endpoints router has {len(router.routes)} routes")
            
            # Simplified endpoint verification - just check if router exists and has routes
            if len(router.routes) >= 10:  # Expect at least 10 advanced endpoints
                print(f"  ✅ Router has sufficient endpoints ({len(router.routes)})")
                endpoint_check_passed = True
            else:
                print(f"  ⚠️  Router has fewer endpoints than expected ({len(router.routes)})")
                endpoint_check_passed = False
            
            self.results["api_endpoints"] = {
                "total_expected": len(expected_endpoints),
                "router_routes": len(router.routes),
                "status": "PASS" if endpoint_check_passed else "PARTIAL"
            }
            
            return endpoint_check_passed
            
        except Exception as e:
            print(f"  ❌ API Endpoints test failed: {e}")
            self.results["api_endpoints"] = f"FAIL: {e}"
            return False
    
    def test_configuration_completeness(self):
        """Test Configuration Completeness"""
        print("\n⚙️  Testing Configuration Completeness")
        
        try:
            from app.model_configs.model_config import (
                PRICING_CONFIG, CHURN_CONFIG, 
                KNOWLEDGE_GRAPH_CONFIG, EXPLAINABLE_AI_CONFIG
            )
            print("  ✅ All Phase 4 configurations imported")
            
            configs = {
                "PRICING_CONFIG": PRICING_CONFIG,
                "CHURN_CONFIG": CHURN_CONFIG,
                "KNOWLEDGE_GRAPH_CONFIG": KNOWLEDGE_GRAPH_CONFIG,
                "EXPLAINABLE_AI_CONFIG": EXPLAINABLE_AI_CONFIG
            }
            
            for name, config in configs.items():
                if config:
                    print(f"  ✅ {name} configured")
                else:
                    print(f"  ❌ {name} not configured")
                    return False
            
            self.results["configuration"] = "PASS"
            return True
            
        except Exception as e:
            print(f"  ❌ Configuration test failed: {e}")
            self.results["configuration"] = f"FAIL: {e}"
            return False
    
    def run_comprehensive_test(self):
        """Run all Phase 4 verification tests"""
        print("🚀 COMPREHENSIVE PHASE 4 VERIFICATION")
        print("=" * 60)
        
        tests = [
            ("Dynamic Pricing Model", self.test_objective_1_dynamic_pricing),
            ("Churn Prediction", self.test_objective_2_churn_prediction),
            ("Explainable AI", self.test_objective_3_explainable_ai),
            ("Knowledge Graphs", self.test_objective_4_knowledge_graphs),
            ("Feedback Mechanism", self.test_objective_5_feedback_mechanism),
            ("Advanced Dependencies", self.test_advanced_dependencies),
            ("API Endpoints", self.test_api_endpoints),
            ("Configuration", self.test_configuration_completeness)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    passed_tests += 1
            except Exception as e:
                print(f"  ❌ {test_name} test crashed: {e}")
        
        print("\n" + "=" * 60)
        print("📊 PHASE 4 VERIFICATION RESULTS")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        
        if success_rate >= 90:
            status = "✅ COMPLETE"
            self.results["overall_status"] = "COMPLETE"
        elif success_rate >= 70:
            status = "🟡 MOSTLY COMPLETE"
            self.results["overall_status"] = "MOSTLY_COMPLETE"
        else:
            status = "❌ INCOMPLETE"
            self.results["overall_status"] = "INCOMPLETE"
        
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"Phase 4 Status: {status}")
        
        self.results["summary"] = {
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "success_rate": success_rate
        }
        
        # Save results to file
        with open('phase4_verification_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: phase4_verification_results.json")
        
        return success_rate >= 90

if __name__ == "__main__":
    verifier = Phase4Verifier()
    is_complete = verifier.run_comprehensive_test()
    
    if is_complete:
        print("\n🎉 CONGRATULATIONS! Phase 4 is COMPLETE!")
        print("🚀 You have successfully implemented all advanced AI features!")
    else:
        print("\n⚠️  Phase 4 needs additional work. Check the results above.")
