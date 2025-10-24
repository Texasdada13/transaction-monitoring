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
