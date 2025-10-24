# app/services/pattern_detectors.py
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import datetime
from app.models.database import Transaction

class PatternDetector:
    """Base class for pattern detection algorithms."""

    def __init__(self, db: Session):
        """
        Initialize pattern detector with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def detect(self, transaction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect if pattern exists for given transaction.

        Args:
            transaction: Current transaction data
            context: Additional contextual data

        Returns:
            Dictionary with detection results including:
            - detected: boolean indicating if pattern was found
            - confidence: float 0-1 indicating confidence level
            - details: additional information about the detection
        """
        raise NotImplementedError("Subclasses must implement detect method")


class SmallTestLargeWithdrawalDetector(PatternDetector):
    """
    Detects pattern where multiple small transactions are followed by a large withdrawal.

    This is a common fraud pattern where attackers:
    1. Test an account with small amounts to verify it works
    2. Once confirmed, quickly move larger sums before detection
    """

    def __init__(self,
                 db: Session,
                 small_amount_threshold: float = 50.0,
                 large_amount_threshold: float = 1000.0,
                 min_small_transactions: int = 3,
                 lookback_hours: int = 24,
                 withdrawal_types: List[str] = None):
        """
        Initialize detector with configurable thresholds.

        Args:
            db: Database session
            small_amount_threshold: Maximum amount to consider "small" (default: $50)
            large_amount_threshold: Minimum amount to consider "large" (default: $1000)
            min_small_transactions: Minimum number of small transactions required (default: 3)
            lookback_hours: Time window to look for small transactions (default: 24 hours)
            withdrawal_types: Transaction types considered withdrawals (default: ["WITHDRAWAL", "WIRE", "ACH_OUT"])
        """
        super().__init__(db)
        self.small_amount_threshold = small_amount_threshold
        self.large_amount_threshold = large_amount_threshold
        self.min_small_transactions = min_small_transactions
        self.lookback_hours = lookback_hours
        self.withdrawal_types = withdrawal_types or ["WITHDRAWAL", "WIRE", "ACH_OUT", "TRANSFER_OUT"]

    def detect(self, transaction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect if current transaction matches the small-test-large-withdrawal pattern.

        Args:
            transaction: Current transaction data
            context: Additional contextual data

        Returns:
            Detection results with pattern details
        """
        result = {
            "detected": False,
            "confidence": 0.0,
            "details": {}
        }

        # Check if current transaction is a large withdrawal
        current_amount = transaction.get("amount", 0)
        current_type = transaction.get("transaction_type", "")

        if current_amount < self.large_amount_threshold:
            result["details"]["reason"] = "Current transaction amount too small"
            return result

        if current_type not in self.withdrawal_types:
            result["details"]["reason"] = "Current transaction is not a withdrawal"
            return result

        # Look for recent small transactions
        account_id = transaction.get("account_id")
        if not account_id:
            result["details"]["reason"] = "No account ID provided"
            return result

        small_transactions = self._get_recent_small_transactions(account_id)

        if len(small_transactions) < self.min_small_transactions:
            result["details"]["reason"] = f"Only {len(small_transactions)} small transactions found, need {self.min_small_transactions}"
            result["details"]["small_transaction_count"] = len(small_transactions)
            return result

        # Pattern detected!
        result["detected"] = True

        # Calculate confidence based on:
        # 1. Number of small transactions (more = higher confidence)
        # 2. Ratio of large to small amounts (larger ratio = higher confidence)
        # 3. Time clustering of small transactions (more clustered = higher confidence)

        small_tx_count = len(small_transactions)
        small_amounts = [tx.amount for tx in small_transactions]
        avg_small_amount = sum(small_amounts) / len(small_amounts) if small_amounts else 0

        # Component 1: Small transaction count (normalized, max at 10 transactions)
        count_score = min(small_tx_count / 10.0, 1.0)

        # Component 2: Amount ratio
        amount_ratio = current_amount / max(avg_small_amount, 1.0)
        ratio_score = min(amount_ratio / 100.0, 1.0)  # Normalize to 0-1, max at 100x

        # Component 3: Time clustering (all within lookback period, more recent = higher score)
        time_scores = []
        now = datetime.datetime.utcnow()
        for tx in small_transactions:
            tx_time = datetime.datetime.fromisoformat(tx.timestamp)
            hours_ago = (now - tx_time).total_seconds() / 3600
            # More recent = higher score (1.0 for very recent, 0.5 for at lookback boundary)
            time_score = 1.0 - (hours_ago / (self.lookback_hours * 2))
            time_scores.append(max(time_score, 0.5))

        avg_time_score = sum(time_scores) / len(time_scores) if time_scores else 0.5

        # Weighted combination
        result["confidence"] = (
            count_score * 0.4 +
            ratio_score * 0.4 +
            avg_time_score * 0.2
        )

        # Add detailed information
        result["details"] = {
            "small_transaction_count": small_tx_count,
            "small_transaction_amounts": small_amounts,
            "avg_small_amount": round(avg_small_amount, 2),
            "large_withdrawal_amount": current_amount,
            "amount_ratio": round(amount_ratio, 2),
            "lookback_hours": self.lookback_hours,
            "small_threshold": self.small_amount_threshold,
            "large_threshold": self.large_amount_threshold,
            "confidence_breakdown": {
                "count_score": round(count_score, 3),
                "ratio_score": round(ratio_score, 3),
                "time_clustering_score": round(avg_time_score, 3)
            }
        }

        return result

    def _get_recent_small_transactions(self, account_id: str) -> List[Transaction]:
        """
        Get recent small transactions for an account.

        Args:
            account_id: Account identifier

        Returns:
            List of Transaction objects that match small transaction criteria
        """
        lookback_time = (
            datetime.datetime.utcnow() -
            datetime.timedelta(hours=self.lookback_hours)
        ).isoformat()

        transactions = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.timestamp > lookback_time,
            Transaction.amount <= self.small_amount_threshold,
            Transaction.amount > 0  # Exclude zero or negative amounts
        ).all()

        return transactions

    def get_pattern_context(self, account_id: str) -> Dict[str, Any]:
        """
        Get pattern-specific context for an account.

        This can be used to enrich the context dictionary with pattern-specific data.

        Args:
            account_id: Account identifier

        Returns:
            Dictionary with pattern context data
        """
        small_transactions = self._get_recent_small_transactions(account_id)

        return {
            "small_test_pattern": {
                "recent_small_tx_count": len(small_transactions),
                "recent_small_tx_sum": sum(tx.amount for tx in small_transactions),
                "lookback_hours": self.lookback_hours,
                "small_threshold": self.small_amount_threshold
            }
        }


def create_small_test_pattern_detector(db: Session, **kwargs) -> SmallTestLargeWithdrawalDetector:
    """
    Factory function to create a SmallTestLargeWithdrawalDetector with custom parameters.

    Args:
        db: Database session
        **kwargs: Optional parameters to override defaults
            - small_amount_threshold: Maximum amount for "small" transactions
            - large_amount_threshold: Minimum amount for "large" withdrawal
            - min_small_transactions: Minimum count of small transactions needed
            - lookback_hours: Time window in hours
            - withdrawal_types: List of transaction types considered withdrawals

    Returns:
        Configured SmallTestLargeWithdrawalDetector instance
    """
    return SmallTestLargeWithdrawalDetector(db, **kwargs)
