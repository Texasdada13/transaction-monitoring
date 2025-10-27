#!/usr/bin/env python3
"""
Generate comprehensive sample data for all fraud scenarios.
"""
import sys
from app.models.database import init_db, get_db

def generate_all_scenarios():
    """Generate data from all available fraud scenarios."""
    print("\n" + "="*80)
    print("GENERATING COMPREHENSIVE SAMPLE DATA")
    print("="*80)

    # Initialize fresh database
    print("\n[1] Initializing database...")
    init_db()
    print("    Database initialized successfully")

    # Run payroll reroute scenario
    print("\n[2] Generating Payroll Fraud scenario data...")
    try:
        from app.scenarios.payroll_reroute_scenario import main as payroll_main
        payroll_main()
        print("    ✓ Payroll fraud data generated")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    # Run beneficiary fraud scenario
    print("\n[3] Generating Beneficiary Fraud scenario data...")
    try:
        from app.scenarios.beneficiary_fraud_scenario import main as beneficiary_main
        beneficiary_main()
        print("    ✓ Beneficiary fraud data generated")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    # Run vendor impersonation scenario
    print("\n[4] Generating Vendor Impersonation scenario data...")
    try:
        from app.scenarios.vendor_impersonation_scenario import main as vendor_main
        vendor_main()
        print("    ✓ Vendor impersonation data generated")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    # Print summary
    print("\n" + "="*80)
    print("DATA GENERATION COMPLETE")
    print("="*80)

    # Show data statistics
    db = next(get_db())
    try:
        from app.models.database import (
            Account, Transaction, Employee, Beneficiary,
            RiskAssessment, AccountChangeHistory, BeneficiaryChangeHistory
        )

        print("\nGenerated data summary:")
        print(f"  Accounts: {db.query(Account).count()}")
        print(f"  Transactions: {db.query(Transaction).count()}")
        print(f"  Employees: {db.query(Employee).count()}")
        print(f"  Beneficiaries: {db.query(Beneficiary).count()}")
        print(f"  Risk Assessments: {db.query(RiskAssessment).count()}")
        print(f"  Account Changes: {db.query(AccountChangeHistory).count()}")
        print(f"  Beneficiary Changes: {db.query(BeneficiaryChangeHistory).count()}")

    finally:
        db.close()

    print("\n✓ Database ready for dashboard visualization")
    print("="*80 + "\n")

if __name__ == "__main__":
    generate_all_scenarios()
