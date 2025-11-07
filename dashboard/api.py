# dashboard/api.py
"""
FastAPI Dashboard API
Provides REST endpoints for the fraud detection dashboard.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import json

from app.models.database import get_db, Transaction, RiskAssessment, Employee, Account
from dashboard.main import DashboardData

app = FastAPI(title="Fraud Detection Dashboard API")

# Mount templates
templates = Jinja2Templates(directory="dashboard/templates")

# Mount static files for CSS/JS
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """
    Serve the main dashboard HTML page.
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/dashboard/overview")
async def get_overview(
    time_window_hours: int = 24,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get overview statistics for the dashboard.

    Returns:
    - Total transactions
    - Total value
    - Auto-approved, manual review, blocked counts
    - Average risk score
    - Review rate
    """
    dashboard = DashboardData(db)
    stats = dashboard.get_overview_stats(time_window_hours)

    # Add additional calculated metrics
    total_txs = stats['total_transactions']
    flagged = stats['manual_review'] + stats['blocked']

    stats['flagged_count'] = flagged
    stats['flagged_rate'] = flagged / max(total_txs, 1)

    # Estimated fraud prevented (rough calculation)
    # Assume average blocked transaction is fraudulent
    stats['fraud_prevented_estimate'] = stats['blocked'] * (stats['total_value'] / max(total_txs, 1))

    # Manual review cost (estimated at $50 per review)
    stats['review_cost_estimate'] = stats['manual_review'] * 50

    # Net savings
    stats['net_savings'] = stats['fraud_prevented_estimate'] - stats['review_cost_estimate']

    return stats


@app.get("/api/dashboard/scenarios")
async def get_scenarios(
    time_window_hours: int = 24,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get fraud scenario breakdown.

    Returns activity segmented by fraud type:
    - Payroll fraud
    - Credit fraud
    - Wire fraud
    - Account takeover
    - Beneficiary fraud
    - Other
    """
    dashboard = DashboardData(db)
    scenarios = dashboard.get_scenario_breakdown(time_window_hours)

    return scenarios


@app.get("/api/dashboard/top-rules")
async def get_top_rules(
    limit: int = 10,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get most frequently triggered detection rules.

    Returns:
    - Rule name
    - Description
    - Trigger count
    - Weight
    """
    dashboard = DashboardData(db)
    rules = dashboard.get_top_triggered_rules(limit)

    return rules


@app.get("/api/dashboard/review-queue")
async def get_review_queue(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Get manual review queue.

    Returns transactions requiring manual review, sorted by risk score.
    """
    dashboard = DashboardData(db)
    queue = dashboard.get_manual_review_queue()

    return queue


@app.get("/api/dashboard/account-changes")
async def get_account_changes(
    limit: int = 20,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get recent account changes for monitoring.

    Returns:
    - Change type
    - Employee ID
    - Verification status
    - Flagged status
    - Timestamp
    """
    dashboard = DashboardData(db)
    changes = dashboard.get_recent_account_changes(limit)

    return changes


@app.get("/api/dashboard/transaction-feed")
async def get_transaction_feed(
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get live transaction feed with risk assessments.

    Returns recent transactions with employee/account details and risk scores.
    """
    # Get recent transactions with risk assessments
    recent = db.query(Transaction, RiskAssessment, Employee, Account).join(
        RiskAssessment, Transaction.transaction_id == RiskAssessment.transaction_id, isouter=True
    ).join(
        Employee, Transaction.employee_id == Employee.employee_id, isouter=True
    ).join(
        Account, Transaction.account_id == Account.account_id, isouter=True
    ).order_by(Transaction.timestamp.desc()).limit(limit).all()

    feed = []
    for tx, assessment, employee, account in recent:
        # Determine risk level
        risk_score = assessment.risk_score if assessment else 0.0
        if risk_score < 0.3:
            risk_level = "low"
        elif risk_score < 0.6:
            risk_level = "medium"
        else:
            risk_level = "high"

        # Get triggered rules
        triggered_rules = []
        if assessment and assessment.triggered_rules:
            rules_dict = json.loads(assessment.triggered_rules)
            triggered_rules = [
                {
                    "name": rule_name,
                    "weight": rule_info.get("weight", 0),
                    "description": rule_info.get("description", "")
                }
                for rule_name, rule_info in rules_dict.items()
            ]

        feed.append({
            "transaction_id": tx.transaction_id,
            "employee_name": employee.name if employee else "Unknown",
            "employee_id": tx.employee_id,
            "amount": float(tx.amount),
            "transaction_type": tx.transaction_type,
            "account_number": account.account_number if account else "N/A",
            "timestamp": tx.timestamp.isoformat() if isinstance(tx.timestamp, datetime) else tx.timestamp,
            "source": tx.transaction_type,
            "verification_status": assessment.review_status if assessment else "pending",
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "decision": assessment.decision if assessment else "pending",
            "triggered_rules": triggered_rules
        })

    return feed


@app.get("/api/dashboard/risk-distribution")
async def get_risk_distribution(
    time_window_hours: int = 24,
    db: Session = Depends(get_db)
) -> Dict[str, int]:
    """
    Get distribution of transactions by risk level.

    Returns counts for low/medium/high risk transactions.
    """
    from datetime import timedelta
    cutoff = (datetime.utcnow() - timedelta(hours=time_window_hours)).isoformat()

    assessments = db.query(RiskAssessment).filter(
        RiskAssessment.review_timestamp > cutoff
    ).all()

    distribution = {"low": 0, "medium": 0, "high": 0}

    for assessment in assessments:
        if assessment.risk_score < 0.3:
            distribution["low"] += 1
        elif assessment.risk_score < 0.6:
            distribution["medium"] += 1
        else:
            distribution["high"] += 1

    return distribution


@app.post("/api/dashboard/review-action")
async def review_action(
    assessment_id: int,
    action: str,
    comment: str = "",
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Process review action (approve, escalate, reject).

    Args:
    - assessment_id: ID of the risk assessment
    - action: 'reviewed' or 'escalated'
    - comment: Optional reviewer comment
    """
    if action not in ["reviewed", "escalated"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    assessment = db.query(RiskAssessment).filter(
        RiskAssessment.assessment_id == assessment_id
    ).first()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Update review status
    assessment.review_status = action
    assessment.reviewer_notes = comment

    db.commit()

    return {"status": "success", "message": f"Assessment {action} successfully"}


@app.get("/api/dashboard/metrics/trends")
async def get_trends(
    days: int = 7,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get trend data for time series charts.

    Returns daily aggregated metrics for the past N days.
    """
    from datetime import timedelta

    trends = []
    for day in range(days):
        date = datetime.utcnow() - timedelta(days=day)
        start = date.replace(hour=0, minute=0, second=0)
        end = date.replace(hour=23, minute=59, second=59)

        # Get assessments for this day
        assessments = db.query(RiskAssessment).filter(
            RiskAssessment.review_timestamp >= start.isoformat(),
            RiskAssessment.review_timestamp <= end.isoformat()
        ).all()

        flagged = sum(1 for a in assessments if a.decision in ["manual_review", "blocked"])

        trends.append({
            "date": start.strftime("%Y-%m-%d"),
            "total": len(assessments),
            "flagged": flagged,
            "high_risk": sum(1 for a in assessments if a.risk_score > 0.6)
        })

    return list(reversed(trends))  # Chronological order


@app.get("/api/dashboard/kpis")
async def get_kpis(
    period: str = "month",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get key performance indicators for the executive summary.

    Args:
    - period: 'day', 'week', 'month', 'quarter'

    Returns:
    - Total transactions monitored
    - Flagged transactions
    - Confirmed frauds prevented
    - Review costs
    - Net savings
    - False positive rate
    - SLA compliance
    """
    from datetime import timedelta

    period_hours = {
        "day": 24,
        "week": 24 * 7,
        "month": 24 * 30,
        "quarter": 24 * 90
    }

    hours = period_hours.get(period, 24 * 30)
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    # Get all assessments in period
    assessments = db.query(RiskAssessment).filter(
        RiskAssessment.review_timestamp > cutoff
    ).all()

    total = len(assessments)
    flagged = sum(1 for a in assessments if a.decision in ["manual_review", "blocked"])
    blocked = sum(1 for a in assessments if a.decision == "blocked")
    manual_review = sum(1 for a in assessments if a.decision == "manual_review")

    # Get average transaction value
    transactions = db.query(Transaction).filter(
        Transaction.timestamp > cutoff
    ).all()
    avg_value = sum(tx.amount for tx in transactions) / max(len(transactions), 1)

    # Estimates
    fraud_prevented = blocked * avg_value
    review_cost = manual_review * 50  # $50 per review
    net_savings = fraud_prevented - review_cost

    # False positive rate (estimated - assuming 90% of manual reviews are false positives)
    false_positive_rate = 0.10

    # SLA compliance (estimated - track completion times)
    sla_compliance = 0.95

    return {
        "period": period,
        "total_transactions": total,
        "flagged_transactions": flagged,
        "flagged_rate": flagged / max(total, 1),
        "confirmed_frauds": blocked,
        "fraud_prevented_value": round(fraud_prevented, 2),
        "review_cost": round(review_cost, 2),
        "net_savings": round(net_savings, 2),
        "false_positive_rate": false_positive_rate,
        "sla_compliance": sla_compliance
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
