# app/services/context_provider.py
from typing import Dict, Any
from sqlalchemy.orm import Session
import json
import datetime
from app.models.database import Transaction, Account

class ContextProvider:
    def __init__(self, db: Session):
        """
        Initialize context provider with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_transaction_context(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gather contextual information about the account and transaction history.
        
        Args:
            transaction: Transaction data
            
        Returns:
            Context dictionary with historical data
        """
        context = {}
        account_id = transaction.get("account_id")
        
        if not account_id:
            return context
        
        # Get account information
        account = self.db.query(Account).filter(Account.account_id == account_id).first()
        if account:
            # Calculate account age
            creation_date = datetime.datetime.fromisoformat(account.creation_date)
            account_age = (datetime.datetime.utcnow() - creation_date).days
            context["account_age_days"] = account_age
            context["risk_tier"] = account.risk_tier
            
        # Get transaction history
        self._add_transaction_history(context, account_id, transaction)
        
        # Check if counterparty is new
        context["is_new_counterparty"] = self._is_new_counterparty(
            account_id,
            transaction.get("counterparty_id")
        )

        # Add money mule detection context
        self._add_money_mule_context(context, account_id, transaction)

        return context
    
    def _add_transaction_history(self, context: Dict[str, Any], 
                                account_id: str, 
                                current_tx: Dict[str, Any]) -> None:
        """Add transaction history data to context."""
        # Transaction velocity for different time windows
        timeframes = [1, 6, 24, 168]  # hours (1h, 6h, 24h, 1 week)
        context["tx_count_last_hours"] = {}
        
        now = datetime.datetime.utcnow()
        for hours in timeframes:
            time_threshold = (now - datetime.timedelta(hours=hours)).isoformat()
            
            count = self.db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.timestamp > time_threshold
            ).count()
            
            context["tx_count_last_hours"][hours] = count
        
        # Calculate average transaction amount for this type
        tx_type = current_tx.get("transaction_type")
        if tx_type:
            # Get transactions of same type in last 90 days
            ninety_days_ago = (now - datetime.timedelta(days=90)).isoformat()
            
            similar_txs = self.db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.transaction_type == tx_type,
                Transaction.timestamp > ninety_days_ago
            ).all()
            
            if similar_txs:
                amounts = [tx.amount for tx in similar_txs]
                avg_amount = sum(amounts) / len(amounts)
                context["avg_transaction_amount"] = avg_amount
                
                # Calculate standard deviation
                import math
                variance = sum((x - avg_amount) ** 2 for x in amounts) / len(amounts)
                std_dev = math.sqrt(variance)
                
                # Calculate deviation of current transaction
                current_amount = current_tx.get("amount", 0)
                if std_dev > 0:
                    context["amount_deviation"] = abs(current_amount - avg_amount) / std_dev
                else:
                    # If all historical amounts are identical, use ratio
                    context["amount_deviation"] = abs(current_amount / max(avg_amount, 0.01))
            else:
                # First transaction of this type
                context["avg_transaction_amount"] = 0
                context["amount_deviation"] = 5.0  # High deviation for first transaction
    
    def _is_new_counterparty(self, account_id: str, counterparty_id: str) -> bool:
        """Check if this is a new counterparty for this account."""
        if not counterparty_id:
            return False

        # Look for previous transactions with this counterparty
        previous_tx = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.counterparty_id == counterparty_id
        ).first()

        return previous_tx is None

    def _add_money_mule_context(self, context: Dict[str, Any],
                                account_id: str,
                                current_tx: Dict[str, Any]) -> None:
        """
        Add money mule detection context.

        Money mule pattern: Multiple small incoming payments quickly followed by outgoing transfers.
        """
        now = datetime.datetime.utcnow()

        # Analyze patterns over different time windows
        time_windows = [24, 72, 168]  # 1 day, 3 days, 1 week (hours)

        for hours in time_windows:
            time_threshold = (now - datetime.timedelta(hours=hours)).isoformat()

            # Get incoming transactions (credits)
            incoming_txs = self.db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.direction == "credit",
                Transaction.timestamp > time_threshold
            ).all()

            # Get outgoing transactions (debits)
            outgoing_txs = self.db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.direction == "debit",
                Transaction.timestamp > time_threshold
            ).all()

            # Calculate metrics
            incoming_count = len(incoming_txs)
            outgoing_count = len(outgoing_txs)
            incoming_total = sum(tx.amount for tx in incoming_txs)
            outgoing_total = sum(tx.amount for tx in outgoing_txs)

            # Store in context
            context[f"incoming_count_{hours}h"] = incoming_count
            context[f"outgoing_count_{hours}h"] = outgoing_count
            context[f"incoming_total_{hours}h"] = incoming_total
            context[f"outgoing_total_{hours}h"] = outgoing_total

            # Calculate average incoming transaction amount (for "many small" detection)
            if incoming_count > 0:
                avg_incoming = incoming_total / incoming_count
                context[f"avg_incoming_amount_{hours}h"] = avg_incoming
            else:
                context[f"avg_incoming_amount_{hours}h"] = 0

            # Calculate flow-through ratio (how much incoming is sent out)
            if incoming_total > 0:
                flow_through_ratio = outgoing_total / incoming_total
                context[f"flow_through_ratio_{hours}h"] = flow_through_ratio
            else:
                context[f"flow_through_ratio_{hours}h"] = 0

        # Calculate average time between incoming and outgoing (velocity of moving money)
        # For recent 7-day window
        week_ago = (now - datetime.timedelta(days=7)).isoformat()

        recent_incoming = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.direction == "credit",
            Transaction.timestamp > week_ago
        ).order_by(Transaction.timestamp).all()

        recent_outgoing = self.db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.direction == "debit",
            Transaction.timestamp > week_ago
        ).order_by(Transaction.timestamp).all()

        # Calculate average time from incoming to next outgoing
        if recent_incoming and recent_outgoing:
            time_gaps = []
            for incoming in recent_incoming:
                incoming_time = datetime.datetime.fromisoformat(incoming.timestamp)
                # Find next outgoing after this incoming
                for outgoing in recent_outgoing:
                    outgoing_time = datetime.datetime.fromisoformat(outgoing.timestamp)
                    if outgoing_time > incoming_time:
                        gap_hours = (outgoing_time - incoming_time).total_seconds() / 3600
                        time_gaps.append(gap_hours)
                        break

            if time_gaps:
                avg_time_to_transfer = sum(time_gaps) / len(time_gaps)
                context["avg_hours_to_transfer"] = avg_time_to_transfer
            else:
                context["avg_hours_to_transfer"] = None
        else:
            context["avg_hours_to_transfer"] = None