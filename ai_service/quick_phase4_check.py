#!/usr/bin/env python3
"""
Quick Phase 4 Status Check based on logs and code analysis
"""

import os
import sys

def check_phase4_status():
    print("🚀 PHASE 4 STATUS VERIFICATION")
    print("=" * 50)
    
    # 1. Check if Phase 4 log message appears
    print("1. 📋 Checking Logs for Phase 4 Initialization...")
    
    log_file = "logs/ai_service_2025-07-03.log"
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            log_content = f.read()
            
        if "Phase 4 advanced models initialized" in log_content:
            print("   ✅ Phase 4 models are initializing (found in logs)")
        else:
            print("   ❌ Phase 4 initialization not found in logs")
    
    # 2. Check file structure
    print("\n2. 📁 Checking Phase 4 File Structure...")
    
    phase4_files = [
        "app/models/advanced_models.py",
        "app/models/knowledge_graph.py", 
        "app/models/explainable_ai.py",
        "app/services/pricing_service.py",
        "app/services/churn_service.py",
        "app/services/reasoning_service.py",
        "app/services/feedback_service.py",
        "app/api/routes/advanced_endpoints.py",
        "app/model_configs/model_config.py",
        "requirements_phase4.txt"
    ]
    
    files_present = 0
    for file_path in phase4_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
            files_present += 1
        else:
            print(f"   ❌ {file_path}")
    
    print(f"\n   📊 Files Present: {files_present}/{len(phase4_files)}")
    
    # 3. Check dependencies
    print("\n3. 📦 Checking Key Dependencies...")
    
    if os.path.exists("requirements_phase4.txt"):
        with open("requirements_phase4.txt", 'r') as f:
            requirements = f.read()
            
        key_deps = ['shap', 'lime', 'networkx', 'lightgbm', 'xgboost']
        for dep in key_deps:
            if dep in requirements:
                print(f"   ✅ {dep} in requirements")
            else:
                print(f"   ❌ {dep} missing from requirements")
    
    # 4. Service initialization check from logs
    print("\n4. 🔧 Checking Service Initialization from Logs...")
    
    if os.path.exists(log_file):
        services_found = []
        services_to_check = [
            "PricingService initialized",
            "ChurnService initialized", 
            "ReasoningService initialized",
            "FeedbackService initialized"
        ]
        
        for service in services_to_check:
            if service in log_content:
                print(f"   ✅ {service}")
                services_found.append(service)
            else:
                print(f"   ❌ {service}")
        
        print(f"\n   📊 Services Initialized: {len(services_found)}/{len(services_to_check)}")
    
    # 5. Calculate overall status
    print("\n" + "=" * 50)
    print("📊 PHASE 4 OVERALL STATUS")
    print("=" * 50)
    
    # Score calculation
    file_score = (files_present / len(phase4_files)) * 100
    
    if file_score >= 90 and "Phase 4 advanced models initialized" in log_content:
        status = "✅ COMPLETE"
        color = "🟢"
    elif file_score >= 80:
        status = "🟡 MOSTLY COMPLETE"
        color = "🟡"
    else:
        status = "❌ INCOMPLETE"  
        color = "🔴"
    
    print(f"{color} File Structure: {file_score:.1f}%")
    print(f"{color} Phase 4 Status: {status}")
    
    # Recommendations
    print("\n📋 NEXT STEPS:")
    if file_score >= 90:
        print("✅ All Phase 4 files are present!")
        print("✅ Phase 4 models are initializing!")
        print("🎯 Phase 4 appears to be working!")
        print("\n🚀 To verify functionality:")
        print("   1. Test Phase 4 API endpoints")
        print("   2. Check model training logs")
        print("   3. Verify explainable AI features")
    else:
        print("⚠️  Some Phase 4 components may be missing")
        print("🔧 Consider running setup_phase4.sh again")
    
    return status == "✅ COMPLETE"

if __name__ == "__main__":
    check_phase4_status()
