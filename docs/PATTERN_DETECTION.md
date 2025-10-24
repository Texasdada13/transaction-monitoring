# Pattern Detection Module

## Overview

The Pattern Detection module provides advanced fraud detection capabilities by identifying complex behavioral patterns that indicate fraudulent activity. This goes beyond simple threshold-based rules by analyzing transaction sequences and temporal patterns.

## Small Test - Large Withdrawal Pattern

### Description

This pattern detector identifies a common fraud technique where attackers:

1. **Testing Phase**: Execute multiple small transactions to verify that a compromised account is functional
2. **Exploitation Phase**: Once confirmed, quickly move larger sums before the fraud is detected

This is a high-confidence fraud indicator because legitimate users rarely exhibit this behavior pattern.

### How It Works

The detector analyzes:

- **Small Transaction Count**: Number of small transactions in the lookback window
- **Amount Ratios**: Ratio between large withdrawal and average small transaction amounts
- **Temporal Clustering**: How recently the small transactions occurred
- **Transaction Types**: Whether the current transaction is a withdrawal type

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `small_amount_threshold` | $50.00 | Maximum amount to consider a "small" transaction |
| `large_amount_threshold` | $1000.00 | Minimum amount to consider a "large" withdrawal |
| `min_small_transactions` | 3 | Minimum number of small transactions required |
| `lookback_hours` | 24 | Time window to search for small transactions |
| `withdrawal_types` | `["WITHDRAWAL", "WIRE", "ACH_OUT", "TRANSFER_OUT"]` | Transaction types considered withdrawals |

### Confidence Scoring

The detector calculates a confidence score (0.0 to 1.0) based on three components:

1. **Count Score (40% weight)**: More small transactions = higher confidence
   - Normalized with maximum at 10 transactions
   - Formula: `min(count / 10.0, 1.0)`

2. **Ratio Score (40% weight)**: Larger withdrawal relative to small amounts = higher confidence
   - Normalized with maximum at 100x ratio
   - Formula: `min(amount_ratio / 100.0, 1.0)`

3. **Time Clustering Score (20% weight)**: More recent small transactions = higher confidence
   - More recent transactions indicate active testing
   - Formula: `1.0 - (hours_ago / (lookback_hours * 2))`

**Final Confidence**: `count_score * 0.4 + ratio_score * 0.4 + time_clustering_score * 0.2`

### Detection Output

The detector returns a dictionary with:

```python
{
    "detected": bool,              # Whether pattern was found
    "confidence": float,           # Confidence score (0.0-1.0)
    "details": {
        "small_transaction_count": int,
        "small_transaction_amounts": List[float],
        "avg_small_amount": float,
        "large_withdrawal_amount": float,
        "amount_ratio": float,
        "lookback_hours": int,
        "small_threshold": float,
        "large_threshold": float,
        "confidence_breakdown": {
            "count_score": float,
            "ratio_score": float,
            "time_clustering_score": float
        }
    }
}
```

## Usage Examples

### Basic Usage

```python
from app.models.database import SessionLocal
from app.services.pattern_detectors import create_small_test_pattern_detector

# Initialize database session
db = SessionLocal()

# Create detector with default settings
detector = create_small_test_pattern_detector(db)

# Evaluate a transaction
transaction = {
    "account_id": "ACC123",
    "amount": 2500.00,
    "transaction_type": "WIRE"
}

result = detector.detect(transaction, {})

if result["detected"]:
    print(f"Pattern detected with {result['confidence']:.1%} confidence")
    print(f"Found {result['details']['small_transaction_count']} small transactions")
```

### Integration with Rules Engine

```python
from app.services.rules_engine import (
    RulesEngine,
    create_small_test_large_withdrawal_rule
)
from app.services.pattern_detectors import create_small_test_pattern_detector
from app.services.context_provider import ContextProvider

# Initialize components
db = SessionLocal()
rules_engine = RulesEngine()
context_provider = ContextProvider(db)

# Create and add pattern detection rule
detector = create_small_test_pattern_detector(db)
pattern_rule = create_small_test_large_withdrawal_rule(
    detector,
    min_confidence=0.6,  # Only trigger if confidence >= 60%
    weight=2.5           # High weight for risk scoring
)
rules_engine.add_rule(pattern_rule)

# Evaluate transaction
transaction = {...}
context = context_provider.get_transaction_context(transaction)
triggered_rules = rules_engine.evaluate_all(transaction, context)

if "small_test_large_withdrawal_pattern" in triggered_rules:
    print("⚠️  Fraud pattern detected!")
```

### Custom Thresholds for Different Risk Profiles

```python
# Strict settings for high-risk accounts
high_risk_detector = create_small_test_pattern_detector(
    db,
    small_amount_threshold=25.0,   # More sensitive
    large_amount_threshold=500.0,  # Lower threshold
    min_small_transactions=2,      # Fewer required
    lookback_hours=48              # Longer window
)

# Relaxed settings for low-risk, verified accounts
low_risk_detector = create_small_test_pattern_detector(
    db,
    small_amount_threshold=100.0,  # Less sensitive
    large_amount_threshold=5000.0, # Higher threshold
    min_small_transactions=5,      # More required
    lookback_hours=12              # Shorter window
)
```

## Real-World Scenario

### Example Fraud Case

**Timeline**:
- Day 1, 10:00 AM: Fraudster gains access to account credentials
- Day 1, 10:15 AM: Test transaction #1 - $15 deposit (verify account works)
- Day 1, 10:30 AM: Test transaction #2 - $25 deposit (verify limits)
- Day 1, 11:00 AM: Test transaction #3 - $30 deposit (confirm smooth processing)
- Day 1, 11:30 AM: Test transaction #4 - $20 deposit (build confidence)
- Day 1, 12:00 PM: **Large withdrawal - $2,500 wire transfer** ⚠️

**Detection Results**:
```
Pattern Detected: True
Confidence Score: 78.5%

Pattern Details:
  • Small transactions found: 4
  • Small transaction amounts: [15.0, 25.0, 30.0, 20.0]
  • Average small amount: $22.50
  • Large withdrawal amount: $2,500.00
  • Amount ratio: 111.1x

Confidence Breakdown:
  • Count score (40%): 0.400 (4 transactions)
  • Ratio score (40%): 1.000 (111x ratio maxed out)
  • Time clustering (20%): 0.950 (very recent)
```

### Legitimate Use Case (Not Triggered)

**Timeline**:
- Week 1: Regular salary deposit $3,000
- Week 2: Regular salary deposit $3,000
- Week 3: Regular salary deposit $3,000
- Week 4: Large withdrawal $2,500 (down payment on car)

**Detection Results**:
```
Pattern Detected: False
Reason: Current transaction amount too small relative to threshold
        (regular deposits are large, not small test amounts)
```

## Performance Considerations

### Database Queries

The detector executes **one database query** per detection:
- Query: Fetch small transactions within lookback window
- Indexed fields: `account_id`, `timestamp`, `amount`

**Optimization tips**:
- Ensure indexes exist on `transactions(account_id, timestamp)`
- For high-volume systems, consider caching recent transactions
- Adjust `lookback_hours` based on your fraud patterns (shorter = faster)

### Recommended Settings by Volume

| Transaction Volume | Lookback Hours | Query Impact |
|-------------------|----------------|--------------|
| < 1K/day | 48 hours | Negligible |
| 1K-10K/day | 24 hours | Low |
| 10K-100K/day | 12 hours | Moderate |
| > 100K/day | 6 hours | Consider caching |

## Integration with Risk Scoring

The pattern detection integrates seamlessly with the risk scoring system:

```python
from app.services.risk_scoring import RiskScorer

# Pattern rule has weight of 2.5 (high severity)
risk_scorer = RiskScorer()
risk_score = risk_scorer.calculate_risk(triggered_rules, context)

# If pattern is detected with high confidence:
# - Risk score increases significantly due to weight of 2.5
# - Likely to trigger manual review threshold
# - Provides detailed explanation for reviewers
```

## Testing

Run the test suite:

```bash
# Run pattern detector tests
python -m pytest tests/test_pattern_detectors.py -v

# Run specific test
python -m pytest tests/test_pattern_detectors.py::TestSmallTestLargeWithdrawalDetector::test_pattern_detected_basic -v

# Run with coverage
python -m pytest tests/test_pattern_detectors.py --cov=app.services.pattern_detectors
```

## Examples

See complete working examples:

```bash
# Run all examples
python examples/small_test_pattern_example.py

# Output includes:
# - Example 1: Basic pattern detection
# - Example 2: Rules engine integration
# - Example 3: Custom thresholds for different risk profiles
```

## Future Enhancements

Potential improvements to the pattern detector:

1. **Machine Learning Integration**: Train ML models on historical fraud cases
2. **Velocity Patterns**: Detect unusual transaction frequency changes
3. **Counterparty Analysis**: Flag new counterparties in large withdrawals
4. **Geographic Patterns**: Detect location changes combined with testing
5. **Multi-Pattern Correlation**: Combine multiple pattern detectors

## API Reference

### Classes

#### `SmallTestLargeWithdrawalDetector`

**Constructor**:
```python
__init__(
    db: Session,
    small_amount_threshold: float = 50.0,
    large_amount_threshold: float = 1000.0,
    min_small_transactions: int = 3,
    lookback_hours: int = 24,
    withdrawal_types: List[str] = None
)
```

**Methods**:

- `detect(transaction: Dict, context: Dict) -> Dict`: Run pattern detection
- `get_pattern_context(account_id: str) -> Dict`: Get pattern-specific context

### Functions

#### `create_small_test_pattern_detector`

Factory function to create detector instance.

```python
create_small_test_pattern_detector(
    db: Session,
    **kwargs  # Override any default parameters
) -> SmallTestLargeWithdrawalDetector
```

#### `create_small_test_large_withdrawal_rule`

Create a rule for the rules engine.

```python
create_small_test_large_withdrawal_rule(
    pattern_detector: SmallTestLargeWithdrawalDetector,
    min_confidence: float = 0.5,
    rule_name: str = None,
    weight: float = 2.0
) -> Rule
```

## Support

For questions or issues:
- Review test cases in `tests/test_pattern_detectors.py`
- Run examples in `examples/small_test_pattern_example.py`
- Check system logs for detection details
