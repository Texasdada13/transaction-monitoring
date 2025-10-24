# config/settings.py
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./transaction_monitoring.db")

# Risk scoring thresholds
RISK_THRESHOLDS = {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.8
}

# Decision engine settings
AUTO_APPROVE_THRESHOLD = 0.3
MANUAL_REVIEW_THRESHOLD = 0.6
DEFAULT_AUTO_APPROVE_THRESHOLD = 0.3
DEFAULT_MANUAL_REVIEW_THRESHOLD = 0.6
DEFAULT_HIGH_VALUE_THRESHOLD = 10000.00

# Cost-benefit parameters
HOURLY_REVIEW_COST = 75.00  # Cost per hour for manual review
AVG_REVIEW_TIME_MINUTES = 15  # Average time to review a transaction

# Payroll fraud detection settings
PAYROLL_SUSPICIOUS_CHANGE_WINDOW_DAYS = 30  # Days before payroll to flag account changes
PAYROLL_RAPID_CHANGE_THRESHOLD = 2  # Number of changes that trigger suspicion
PAYROLL_RAPID_CHANGE_WINDOW_DAYS = 90  # Window to count rapid changes
PAYROLL_VERIFICATION_REQUIRED_THRESHOLD = 5000.00  # Payroll amount requiring verification

# Beneficiary fraud detection settings
BENEFICIARY_RAPID_ADDITION_THRESHOLD = 5  # Number of beneficiaries added to trigger alert
BENEFICIARY_RAPID_ADDITION_WINDOW_HOURS = 24  # Time window for rapid additions
BENEFICIARY_BULK_ADDITION_THRESHOLD = 10  # Threshold for bulk/scripted additions
BENEFICIARY_BULK_ADDITION_WINDOW_HOURS = 72  # Extended window for bulk detection
BENEFICIARY_RECENT_ADDITION_HOURS = 48  # Hours to consider beneficiary as "newly added"
BENEFICIARY_NEW_BENEFICIARY_PAYMENT_RATIO = 0.7  # Ratio of payments to new beneficiaries (70%+)
