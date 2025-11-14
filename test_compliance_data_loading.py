#!/usr/bin/env python3
"""
Test script to verify compliance dataset can be loaded correctly
"""
from pathlib import Path
import pandas as pd

def test_ai_ml_data_loading():
    """Test AI ML Intelligence page data loading"""
    print("Testing AI ML Intelligence data loading...")
    try:
        # Simulate the path from AI_ML_Intelligence.py
        # __file__ would be streamlit_app/pages/AI_ML_Intelligence.py
        # parent.parent.parent would be project root
        data_dir = Path("compliance_dataset")

        print(f"Data directory: {data_dir.absolute()}")
        print(f"Directory exists: {data_dir.exists()}")

        if not data_dir.exists():
            print("❌ Directory not found!")
            return False

        # Test loading files
        files_to_test = [
            "transactions.csv",
            "alerts_analyst_actions.csv",
            "customer_profiles.csv"
        ]

        for filename in files_to_test:
            filepath = data_dir / filename
            print(f"  Checking {filename}... ", end="")
            if not filepath.exists():
                print(f"❌ NOT FOUND")
                return False
            try:
                df = pd.read_csv(str(filepath))
                print(f"✓ OK ({len(df)} rows)")
            except Exception as e:
                print(f"❌ ERROR: {e}")
                return False

        print("✓ AI ML Intelligence data loading: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ AI ML Intelligence data loading failed: {e}")
        return False

def test_compliance_data_loading():
    """Test Compliance KYC page data loading"""
    print("\nTesting Compliance KYC data loading...")
    try:
        data_dir = Path("compliance_dataset")

        print(f"Data directory: {data_dir.absolute()}")
        print(f"Directory exists: {data_dir.exists()}")

        if not data_dir.exists():
            print("❌ Directory not found!")
            return False

        # Test loading files
        files_to_test = [
            "customer_profiles.csv",
            "transactions.csv",
            "kyc_events.csv",
            "cdd_events.csv",
            "edd_actions.csv",
            "alerts_analyst_actions.csv",
            "rule_executions.csv",
            "audit_trail.csv"
        ]

        for filename in files_to_test:
            filepath = data_dir / filename
            print(f"  Checking {filename}... ", end="")
            if not filepath.exists():
                print(f"❌ NOT FOUND")
                return False
            try:
                df = pd.read_csv(str(filepath))
                print(f"✓ OK ({len(df)} rows)")
            except Exception as e:
                print(f"❌ ERROR: {e}")
                return False

        print("✓ Compliance KYC data loading: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ Compliance KYC data loading failed: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Compliance Dataset Loading Test")
    print("="*60)

    ai_ml_ok = test_ai_ml_data_loading()
    compliance_ok = test_compliance_data_loading()

    print("\n" + "="*60)
    if ai_ml_ok and compliance_ok:
        print("✓ ALL TESTS PASSED")
        print("Both pages should now work correctly for manager login!")
    else:
        print("❌ SOME TESTS FAILED")
        if not ai_ml_ok:
            print("  - AI ML Intelligence page has issues")
        if not compliance_ok:
            print("  - Compliance KYC page has issues")
    print("="*60)
