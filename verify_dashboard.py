#!/usr/bin/env python3
"""
Verify dashboard setup and dependencies.
"""
import sys

def check_dependencies():
    """Check if all required packages are installed."""
    print("Checking dependencies...")
    required = {
        'streamlit': 'streamlit',
        'plotly': 'plotly',
        'pandas': 'pandas',
        'sqlalchemy': 'sqlalchemy'
    }

    missing = []
    for package, import_name in required.items():
        try:
            __import__(import_name)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - NOT INSTALLED")
            missing.append(package)

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False

    print("\n✓ All dependencies installed")
    return True


def check_database():
    """Check if database exists and has data."""
    print("\nChecking database...")
    import os
    from app.models.database import get_db, Transaction, RiskAssessment

    db_path = "transaction_monitoring.db"
    if not os.path.exists(db_path):
        print(f"  ✗ Database not found: {db_path}")
        print("  Run: python generate_comprehensive_data.py")
        return False

    print(f"  ✓ Database exists: {db_path}")

    # Check data
    db = next(get_db())
    try:
        tx_count = db.query(Transaction).count()
        assess_count = db.query(RiskAssessment).count()

        print(f"  ✓ Transactions: {tx_count}")
        print(f"  ✓ Risk Assessments: {assess_count}")

        if tx_count == 0:
            print("\n  ⚠️  No transaction data found")
            print("  Run: python generate_comprehensive_data.py")
            return False

        return True
    finally:
        db.close()


def check_pages():
    """Check if all dashboard pages exist."""
    print("\nChecking dashboard pages...")
    import os

    pages = [
        'pages/__init__.py',
        'pages/executive_summary.py',
        'pages/fraud_scenarios.py',
        'pages/rule_performance.py',
        'pages/risk_distribution.py',
        'pages/review_queue.py',
        'pages/account_activity.py',
        'pages/transaction_velocity.py',
        'pages/cost_benefit.py'
    ]

    all_exist = True
    for page in pages:
        if os.path.exists(page):
            print(f"  ✓ {page}")
        else:
            print(f"  ✗ {page} - NOT FOUND")
            all_exist = False

    if all_exist:
        print("\n✓ All dashboard pages present")
    return all_exist


def test_imports():
    """Test importing dashboard modules."""
    print("\nTesting dashboard imports...")

    try:
        from pages import (
            executive_summary,
            fraud_scenarios,
            rule_performance,
            risk_distribution,
            review_queue,
            account_activity,
            transaction_velocity,
            cost_benefit
        )
        print("  ✓ All page modules import successfully")
        return True
    except Exception as e:
        print(f"  ✗ Import error: {e}")
        return False


def main():
    """Run all verification checks."""
    print("="*80)
    print("DASHBOARD VERIFICATION")
    print("="*80)

    checks = [
        ("Dependencies", check_dependencies),
        ("Database", check_database),
        ("Page Files", check_pages),
        ("Module Imports", test_imports)
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Error in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8s} - {name}")
        if not passed:
            all_passed = False

    print("="*80)

    if all_passed:
        print("\n✅ All checks passed! Dashboard is ready to run.")
        print("\nTo start the dashboard:")
        print("  streamlit run streamlit_app.py")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
