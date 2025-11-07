# Transaction Monitoring BI Dashboard

A comprehensive Streamlit-based Business Intelligence dashboard for visualizing fraud detection patterns, risk distributions, and transaction analytics.

## Features

### 📊 8 Interactive Pages

1. **🏠 Executive Summary**
   - Total transactions and value processed
   - Auto-approval rates and average risk scores
   - Transaction volume trends
   - Decision distribution (auto-approve vs manual review)
   - Transaction type breakdown
   - Risk score histogram
   - Amount distribution analysis

2. **🔍 Fraud Scenario Analysis**
   - Payroll fraud detection metrics
   - Beneficiary fraud patterns
   - Check fraud indicators
   - Wire fraud analysis
   - Account takeover detection
   - Scenario comparison and rule frequency

3. **📋 Rule Performance**
   - Top 10 most triggered rules
   - Rule weight distribution
   - Average risk scores per rule
   - Common rule combinations
   - Detailed rule statistics table

4. **⚠️ Risk Distribution**
   - Risk category distribution (Low/Medium/High)
   - Risk score histogram
   - Risk trends over time
   - Risk by transaction type
   - Risk vs amount correlation
   - High-risk transaction details

5. **👥 Manual Review Queue**
   - Pending review items
   - Review status distribution
   - Priority queue (highest risk first)
   - Detailed transaction and risk information
   - Triggered rules for each transaction

6. **🏦 Account Activity**
   - Recent account changes
   - Employee account details
   - Beneficiary registry
   - Suspicious activity flags
   - Verification status tracking
   - Change source distribution

7. **⚡ Transaction Velocity**
   - Daily/hourly/weekly volume trends
   - Most active accounts
   - New counterparties tracking
   - Transaction burst detection
   - Off-hours activity alerts
   - Weekend transaction analysis
   - Amount velocity trends

8. **💰 Cost-Benefit Analysis**
   - Total review costs
   - Fraud prevention estimates
   - Net benefit calculations
   - ROI analysis
   - Cost-benefit by risk threshold
   - Optimal threshold recommendations

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Sample Data

```bash
# Generate comprehensive sample data with 100 transactions
python generate_comprehensive_data.py
```

This creates:
- 10 accounts
- 8 employees
- 10 beneficiaries
- 100 transactions
- 100 risk assessments
- Account and beneficiary change history

### 3. Launch Dashboard

```bash
streamlit run streamlit_app.py
```

The dashboard will open in your browser at http://localhost:8501

## Data Structure

The dashboard visualizes data from these database tables:

- **accounts** - Business accounts
- **transactions** - All financial transactions
- **employees** - Employee/payroll data
- **beneficiaries** - Vendor/payee registry
- **risk_assessments** - Fraud detection results
- **account_change_history** - Account modifications
- **beneficiary_change_history** - Vendor account changes

## Dashboard Navigation

Use the sidebar to navigate between pages. Each page provides different analytics and insights:

- Start with **Executive Summary** for overall metrics
- Drill down into **Fraud Scenarios** for specific fraud types
- Review **Rule Performance** to understand detection effectiveness
- Analyze **Risk Distribution** for risk patterns
- Monitor **Manual Review Queue** for pending items
- Track **Account Activity** for recent changes
- Examine **Transaction Velocity** for volume patterns
- Optimize with **Cost-Benefit Analysis**

## Key Metrics

### Risk Scores
- **0.0 - 0.3**: Low Risk (auto-approved)
- **0.3 - 0.6**: Medium Risk (may require review)
- **0.6 - 1.0**: High Risk (manual review required)

### Transaction Types
- `direct_deposit` - Payroll deposits
- `vendor_payment` - Payments to vendors
- `WIRE` - Wire transfers
- `ACH` - ACH transactions
- `CHECK_DEPOSIT` - Check deposits
- `TRANSFER` - Internal transfers

### Fraud Scenarios
- **Payroll Fraud** - Unauthorized account changes
- **Beneficiary Fraud** - Rapid beneficiary additions
- **Vendor Impersonation** - BEC attacks
- **Check Fraud** - Duplicate checks
- **Account Takeover** - Suspicious account access
- **Wire Fraud** - High-value wire transfers

## Customization

### Cost Parameters
In the **Cost-Benefit Analysis** page, you can adjust:
- Manual review cost (default: $18.75)
- Fraud prevention rate (default: 85%)

These affect ROI calculations and optimal threshold recommendations.

### Time Windows
Most pages analyze data from the last 30 days. You can modify this in the respective page files.

### Risk Thresholds
The default risk threshold for manual review is 0.6. The Cost-Benefit page helps identify optimal thresholds.

## Technical Stack

- **Streamlit** - Dashboard framework
- **Plotly** - Interactive visualizations
- **Pandas** - Data manipulation
- **SQLAlchemy** - Database ORM
- **SQLite** - Data storage

## Architecture

```
streamlit_app.py          # Main application entry point
pages/
  ├── executive_summary.py     # Page 1
  ├── fraud_scenarios.py       # Page 2
  ├── rule_performance.py      # Page 3
  ├── risk_distribution.py     # Page 4
  ├── review_queue.py          # Page 5
  ├── account_activity.py      # Page 6
  ├── transaction_velocity.py  # Page 7
  └── cost_benefit.py          # Page 8
```

## Data Generation

### Quick Start
```bash
python generate_comprehensive_data.py
```

### Custom Scenarios
Run individual scenario generators:
```bash
python app/scenarios/payroll_reroute_scenario.py
python app/scenarios/beneficiary_fraud_scenario.py
python app/scenarios/vendor_impersonation_scenario.py
```

### Test Data
Run the test suite to generate additional test data:
```bash
python -m pytest tests/ -v
```

## Troubleshooting

### "No data available" warnings
- Run `python generate_comprehensive_data.py` to create sample data
- Verify `transaction_monitoring.db` exists in the project root

### Import errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that you're running from the project root directory

### Database errors
- Delete `transaction_monitoring.db` and regenerate data
- Check SQLAlchemy version compatibility

## Future Enhancements

Potential additions:
- Real-time data streaming
- Alert notifications
- Export reports to PDF/Excel
- Custom date range filtering
- User authentication
- Role-based access control
- Machine learning model integration
- Predictive fraud analytics

## Support

For issues or questions about the Transaction Monitoring System, please refer to the main project documentation.

---

**Version**: 1.0
**Last Updated**: 2025-10-27
