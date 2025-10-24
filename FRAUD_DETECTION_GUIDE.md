# Low-Activity Large Transfer Fraud Detection

## Overview

This fraud detection rule identifies **unusually large transfers from low-activity accounts**, a common indicator of account compromise and fraudulent activity.

## Use Case

**Scenario**: A customer suddenly sends a much larger wire or ACH payment than they normally do, which can indicate fraud.

This pattern commonly occurs when:
- An account has been compromised (stolen credentials)
- Money mule activity
- Account takeover fraud
- Business Email Compromise (BEC)
- Wire fraud attempts

## How It Works

The rule triggers when **ALL** of the following conditions are met:

1. **Low Activity**: The account has few transactions (≤ threshold) in the analysis period
2. **Large Transfer**: The current transaction is significantly larger (≥ multiplier) than historical average
3. **Minimum Amount**: The transaction exceeds a minimum dollar amount

### Default Parameters

```python
low_activity_threshold = 5      # Max transactions to be "low-activity"
amount_multiplier = 3.0         # Current amount must be 3x average
min_amount = 1000.0             # Minimum $1,000 to trigger
timeframe_days = 90             # Look back 90 days
weight = 2.0                    # High risk weight
```

## Implementation

### Basic Usage

```python
from app.services.rules_engine import (
    RulesEngine,
    create_low_activity_large_transfer_rule
)

# Create the rules engine
engine = RulesEngine()

# Add the fraud detection rule with default parameters
fraud_rule = create_low_activity_large_transfer_rule()
engine.add_rule(fraud_rule)

# Evaluate a transaction
transaction = {
    "amount": 25000.00,
    "transaction_type": "WIRE",
    "account_id": "ACC-123"
}

context = {
    "total_tx_count_period": 2,        # Only 2 transactions in 90 days
    "avg_transaction_amount": 500.00   # Average is $500
}

triggered_rules = engine.evaluate_all(transaction, context)

if "low_activity_large_transfer" in triggered_rules:
    print("⚠️  FRAUD ALERT: Suspicious large transfer detected!")
```

### Custom Configuration

You can customize the rule parameters for different risk profiles:

```python
# Stricter rule for high-risk scenarios
strict_rule = create_low_activity_large_transfer_rule(
    low_activity_threshold=3,      # Even lower activity threshold
    amount_multiplier=2.0,          # Only 2x average needed
    min_amount=5000.0,              # Higher minimum amount
    weight=2.5                      # Higher risk weight
)

# More lenient rule for established customers
lenient_rule = create_low_activity_large_transfer_rule(
    low_activity_threshold=10,     # Allow more transactions
    amount_multiplier=5.0,          # Require 5x average
    min_amount=10000.0,             # Higher threshold
    weight=1.5                      # Lower risk weight
)
```

## Examples

### Example 1: Fraud Detected ✅

**Account Profile:**
- 2 transactions in past 90 days
- Average transaction: $350
- Account age: 45 days

**Current Transaction:**
- Amount: $25,000 WIRE transfer
- New counterparty

**Result:** **FLAGGED** - Large transfer from low-activity account

**Explanation:**
- Activity: 2 tx < 5 tx threshold ✓
- Size: $25,000 / $350 = 71x average > 3x ✓
- Amount: $25,000 > $1,000 minimum ✓

### Example 2: Legitimate Transaction ✅

**Account Profile:**
- 15 transactions in past 90 days
- Average transaction: $2,000
- Account age: 730 days

**Current Transaction:**
- Amount: $2,500 ACH payment
- Known counterparty

**Result:** **APPROVED** - Normal activity

**Explanation:**
- Activity: 15 tx > 5 tx threshold ✗
- The account has regular activity, so the rule doesn't trigger

### Example 3: First Large Transaction ✅

**Account Profile:**
- 0 transactions in past 90 days (dormant)
- No historical average
- Account age: 5 days

**Current Transaction:**
- Amount: $15,000 WIRE transfer

**Result:** **FLAGGED** - Suspicious first transaction

**Explanation:**
- Activity: 0 tx < 5 tx threshold ✓
- Size: First transaction > $1,000 minimum (special handling) ✓
- Amount: $15,000 > $1,000 minimum ✓

## Integration with Context Provider

The rule relies on context data gathered by `ContextProvider`:

```python
from app.services.context_provider import ContextProvider

# The context provider automatically calculates:
context = {
    "total_tx_count_period": X,        # Total transactions in 90 days
    "avg_transaction_amount": Y,       # Average amount for this tx type
    "account_age_days": Z,             # Days since account creation
}
```

## Testing

Run the comprehensive test suite:

```bash
pytest tests/test_rules_engine.py::TestLowActivityLargeTransferRule -v
```

Run the interactive demonstration:

```bash
python demo_fraud_detection.py
```

## Real-World Fraud Scenarios Detected

1. **Account Takeover**
   - Attacker gains access to dormant account
   - Attempts large wire transfer before detection

2. **Money Mule Recruitment**
   - Newly opened account receives large deposit
   - Immediately transfers funds to another account

3. **Credential Stuffing Success**
   - Compromised credentials from data breach
   - Used to access low-activity account for fraud

4. **Business Email Compromise (BEC)**
   - Employee account compromised
   - Fraudulent wire transfer initiated

5. **Wire Fraud**
   - Social engineering attack
   - Victim instructed to send large wire transfer

## Performance Considerations

- **Database Queries**: The rule requires 1 additional query (total transaction count)
- **Computation**: Minimal - simple arithmetic comparisons
- **False Positive Rate**: Low when properly tuned
- **False Negative Rate**: Low for typical account takeover scenarios

## Configuration Best Practices

1. **Start Conservative**: Use default parameters and monitor results
2. **Tune by Segment**: Different thresholds for retail vs. business accounts
3. **Monitor False Positives**: Adjust if legitimate transactions are flagged
4. **Combine Rules**: Use with velocity, counterparty, and other rules
5. **Regular Review**: Update thresholds as fraud patterns evolve

## Academic/Educational Value

This rule demonstrates several important concepts for school projects:

- **Statistical Analysis**: Comparing current behavior to historical patterns
- **Threshold-Based Detection**: Multiple criteria for decision-making
- **Context-Aware Systems**: Using historical data to inform decisions
- **Anomaly Detection**: Identifying outliers in transaction patterns
- **Risk Scoring**: Weighted contribution to overall fraud score
- **Real-World Application**: Production-ready fraud prevention technique

## References

This fraud detection pattern is based on industry-standard practices used by:
- Financial institutions for AML/CFT compliance
- Payment processors for fraud prevention
- FinCEN guidance on suspicious activity reporting
- FFIEC authentication guidance

## License

This code is provided for educational and experimental purposes.

## Support

For questions about this fraud detection rule:
1. Review the demonstration script: `demo_fraud_detection.py`
2. Run the test suite: `pytest tests/test_rules_engine.py`
3. Check the inline documentation in `app/services/rules_engine.py`
