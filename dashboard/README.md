# Fraud Detection Dashboard

A comprehensive web-based dashboard for real-time fraud detection and transaction monitoring, designed for multiple personas including Risk Officers, Fraud Analysts, and Leadership.

## Features

### Multi-Persona Dashboard Tabs

#### 1. Control Room (Risk Officer / Fraud Analyst)
- **Real-time Metrics KPIs**
  - Transactions screened today
  - Alerts flagged
  - Manual reviews in progress
  - Fraud prevented (estimated)

- **Live Transaction Feed**
  - Color-coded risk levels (Green/Yellow/Red)
  - Employee/account information
  - Original & new account numbers
  - Timestamp and source
  - Verification status
  - Risk scores prominently displayed

- **Manual Review Queue**
  - Sorted by risk score (descending)
  - "Reviewed" and "Escalated" action buttons
  - Comment section (optional)
  - Real-time updates

- **Risk Score Distribution**
  - Interactive gauge/chart
  - Visual breakdown by risk level

- **Triggered Rules & Explanations**
  - Rule name and description
  - Weight assigned
  - Trigger frequency
  - Detailed explanations

#### 2. Executive Summary (Leadership / Stakeholder)
- **Summary KPI Panels**
  - Total transactions monitored
  - Flagged transactions (count and percentage)
  - Confirmed frauds prevented
  - Manual review cost estimates
  - Net savings (fraud prevented - review costs)
  - False positive rate (target: < 15%)
  - SLA compliance (target: > 95%)

- **Risk Score Distribution**
  - Pie/bar chart by risk level
  - Visual breakdown of transaction risk

- **Trends and Time Series**
  - Line chart: Flagged transactions per week
  - Historical trend analysis
  - Total vs. flagged vs. high-risk transactions

- **Top Risk Contributors**
  - Ranked list of most common triggered rules
  - Contribution counts
  - Rule descriptions

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js
- **Database**: SQLAlchemy ORM
- **Server**: Uvicorn (ASGI)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure the database is initialized:
```bash
python -c "from app.models.database import init_db; init_db()"
```

## Running the Dashboard

### Method 1: Using run.py (Recommended)
```bash
python run.py --mode dashboard
```

### Method 2: Direct API launch
```bash
python dashboard/api.py
```

### Method 3: Using uvicorn
```bash
uvicorn dashboard.api:app --host 0.0.0.0 --port 8000
```

The dashboard will be available at: **http://localhost:8000**

## API Endpoints

### Dashboard Data Endpoints

- `GET /` - Main dashboard HTML page
- `GET /api/dashboard/overview` - Overview statistics
  - Query params: `time_window_hours` (default: 24)
- `GET /api/dashboard/scenarios` - Fraud scenario breakdown
- `GET /api/dashboard/top-rules` - Most triggered rules
  - Query params: `limit` (default: 10)
- `GET /api/dashboard/review-queue` - Manual review queue
- `GET /api/dashboard/account-changes` - Recent account changes
- `GET /api/dashboard/transaction-feed` - Live transaction feed
  - Query params: `limit` (default: 50)
- `GET /api/dashboard/risk-distribution` - Risk level distribution
- `GET /api/dashboard/metrics/trends` - Trend data for charts
  - Query params: `days` (default: 7)
- `GET /api/dashboard/kpis` - Executive KPIs
  - Query params: `period` (day/week/month/quarter)

### Action Endpoints

- `POST /api/dashboard/review-action` - Process review action
  - Body: `{assessment_id, action, comment}`
  - Actions: `reviewed`, `escalated`

## Dashboard Components

### Color Coding

**Risk Levels:**
- 🟢 **Green (Low)**: Risk score < 0.3
- 🟡 **Yellow (Medium)**: Risk score 0.3 - 0.6
- 🔴 **Red (High)**: Risk score > 0.6

**Decision Types:**
- ✅ **Auto-Approved**: Low risk, automatically approved
- 👁️ **Manual Review**: Requires analyst review
- 🚫 **Blocked**: High risk, automatically blocked

### Real-time Updates

The dashboard automatically refreshes every 30 seconds to display the latest data. You can also manually refresh specific components using the refresh buttons.

### Interactive Features

- **Click on transactions** to view detailed information including all triggered rules
- **Sort review queue** by risk score
- **Take action** on pending reviews with "Reviewed" or "Escalated" buttons
- **Switch between tabs** for different persona views
- **Select time periods** for executive summary (Day/Week/Month/Quarter)

## Metrics Explained

### False Positive Rate (FPR)
Percentage of flagged transactions that are not actually fraudulent. Target: < 15%

### SLA Compliance
Percentage of reviews completed within service level agreement timeframes. Target: > 95%

### Net Savings
Estimated fraud prevented minus the cost of manual reviews.

Formula: `(Blocked Transactions × Avg Transaction Value) - (Manual Reviews × $50)`

### Review Cost Estimate
Estimated at $50 per manual review based on analyst time and overhead.

## File Structure

```
dashboard/
├── README.md              # This file
├── api.py                 # FastAPI application and endpoints
├── main.py                # Dashboard data aggregation logic
├── templates/
│   └── dashboard.html     # Main dashboard HTML template
└── static/
    ├── css/
    │   └── dashboard.css  # Dashboard styling
    └── js/
        └── dashboard.js   # Dashboard JavaScript logic
```

## Customization

### Adding New Metrics

1. Add new endpoint in `api.py`
2. Update frontend in `dashboard.js` to fetch the data
3. Add display component in `dashboard.html`
4. Style as needed in `dashboard.css`

### Modifying Risk Thresholds

Risk thresholds can be adjusted in:
- **Backend**: `dashboard/api.py` (line ~230)
- **Frontend**: `dashboard.js` (line ~150)

### Changing Refresh Interval

Edit `dashboard.js` line ~15:
```javascript
refreshInterval = setInterval(() => {
    // ...
}, 30000);  // Change this value (milliseconds)
```

## Troubleshooting

### Dashboard won't start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that port 8000 is not in use
- Verify database is initialized

### No data displayed
- Run demo mode first to populate data: `python run.py --mode demo`
- Check database connection
- Verify API endpoints are responding: `curl http://localhost:8000/api/dashboard/overview`

### Charts not rendering
- Ensure Chart.js CDN is accessible
- Check browser console for JavaScript errors
- Verify data is being returned from API endpoints

## Development

To modify the dashboard:

1. **Backend changes**: Edit `dashboard/api.py`
2. **Frontend logic**: Edit `dashboard/static/js/dashboard.js`
3. **Styling**: Edit `dashboard/static/css/dashboard.css`
4. **Layout**: Edit `dashboard/templates/dashboard.html`

The server will need to be restarted after backend changes. Frontend changes (HTML/CSS/JS) require only a browser refresh.

## Future Enhancements

Planned features for future releases:

- [ ] Case Management Dashboard - Deep dive on specific cases
- [ ] Compliance Officer Dashboard - Accountability and reporting
- [ ] Model & Rule Performance Dashboard - Technical ML performance
- [ ] Operational Metrics - Compliance rates, review times, SLA tracking
- [ ] Advanced filtering and search
- [ ] Commenting system for reviews
- [ ] Data export capabilities (CSV, PDF)
- [ ] WebSocket support for true real-time updates
- [ ] User authentication and role-based access
- [ ] Customizable dashboards per user
- [ ] Mobile responsive improvements

## Support

For issues or questions, please refer to the main project documentation or open an issue in the repository.

## License

This dashboard is part of the Transaction Monitoring System project.
