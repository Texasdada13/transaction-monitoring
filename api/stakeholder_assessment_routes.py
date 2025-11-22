"""
FastAPI routes for Stakeholder Assessment Tool

Provides REST API endpoints for managing stakeholders, interviews,
responses, and analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from app.services.stakeholder_assessment import (
    assessment_store,
    StakeholderType,
    InterviewStatus,
    QuestionCategory,
    ASSESSMENT_QUESTIONS,
    CATEGORY_NAMES,
    CATEGORY_WEIGHTS,
    get_questions_by_category,
    get_question_by_id
)


router = APIRouter(prefix="/api/v1/stakeholder-assessment", tags=["Stakeholder Assessment"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class StakeholderCreate(BaseModel):
    name: str
    email: str
    role: str
    department: str
    stakeholder_type: str
    applications: List[str] = []
    phone: Optional[str] = None
    availability: Optional[str] = None
    notes: Optional[str] = None


class StakeholderUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    stakeholder_type: Optional[str] = None
    applications: Optional[List[str]] = None
    phone: Optional[str] = None
    availability: Optional[str] = None
    notes: Optional[str] = None


class InterviewCreate(BaseModel):
    stakeholder_id: str
    application_id: str
    scheduled_date: Optional[str] = None
    interviewer_id: Optional[str] = None
    notes: Optional[str] = None


class InterviewUpdate(BaseModel):
    scheduled_date: Optional[str] = None
    interviewer_id: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    duration_minutes: Optional[int] = None


class ResponseCreate(BaseModel):
    question_id: str
    numeric_value: Optional[int] = None
    text_value: Optional[str] = None
    confidence_level: int = 3
    notes: Optional[str] = None


class BatchResponseCreate(BaseModel):
    responses: List[ResponseCreate]


class SuccessResponse(BaseModel):
    success: bool
    message: str


# ============================================================================
# STAKEHOLDER ENDPOINTS
# ============================================================================

@router.get("/stakeholders")
async def list_stakeholders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    stakeholder_type: Optional[str] = None,
    application_id: Optional[str] = None
):
    """List all stakeholders with optional filtering."""
    stakeholders = assessment_store.get_all_stakeholders()

    # Apply filters
    if search:
        search_lower = search.lower()
        stakeholders = [
            s for s in stakeholders
            if search_lower in s.name.lower()
            or search_lower in s.email.lower()
            or search_lower in s.department.lower()
        ]

    if stakeholder_type:
        stakeholders = [s for s in stakeholders if s.stakeholder_type.value == stakeholder_type]

    if application_id:
        stakeholders = [s for s in stakeholders if application_id in s.applications]

    # Pagination
    total = len(stakeholders)
    start = (page - 1) * limit
    end = start + limit
    paginated = stakeholders[start:end]

    return {
        "stakeholders": [s.to_dict() for s in paginated],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/stakeholders/{stakeholder_id}")
async def get_stakeholder(stakeholder_id: str):
    """Get a specific stakeholder by ID."""
    stakeholder = assessment_store.get_stakeholder(stakeholder_id)
    if not stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    # Get interview history
    interviews = assessment_store.get_all_interviews(stakeholder_id=stakeholder_id)

    result = stakeholder.to_dict()
    result["interviews"] = [i.to_dict() for i in interviews]

    return result


@router.post("/stakeholders")
async def create_stakeholder(data: StakeholderCreate):
    """Create a new stakeholder."""
    try:
        stakeholder_type = StakeholderType(data.stakeholder_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stakeholder type: {data.stakeholder_type}")

    stakeholder = assessment_store.create_stakeholder(
        name=data.name,
        email=data.email,
        role=data.role,
        department=data.department,
        stakeholder_type=stakeholder_type,
        applications=data.applications,
        phone=data.phone,
        availability=data.availability,
        notes=data.notes
    )

    return stakeholder.to_dict()


@router.put("/stakeholders/{stakeholder_id}")
async def update_stakeholder(stakeholder_id: str, data: StakeholderUpdate):
    """Update an existing stakeholder."""
    update_data = data.dict(exclude_unset=True)

    if "stakeholder_type" in update_data:
        try:
            update_data["stakeholder_type"] = StakeholderType(update_data["stakeholder_type"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid stakeholder type")

    stakeholder = assessment_store.update_stakeholder(stakeholder_id, **update_data)
    if not stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    return stakeholder.to_dict()


@router.delete("/stakeholders/{stakeholder_id}")
async def delete_stakeholder(stakeholder_id: str):
    """Delete a stakeholder."""
    success = assessment_store.delete_stakeholder(stakeholder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    return {"success": True, "message": "Stakeholder deleted successfully"}


# ============================================================================
# INTERVIEW ENDPOINTS
# ============================================================================

@router.get("/interviews")
async def list_interviews(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    stakeholder_id: Optional[str] = None,
    application_id: Optional[str] = None
):
    """List all interviews with optional filtering."""
    interviews = assessment_store.get_all_interviews(
        status=status,
        stakeholder_id=stakeholder_id,
        application_id=application_id
    )

    # Pagination
    total = len(interviews)
    start = (page - 1) * limit
    end = start + limit
    paginated = interviews[start:end]

    # Enrich with stakeholder names
    results = []
    for interview in paginated:
        interview_dict = interview.to_dict()
        stakeholder = assessment_store.get_stakeholder(interview.stakeholder_id)
        interview_dict["stakeholder_name"] = stakeholder.name if stakeholder else "Unknown"
        results.append(interview_dict)

    return {
        "interviews": results,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/interviews/{session_id}")
async def get_interview(session_id: str):
    """Get a specific interview by ID."""
    interview = assessment_store.get_interview(session_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    result = interview.to_dict()

    # Enrich with stakeholder info
    stakeholder = assessment_store.get_stakeholder(interview.stakeholder_id)
    if stakeholder:
        result["stakeholder"] = stakeholder.to_dict()

    return result


@router.post("/interviews")
async def create_interview(data: InterviewCreate):
    """Create a new interview session."""
    # Validate stakeholder exists
    stakeholder = assessment_store.get_stakeholder(data.stakeholder_id)
    if not stakeholder:
        raise HTTPException(status_code=404, detail="Stakeholder not found")

    scheduled_date = None
    if data.scheduled_date:
        try:
            scheduled_date = datetime.fromisoformat(data.scheduled_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

    interview = assessment_store.create_interview(
        stakeholder_id=data.stakeholder_id,
        application_id=data.application_id,
        scheduled_date=scheduled_date,
        interviewer_id=data.interviewer_id,
        notes=data.notes
    )

    return interview.to_dict()


@router.put("/interviews/{session_id}")
async def update_interview(session_id: str, data: InterviewUpdate):
    """Update an existing interview."""
    update_data = data.dict(exclude_unset=True)

    if "scheduled_date" in update_data and update_data["scheduled_date"]:
        try:
            update_data["scheduled_date"] = datetime.fromisoformat(
                update_data["scheduled_date"].replace('Z', '+00:00')
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

    if "status" in update_data:
        try:
            update_data["status"] = InterviewStatus(update_data["status"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")

    interview = assessment_store.update_interview(session_id, **update_data)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    return interview.to_dict()


@router.delete("/interviews/{session_id}")
async def delete_interview(session_id: str):
    """Delete an interview session."""
    success = assessment_store.delete_interview(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Interview not found")

    return {"success": True, "message": "Interview deleted successfully"}


@router.post("/interviews/{session_id}/start")
async def start_interview(session_id: str):
    """Start an interview session."""
    interview = assessment_store.start_interview(session_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    return interview.to_dict()


@router.post("/interviews/{session_id}/complete")
async def complete_interview(session_id: str):
    """Complete an interview session and calculate scores."""
    interview = assessment_store.complete_interview(session_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    return interview.to_dict()


# ============================================================================
# RESPONSE ENDPOINTS
# ============================================================================

@router.get("/interviews/{session_id}/responses")
async def get_interview_responses(session_id: str):
    """Get all responses for an interview."""
    interview = assessment_store.get_interview(session_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    responses = assessment_store.get_interview_responses(session_id)

    return {
        "responses": [r.to_dict() for r in responses],
        "completion_percentage": interview.completion_percentage
    }


@router.post("/interviews/{session_id}/responses")
async def submit_response(session_id: str, data: ResponseCreate):
    """Submit a response for a question."""
    interview = assessment_store.get_interview(session_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Validate question exists
    question = get_question_by_id(data.question_id)
    if not question:
        raise HTTPException(status_code=400, detail=f"Invalid question ID: {data.question_id}")

    response = assessment_store.add_response(
        session_id=session_id,
        question_id=data.question_id,
        numeric_value=data.numeric_value,
        text_value=data.text_value,
        confidence_level=data.confidence_level,
        notes=data.notes
    )

    return response.to_dict()


@router.post("/interviews/{session_id}/responses/batch")
async def submit_batch_responses(session_id: str, data: BatchResponseCreate):
    """Submit multiple responses at once."""
    interview = assessment_store.get_interview(session_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    success_count = 0
    failed = []

    for response_data in data.responses:
        question = get_question_by_id(response_data.question_id)
        if not question:
            failed.append({
                "question_id": response_data.question_id,
                "error": "Invalid question ID"
            })
            continue

        assessment_store.add_response(
            session_id=session_id,
            question_id=response_data.question_id,
            numeric_value=response_data.numeric_value,
            text_value=response_data.text_value,
            confidence_level=response_data.confidence_level,
            notes=response_data.notes
        )
        success_count += 1

    return {
        "success": success_count,
        "failed": len(failed),
        "errors": failed
    }


# ============================================================================
# QUESTION ENDPOINTS
# ============================================================================

@router.get("/questions")
async def list_questions(category: Optional[str] = None):
    """Get all assessment questions, optionally filtered by category."""
    if category:
        try:
            cat_enum = QuestionCategory(category)
            questions = get_questions_by_category(cat_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    else:
        questions = ASSESSMENT_QUESTIONS

    return {
        "questions": [q.to_dict() for q in questions],
        "total": len(questions)
    }


@router.get("/questions/categories")
async def list_categories():
    """Get all question categories with their weights."""
    categories = []
    for cat in QuestionCategory:
        categories.append({
            "id": cat.value,
            "name": CATEGORY_NAMES.get(cat, cat.value),
            "weight": CATEGORY_WEIGHTS.get(cat, 10),
            "question_count": len(get_questions_by_category(cat))
        })

    return {"categories": categories}


@router.get("/questions/category/{category}")
async def get_questions_by_cat(category: str):
    """Get questions for a specific category."""
    try:
        cat_enum = QuestionCategory(category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

    questions = get_questions_by_category(cat_enum)

    return {
        "questions": [q.to_dict() for q in questions],
        "category_info": {
            "id": cat_enum.value,
            "name": CATEGORY_NAMES.get(cat_enum, category),
            "weight": CATEGORY_WEIGHTS.get(cat_enum, 10)
        }
    }


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@router.get("/analysis/interview/{session_id}")
async def analyze_interview(session_id: str):
    """Get analysis for a specific interview."""
    analysis = assessment_store.get_interview_analysis(session_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Interview not found")

    return analysis


@router.get("/analysis/application/{application_id}")
async def analyze_application(application_id: str, include_history: bool = False):
    """Get analysis for a specific application across all interviews."""
    analysis = assessment_store.get_application_analysis(application_id)

    if include_history:
        interviews = assessment_store.get_all_interviews(application_id=application_id)
        analysis["interview_history"] = [
            {
                "session_id": i.session_id,
                "date": i.conducted_date.isoformat() if i.conducted_date else None,
                "score": i.overall_score,
                "status": i.status.value
            }
            for i in interviews
        ]

    return analysis


@router.get("/analysis/portfolio")
async def analyze_portfolio(application_ids: Optional[str] = None):
    """Get portfolio-wide analysis."""
    analysis = assessment_store.get_portfolio_analysis()
    return analysis


@router.post("/analysis/compare")
async def compare_applications(application_ids: List[str], metrics: Optional[List[str]] = None):
    """Compare multiple applications."""
    comparisons = []

    for app_id in application_ids:
        app_analysis = assessment_store.get_application_analysis(app_id)
        comparisons.append({
            "application_id": app_id,
            "average_score": app_analysis.get("average_score", 0),
            "category_averages": app_analysis.get("category_averages", {}),
            "interviews_count": app_analysis.get("interviews_count", 0)
        })

    return {
        "applications": comparisons,
        "comparison_count": len(comparisons)
    }


# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@router.get("/statistics")
async def get_statistics():
    """Get overall statistics for the dashboard."""
    return assessment_store.get_statistics()


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@router.get("/export/interview/{session_id}")
async def export_interview(session_id: str, format: str = "json"):
    """Export interview data."""
    interview = assessment_store.get_interview(session_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if format == "json":
        analysis = assessment_store.get_interview_analysis(session_id)
        return {
            "interview": interview.to_dict(),
            "analysis": analysis
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
