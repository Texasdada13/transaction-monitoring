"""
FastAPI Application for Transaction Monitoring Dashboard

Provides REST API endpoints for the Streamlit dashboard to consume.
Leverages existing DashboardData and TransactionMonitor classes.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.database import get_db
from dashboard.main import DashboardData
from run import TransactionMonitor
from api.auth import authenticate_user, create_access_token, decode_token, Token, ACCESS_TOKEN_EXPIRE_MINUTES

# Initialize FastAPI
app = FastAPI(
    title="Transaction Monitoring API",
    description="REST API for fraud detection dashboard",
    version="1.0.0"
)

# CORS middleware (allow Streamlit to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# ==================== Response Models ====================

class OverviewStatsResponse(BaseModel):
    time_window_hours: int
    total_transactions: int
    total_value: float
    auto_approved: int
    manual_review: int
    blocked: int
    average_risk_score: float
    review_rate: float

class AlertItem(BaseModel):
    assessment_id: str
    transaction_id: str
    amount: float
    transaction_type: str
    risk_score: float
    triggered_rules: List[str]
    timestamp: str

class RuleStats(BaseModel):
    name: str
    description: str
    count: int
    weight: float

class AccountChangeItem(BaseModel):
    change_id: str
    employee_id: str
    change_type: str
    change_source: str
    verified: bool
    flagged: bool
    timestamp: str

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str
    database: str

# ==================== Authentication ====================

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT authentication token.

    Returns user information if token is valid.
    """
    token = credentials.credentials
    token_data = decode_token(token)

    if not token_data or not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": token_data.user_id,
        "role": token_data.role
    }

# ==================== Endpoints ====================

@app.get("/", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"
    }

@app.post("/api/v1/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint - authenticates user and returns JWT token.

    Test credentials:
    - Username: analyst, Password: analyst123 (Role: analyst)
    - Username: manager, Password: manager123 (Role: manager)
    - Username: investigator, Password: investigator123 (Role: investigator)
    - Username: admin, Password: admin123 (Role: admin)
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    access_token = create_access_token(
        data={"sub": user.user_id, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.user_id
    }

@app.get("/api/v1/overview", response_model=OverviewStatsResponse)
async def get_overview_stats(
    time_window_hours: int = 24,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """
    Get overview statistics for the dashboard.

    Args:
        time_window_hours: Time window for statistics (default 24 hours)

    Returns:
        Overview statistics including transaction counts, risk scores, etc.
    """
    dashboard = DashboardData(db)
    stats = dashboard.get_overview_stats(time_window_hours)
    return stats

@app.get("/api/v1/alerts/live", response_model=List[AlertItem])
async def get_live_alerts(
    limit: int = 100,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """
    Get live fraud alerts (manual review queue).

    Args:
        limit: Maximum number of alerts to return

    Returns:
        List of pending fraud alerts sorted by risk score (descending)
    """
    dashboard = DashboardData(db)
    queue = dashboard.get_manual_review_queue()
    return queue[:limit]

@app.get("/api/v1/rules/top", response_model=List[RuleStats])
async def get_top_triggered_rules(
    limit: int = 10,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """
    Get most frequently triggered fraud detection rules.

    Args:
        limit: Number of top rules to return

    Returns:
        List of rules sorted by trigger count
    """
    dashboard = DashboardData(db)
    rules = dashboard.get_top_triggered_rules(limit)
    return rules

@app.get("/api/v1/scenarios/breakdown")
async def get_scenario_breakdown(
    time_window_hours: int = 24,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """
    Get fraud activity breakdown by scenario type.

    Args:
        time_window_hours: Time window for analysis

    Returns:
        Breakdown of fraud activity by scenario (payroll, beneficiary, etc.)
    """
    dashboard = DashboardData(db)
    scenarios = dashboard.get_scenario_breakdown(time_window_hours)
    return scenarios

@app.get("/api/v1/account-changes/recent", response_model=List[AccountChangeItem])
async def get_recent_account_changes(
    limit: int = 20,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """
    Get recent account changes (for payroll fraud monitoring).

    Args:
        limit: Number of changes to return

    Returns:
        List of recent account changes
    """
    dashboard = DashboardData(db)
    changes = dashboard.get_recent_account_changes(limit)
    return changes

@app.get("/api/v1/transaction/{transaction_id}")
async def get_transaction_details(
    transaction_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """
    Get detailed information about a specific transaction.

    Args:
        transaction_id: Transaction ID to lookup

    Returns:
        Detailed transaction and risk assessment information
    """
    from app.models.database import Transaction, RiskAssessment
    import json

    # Get transaction
    tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Get risk assessment
    assessment = db.query(RiskAssessment).filter(
        RiskAssessment.transaction_id == transaction_id
    ).first()

    result = {
        "transaction_id": tx.transaction_id,
        "account_id": tx.account_id,
        "amount": tx.amount,
        "direction": tx.direction,
        "transaction_type": tx.transaction_type,
        "description": tx.description,
        "timestamp": tx.timestamp,
        "counterparty_id": tx.counterparty_id
    }

    if assessment:
        triggered_rules = json.loads(assessment.triggered_rules) if assessment.triggered_rules else {}
        result["risk_assessment"] = {
            "assessment_id": assessment.assessment_id,
            "risk_score": assessment.risk_score,
            "decision": assessment.decision,
            "review_status": assessment.review_status,
            "triggered_rules": triggered_rules,
            "review_notes": assessment.review_notes
        }

    return result

@app.post("/api/v1/alert/{assessment_id}/action")
async def update_alert_status(
    assessment_id: str,
    action: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """
    Update alert status (approve, reject, escalate).

    Args:
        assessment_id: Risk assessment ID
        action: Action to take (approved, rejected, escalated)
        notes: Optional review notes

    Returns:
        Updated assessment status
    """
    from app.models.database import RiskAssessment

    # Get assessment
    assessment = db.query(RiskAssessment).filter(
        RiskAssessment.assessment_id == assessment_id
    ).first()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Update status
    if action == "approved":
        assessment.review_status = "approved"
    elif action == "rejected":
        assessment.review_status = "rejected"
    elif action == "escalated":
        assessment.review_status = "escalated"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    assessment.review_notes = notes
    assessment.reviewer_id = user["user_id"]
    assessment.review_timestamp = datetime.utcnow().isoformat()

    db.commit()

    return {
        "assessment_id": assessment_id,
        "status": assessment.review_status,
        "reviewer": user["user_id"]
    }

@app.get("/api/v1/metrics/time-series")
async def get_time_series_metrics(
    time_range: str = "24h",
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """
    Get time-series metrics for trend analysis.

    Args:
        time_range: Time range (1h, 24h, 7d, 30d)

    Returns:
        Time-series data for charts
    """
    from app.models.database import RiskAssessment, Transaction

    # Parse time range
    time_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
    hours = time_map.get(time_range, 24)

    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    # Get assessments
    assessments = db.query(RiskAssessment).filter(
        RiskAssessment.review_timestamp > cutoff
    ).all()

    # Group by hour
    hourly_data = {}
    for assessment in assessments:
        hour = assessment.review_timestamp[:13]  # YYYY-MM-DDTHH
        if hour not in hourly_data:
            hourly_data[hour] = {
                "timestamp": hour,
                "count": 0,
                "avg_risk": 0,
                "total_risk": 0,
                "high_risk_count": 0,
                "manual_review_count": 0,
                "auto_approve_count": 0
            }

        hourly_data[hour]["count"] += 1
        hourly_data[hour]["total_risk"] += assessment.risk_score
        if assessment.risk_score > 0.6:
            hourly_data[hour]["high_risk_count"] += 1

        if assessment.decision == "manual_review":
            hourly_data[hour]["manual_review_count"] += 1
        elif assessment.decision == "auto_approve":
            hourly_data[hour]["auto_approve_count"] += 1

    # Calculate averages
    for data in hourly_data.values():
        if data["count"] > 0:
            data["avg_risk"] = data["total_risk"] / data["count"]

    return {
        "time_range": time_range,
        "data": sorted(hourly_data.values(), key=lambda x: x["timestamp"])
    }

@app.get("/api/v1/analytics/risk-distribution")
async def get_risk_distribution(
    time_range: str = "24h",
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """
    Get risk score distribution for histogram.

    Returns:
        Risk score bins and counts
    """
    from app.models.database import RiskAssessment

    time_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
    hours = time_map.get(time_range, 24)
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    assessments = db.query(RiskAssessment).filter(
        RiskAssessment.review_timestamp > cutoff
    ).all()

    risk_scores = [a.risk_score for a in assessments]

    return {
        "risk_scores": risk_scores,
        "total_count": len(risk_scores),
        "avg_risk": sum(risk_scores) / len(risk_scores) if risk_scores else 0,
        "max_risk": max(risk_scores) if risk_scores else 0,
        "min_risk": min(risk_scores) if risk_scores else 0
    }

@app.get("/api/v1/analytics/money-saved")
async def get_money_saved(
    time_range: str = "24h",
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """
    Calculate money saved by blocking fraudulent transactions.

    Returns:
        Amount saved, blocked count, etc.
    """
    from app.models.database import RiskAssessment, Transaction
    import json

    time_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
    hours = time_map.get(time_range, 24)
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    # Get high-risk transactions that were flagged
    assessments = db.query(RiskAssessment).filter(
        RiskAssessment.review_timestamp > cutoff,
        RiskAssessment.risk_score >= 0.6  # High risk threshold
    ).all()

    total_saved = 0
    blocked_count = 0
    prevented_fraud_count = 0

    for assessment in assessments:
        tx = db.query(Transaction).filter(
            Transaction.transaction_id == assessment.transaction_id
        ).first()

        if tx:
            # Count as prevented if manual review or high risk
            if assessment.decision == "manual_review" or assessment.review_status == "rejected":
                total_saved += tx.amount
                prevented_fraud_count += 1

            if assessment.review_status == "rejected":
                blocked_count += 1

    return {
        "total_amount_saved": total_saved,
        "blocked_transaction_count": blocked_count,
        "prevented_fraud_count": prevented_fraud_count,
        "high_risk_flagged": len(assessments),
        "time_range": time_range
    }

@app.get("/api/v1/analytics/module-performance")
async def get_module_performance(
    time_range: str = "24h",
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """
    Get performance metrics for each fraud detection module.

    Returns:
        Module statistics including trigger rates, accuracy, etc.
    """
    from app.models.database import RiskAssessment
    import json

    time_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
    hours = time_map.get(time_range, 24)
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    assessments = db.query(RiskAssessment).filter(
        RiskAssessment.review_timestamp > cutoff
    ).all()

    module_stats = {}

    for assessment in assessments:
        triggered = json.loads(assessment.triggered_rules) if assessment.triggered_rules else {}

        for rule_name, rule_info in triggered.items():
            if rule_name not in module_stats:
                module_stats[rule_name] = {
                    "name": rule_name,
                    "description": rule_info.get("description", ""),
                    "trigger_count": 0,
                    "total_weight": 0,
                    "avg_weight": 0,
                    "high_risk_triggers": 0,
                    "confirmed_fraud": 0
                }

            module_stats[rule_name]["trigger_count"] += 1
            module_stats[rule_name]["total_weight"] += rule_info.get("weight", 0)

            if assessment.risk_score >= 0.6:
                module_stats[rule_name]["high_risk_triggers"] += 1

            if assessment.review_status == "rejected":
                module_stats[rule_name]["confirmed_fraud"] += 1

    # Calculate averages
    for stats in module_stats.values():
        if stats["trigger_count"] > 0:
            stats["avg_weight"] = stats["total_weight"] / stats["trigger_count"]
            stats["precision"] = stats["confirmed_fraud"] / stats["trigger_count"] if stats["trigger_count"] > 0 else 0

    return {
        "modules": list(module_stats.values()),
        "total_modules": len(module_stats)
    }

# ==================== Run Application ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
