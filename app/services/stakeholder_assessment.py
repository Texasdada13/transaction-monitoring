"""
Stakeholder Assessment Engine

Complete backend implementation for stakeholder assessment interviews,
scoring, and analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid
import json


# ============================================================================
# ENUMERATIONS
# ============================================================================

class StakeholderType(str, Enum):
    BUSINESS_OWNER = "business_owner"
    TECHNICAL_LEAD = "technical_lead"
    END_USER = "end_user"
    EXECUTIVE = "executive"
    IT_OPERATIONS = "it_operations"
    COMPLIANCE = "compliance"


class InterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class QuestionCategory(str, Enum):
    BUSINESS_VALUE = "business_value"
    USER_SATISFACTION = "user_satisfaction"
    TECHNICAL_HEALTH = "technical_health"
    CHANGE_READINESS = "change_readiness"
    DEPENDENCIES = "dependencies"
    COST_AWARENESS = "cost_awareness"
    FUTURE_NEEDS = "future_needs"


class QuestionType(str, Enum):
    SCALE = "scale"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    YES_NO = "yes_no"
    RANKING = "ranking"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Stakeholder:
    """Represents a stakeholder who provides assessment input."""
    stakeholder_id: str
    name: str
    email: str
    role: str
    department: str
    stakeholder_type: StakeholderType
    applications: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    phone: Optional[str] = None
    availability: Optional[str] = None

    @classmethod
    def create(cls, name: str, email: str, role: str, department: str,
               stakeholder_type: StakeholderType, **kwargs) -> 'Stakeholder':
        return cls(
            stakeholder_id=str(uuid.uuid4()),
            name=name,
            email=email,
            role=role,
            department=department,
            stakeholder_type=stakeholder_type,
            **kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'stakeholder_id': self.stakeholder_id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'department': self.department,
            'stakeholder_type': self.stakeholder_type.value if isinstance(self.stakeholder_type, Enum) else self.stakeholder_type,
            'applications': self.applications,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'notes': self.notes,
            'phone': self.phone,
            'availability': self.availability
        }


@dataclass
class Question:
    """Represents an assessment question."""
    question_id: str
    category: QuestionCategory
    text: str
    question_type: QuestionType
    weight: float = 1.0
    order: int = 0
    required: bool = True
    description: Optional[str] = None
    options: Optional[List[str]] = None
    option_values: Optional[Dict[str, int]] = None
    follow_up_trigger: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'question_id': self.question_id,
            'category': self.category.value if isinstance(self.category, Enum) else self.category,
            'text': self.text,
            'question_type': self.question_type.value if isinstance(self.question_type, Enum) else self.question_type,
            'weight': self.weight,
            'order': self.order,
            'required': self.required,
            'description': self.description,
            'options': self.options,
            'option_values': self.option_values
        }


@dataclass
class Response:
    """Represents a stakeholder's response to a question."""
    response_id: str
    session_id: str
    question_id: str
    numeric_value: Optional[int] = None
    text_value: Optional[str] = None
    confidence_level: int = 3
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(cls, session_id: str, question_id: str, **kwargs) -> 'Response':
        return cls(
            response_id=str(uuid.uuid4()),
            session_id=session_id,
            question_id=question_id,
            **kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'response_id': self.response_id,
            'session_id': self.session_id,
            'question_id': self.question_id,
            'numeric_value': self.numeric_value,
            'text_value': self.text_value,
            'confidence_level': self.confidence_level,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class InterviewSession:
    """Represents an assessment interview session."""
    session_id: str
    stakeholder_id: str
    application_id: str
    interviewer_id: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    conducted_date: Optional[datetime] = None
    status: InterviewStatus = InterviewStatus.SCHEDULED
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    overall_score: Optional[float] = None
    category_scores: Dict[str, float] = field(default_factory=dict)
    responses: List[Response] = field(default_factory=list)

    @classmethod
    def create(cls, stakeholder_id: str, application_id: str, **kwargs) -> 'InterviewSession':
        return cls(
            session_id=str(uuid.uuid4()),
            stakeholder_id=stakeholder_id,
            application_id=application_id,
            **kwargs
        )

    @property
    def completion_percentage(self) -> float:
        total_questions = len(ASSESSMENT_QUESTIONS)
        answered = len([r for r in self.responses if r.numeric_value is not None or r.text_value is not None])
        return (answered / total_questions * 100) if total_questions > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'stakeholder_id': self.stakeholder_id,
            'application_id': self.application_id,
            'interviewer_id': self.interviewer_id,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'conducted_date': self.conducted_date.isoformat() if self.conducted_date else None,
            'status': self.status.value if isinstance(self.status, Enum) else self.status,
            'duration_minutes': self.duration_minutes,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'overall_score': self.overall_score,
            'category_scores': self.category_scores,
            'completion_percentage': self.completion_percentage,
            'responses': [r.to_dict() for r in self.responses]
        }


# ============================================================================
# QUESTION DEFINITIONS
# ============================================================================

CATEGORY_WEIGHTS = {
    QuestionCategory.BUSINESS_VALUE: 20,
    QuestionCategory.USER_SATISFACTION: 15,
    QuestionCategory.TECHNICAL_HEALTH: 20,
    QuestionCategory.CHANGE_READINESS: 15,
    QuestionCategory.DEPENDENCIES: 10,
    QuestionCategory.COST_AWARENESS: 10,
    QuestionCategory.FUTURE_NEEDS: 10
}

CATEGORY_NAMES = {
    QuestionCategory.BUSINESS_VALUE: "Business Value & Criticality",
    QuestionCategory.USER_SATISFACTION: "User Satisfaction & Experience",
    QuestionCategory.TECHNICAL_HEALTH: "Technical Health & Sustainability",
    QuestionCategory.CHANGE_READINESS: "Change Readiness & Migration Potential",
    QuestionCategory.DEPENDENCIES: "Dependencies & Integration",
    QuestionCategory.COST_AWARENESS: "Cost & Resource Awareness",
    QuestionCategory.FUTURE_NEEDS: "Future Needs & Strategic Alignment"
}

ASSESSMENT_QUESTIONS: List[Question] = [
    # Business Value & Criticality
    Question(
        question_id="BV01",
        category=QuestionCategory.BUSINESS_VALUE,
        text="How critical is this application to your daily business operations?",
        description="Consider the impact on business processes if this application were unavailable",
        question_type=QuestionType.SCALE,
        weight=1.2,
        order=1
    ),
    Question(
        question_id="BV02",
        category=QuestionCategory.BUSINESS_VALUE,
        text="What is the estimated revenue impact if this application is unavailable for 24 hours?",
        description="Consider direct revenue loss, productivity impact, and customer satisfaction",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=["No impact", "<$10K", "$10K-$100K", "$100K-$1M", ">$1M"],
        option_values={"No impact": 1, "<$10K": 3, "$10K-$100K": 5, "$100K-$1M": 8, ">$1M": 10},
        weight=1.3,
        order=2
    ),
    Question(
        question_id="BV03",
        category=QuestionCategory.BUSINESS_VALUE,
        text="How many business processes depend on this application?",
        description="1 = Single process, 10 = Enterprise-wide impact",
        question_type=QuestionType.SCALE,
        weight=1.0,
        order=3
    ),
    Question(
        question_id="BV04",
        category=QuestionCategory.BUSINESS_VALUE,
        text="Does this application provide competitive advantage?",
        description="Consider whether the application provides unique capabilities that differentiate your business",
        question_type=QuestionType.SCALE,
        weight=1.1,
        order=4
    ),
    Question(
        question_id="BV05",
        category=QuestionCategory.BUSINESS_VALUE,
        text="How well does this application support regulatory compliance requirements?",
        description="1 = Not applicable, 10 = Essential for compliance",
        question_type=QuestionType.SCALE,
        weight=1.2,
        order=5
    ),
    Question(
        question_id="BV06",
        category=QuestionCategory.BUSINESS_VALUE,
        text="Rate the business value delivered relative to the cost of maintaining this application",
        description="1 = Poor ROI, 10 = Excellent ROI",
        question_type=QuestionType.SCALE,
        weight=1.0,
        order=6
    ),

    # User Satisfaction & Experience
    Question(
        question_id="US01",
        category=QuestionCategory.USER_SATISFACTION,
        text="How satisfied are end users with this application's functionality?",
        description="Based on user feedback, surveys, or direct observation",
        question_type=QuestionType.SCALE,
        weight=1.2,
        order=1
    ),
    Question(
        question_id="US02",
        category=QuestionCategory.USER_SATISFACTION,
        text="How would you rate the application's ease of use?",
        description="1 = Very difficult, 10 = Very intuitive",
        question_type=QuestionType.SCALE,
        weight=1.0,
        order=2
    ),
    Question(
        question_id="US03",
        category=QuestionCategory.USER_SATISFACTION,
        text="How often do users report issues or complaints about this application?",
        description="Frequency of reported problems",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=["Daily", "Weekly", "Monthly", "Rarely", "Never"],
        option_values={"Daily": 1, "Weekly": 3, "Monthly": 6, "Rarely": 8, "Never": 10},
        weight=1.1,
        order=3
    ),
    Question(
        question_id="US04",
        category=QuestionCategory.USER_SATISFACTION,
        text="How well does the application meet users' current needs?",
        description="Consider functionality gaps and workarounds users must employ",
        question_type=QuestionType.SCALE,
        weight=1.2,
        order=4
    ),
    Question(
        question_id="US05",
        category=QuestionCategory.USER_SATISFACTION,
        text="Rate the quality of available training and documentation",
        description="1 = Non-existent, 10 = Excellent",
        question_type=QuestionType.SCALE,
        weight=0.8,
        order=5
    ),
    Question(
        question_id="US06",
        category=QuestionCategory.USER_SATISFACTION,
        text="How responsive is support when users encounter issues?",
        description="1 = Very slow, 10 = Immediate",
        question_type=QuestionType.SCALE,
        weight=1.0,
        order=6
    ),

    # Technical Health & Sustainability
    Question(
        question_id="TH01",
        category=QuestionCategory.TECHNICAL_HEALTH,
        text="How would you rate the overall technical condition of this application?",
        description="Consider architecture, code quality, and maintainability",
        question_type=QuestionType.SCALE,
        weight=1.3,
        order=1
    ),
    Question(
        question_id="TH02",
        category=QuestionCategory.TECHNICAL_HEALTH,
        text="How frequently does this application experience outages or performance issues?",
        description="Frequency of technical problems",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=["Daily", "Weekly", "Monthly", "Quarterly", "Rarely"],
        option_values={"Daily": 1, "Weekly": 3, "Monthly": 5, "Quarterly": 8, "Rarely": 10},
        weight=1.2,
        order=2
    ),
    Question(
        question_id="TH03",
        category=QuestionCategory.TECHNICAL_HEALTH,
        text="Is the underlying technology stack current and supported?",
        description="1 = End of life, 10 = Current/modern",
        question_type=QuestionType.SCALE,
        weight=1.1,
        order=3
    ),
    Question(
        question_id="TH04",
        category=QuestionCategory.TECHNICAL_HEALTH,
        text="How easy is it to find qualified resources to support this application?",
        description="Consider availability of developers, administrators, and consultants",
        question_type=QuestionType.SCALE,
        weight=1.0,
        order=4
    ),
    Question(
        question_id="TH05",
        category=QuestionCategory.TECHNICAL_HEALTH,
        text="Rate the quality and completeness of technical documentation",
        description="1 = Non-existent, 10 = Comprehensive",
        question_type=QuestionType.SCALE,
        weight=0.9,
        order=5
    ),
    Question(
        question_id="TH06",
        category=QuestionCategory.TECHNICAL_HEALTH,
        text="How well does the application integrate with security standards and protocols?",
        description="Consider vulnerabilities, compliance with security policies",
        question_type=QuestionType.SCALE,
        weight=1.2,
        order=6
    ),

    # Change Readiness & Migration Potential
    Question(
        question_id="CR01",
        category=QuestionCategory.CHANGE_READINESS,
        text="How modular and well-architected is this application for potential changes?",
        description="1 = Monolithic/rigid, 10 = Highly modular",
        question_type=QuestionType.SCALE,
        weight=1.1,
        order=1
    ),
    Question(
        question_id="CR02",
        category=QuestionCategory.CHANGE_READINESS,
        text="What is the estimated effort to migrate data from this application?",
        description="Consider data volume, complexity, and cleanliness",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=["Minimal", "Moderate", "Significant", "Major undertaking", "Unknown"],
        option_values={"Minimal": 9, "Moderate": 7, "Significant": 5, "Major undertaking": 3, "Unknown": 5},
        weight=1.0,
        order=2
    ),
    Question(
        question_id="CR03",
        category=QuestionCategory.CHANGE_READINESS,
        text="Are there viable alternative solutions available in the market?",
        description="1 = No alternatives, 10 = Many quality options",
        question_type=QuestionType.SCALE,
        weight=0.9,
        order=3
    ),
    Question(
        question_id="CR04",
        category=QuestionCategory.CHANGE_READINESS,
        text="How resistant would users be to transitioning to a new solution?",
        description="1 = Very resistant, 10 = Very receptive",
        question_type=QuestionType.SCALE,
        weight=1.1,
        order=4
    ),
    Question(
        question_id="CR05",
        category=QuestionCategory.CHANGE_READINESS,
        text="Is there executive sponsorship for modernizing this application?",
        description="Support from leadership for change initiatives",
        question_type=QuestionType.YES_NO,
        options=["Yes", "No", "Uncertain"],
        option_values={"Yes": 10, "No": 1, "Uncertain": 5},
        weight=1.2,
        order=5
    ),
    Question(
        question_id="CR06",
        category=QuestionCategory.CHANGE_READINESS,
        text="Rate the organization's capacity to manage change for this application",
        description="Consider available resources, expertise, and bandwidth",
        question_type=QuestionType.SCALE,
        weight=1.0,
        order=6
    ),

    # Dependencies & Integration
    Question(
        question_id="DI01",
        category=QuestionCategory.DEPENDENCIES,
        text="How many other applications depend on this application's data or services?",
        description="Count of downstream dependencies",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=["None", "1-3", "4-6", "7-10", ">10"],
        option_values={"None": 2, "1-3": 4, "4-6": 6, "7-10": 8, ">10": 10},
        weight=1.1,
        order=1
    ),
    Question(
        question_id="DI02",
        category=QuestionCategory.DEPENDENCIES,
        text="How critical are the upstream dependencies to this application's function?",
        description="1 = Not dependent, 10 = Completely dependent",
        question_type=QuestionType.SCALE,
        weight=1.0,
        order=2
    ),
    Question(
        question_id="DI03",
        category=QuestionCategory.DEPENDENCIES,
        text="Rate the complexity of integrations with other systems",
        description="1 = Simple, 10 = Highly complex",
        question_type=QuestionType.SCALE,
        weight=1.0,
        order=3
    ),
    Question(
        question_id="DI04",
        category=QuestionCategory.DEPENDENCIES,
        text="How well documented are the integration points and data flows?",
        description="1 = Undocumented, 10 = Fully documented",
        question_type=QuestionType.SCALE,
        weight=0.9,
        order=4
    ),
    Question(
        question_id="DI05",
        category=QuestionCategory.DEPENDENCIES,
        text="Are there any single points of failure in the integration architecture?",
        description="Presence of critical failure points",
        question_type=QuestionType.YES_NO,
        options=["Yes", "No", "Unknown"],
        option_values={"Yes": 2, "No": 10, "Unknown": 5},
        weight=1.1,
        order=5
    ),

    # Cost & Resource Awareness
    Question(
        question_id="CA01",
        category=QuestionCategory.COST_AWARENESS,
        text="How well do you understand the total cost of ownership for this application?",
        description="Include licensing, infrastructure, support, and personnel",
        question_type=QuestionType.SCALE,
        weight=1.0,
        order=1
    ),
    Question(
        question_id="CA02",
        category=QuestionCategory.COST_AWARENESS,
        text="What is the trend of operational costs for this application?",
        description="Direction of cost changes over time",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=["Decreasing", "Stable", "Slowly increasing", "Rapidly increasing", "Unknown"],
        option_values={"Decreasing": 9, "Stable": 7, "Slowly increasing": 5, "Rapidly increasing": 2, "Unknown": 5},
        weight=1.1,
        order=2
    ),
    Question(
        question_id="CA03",
        category=QuestionCategory.COST_AWARENESS,
        text="Are there hidden costs that are not typically accounted for?",
        description="Describe any costs that may not be captured in standard reporting",
        question_type=QuestionType.TEXT,
        weight=0.8,
        order=3,
        required=False
    ),
    Question(
        question_id="CA04",
        category=QuestionCategory.COST_AWARENESS,
        text="Rate the efficiency of resource utilization (servers, licenses, etc.)",
        description="1 = Very inefficient, 10 = Optimally utilized",
        question_type=QuestionType.SCALE,
        weight=1.0,
        order=4
    ),
    Question(
        question_id="CA05",
        category=QuestionCategory.COST_AWARENESS,
        text="How predictable are the costs associated with this application?",
        description="1 = Highly variable, 10 = Very predictable",
        question_type=QuestionType.SCALE,
        weight=0.9,
        order=5
    ),

    # Future Needs & Strategic Alignment
    Question(
        question_id="FN01",
        category=QuestionCategory.FUTURE_NEEDS,
        text="How well does this application align with the organization's strategic direction?",
        description="Consider digital transformation goals, business strategy",
        question_type=QuestionType.SCALE,
        weight=1.2,
        order=1
    ),
    Question(
        question_id="FN02",
        category=QuestionCategory.FUTURE_NEEDS,
        text="What new capabilities will the business need from this application in 2-3 years?",
        description="Describe anticipated future requirements",
        question_type=QuestionType.TEXT,
        weight=0.8,
        order=2,
        required=False
    ),
    Question(
        question_id="FN03",
        category=QuestionCategory.FUTURE_NEEDS,
        text="Is this application positioned to support expected business growth?",
        description="1 = Cannot scale, 10 = Highly scalable",
        question_type=QuestionType.SCALE,
        weight=1.1,
        order=3
    ),
    Question(
        question_id="FN04",
        category=QuestionCategory.FUTURE_NEEDS,
        text="Rate the likelihood of significant functionality changes in the next 12 months",
        description="Expected scope of changes",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=["None expected", "Minor changes", "Moderate changes", "Major changes", "Complete replacement"],
        option_values={"None expected": 2, "Minor changes": 4, "Moderate changes": 6, "Major changes": 8, "Complete replacement": 10},
        weight=1.0,
        order=4
    ),
    Question(
        question_id="FN05",
        category=QuestionCategory.FUTURE_NEEDS,
        text="How important is this application to digital transformation initiatives?",
        description="1 = Not relevant, 10 = Central to transformation",
        question_type=QuestionType.SCALE,
        weight=1.1,
        order=5
    ),
    Question(
        question_id="FN06",
        category=QuestionCategory.FUTURE_NEEDS,
        text="Does the current vendor/solution have a strong product roadmap?",
        description="1 = No roadmap/EOL, 10 = Strong innovation",
        question_type=QuestionType.SCALE,
        weight=1.0,
        order=6
    )
]


# ============================================================================
# SCORING ENGINE
# ============================================================================

class ScoringEngine:
    """Calculates scores for stakeholder assessments."""

    def __init__(self, category_weights: Dict[QuestionCategory, int] = None):
        self.category_weights = category_weights or CATEGORY_WEIGHTS
        self.questions_by_id = {q.question_id: q for q in ASSESSMENT_QUESTIONS}

    def normalize_response_value(self, response: Response, question: Question) -> float:
        """Normalize a response value to 0-10 scale."""
        if question.question_type == QuestionType.SCALE:
            return float(response.numeric_value) if response.numeric_value else 0.0

        elif question.question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.YES_NO]:
            if response.text_value and question.option_values:
                return float(question.option_values.get(response.text_value, 5))
            return 5.0  # Default middle value

        elif question.question_type == QuestionType.TEXT:
            # Text responses don't contribute to numeric score
            return 0.0

        return 0.0

    def apply_confidence_adjustment(self, response: Response, question: Question) -> float:
        """Adjust weight based on confidence level."""
        base_weight = question.weight
        if response.confidence_level and response.confidence_level <= 2:
            return base_weight * 0.5
        return base_weight

    def calculate_category_score(self, responses: List[Response],
                                  category: QuestionCategory) -> float:
        """Calculate score for a single category."""
        category_questions = [q for q in ASSESSMENT_QUESTIONS if q.category == category]
        category_question_ids = {q.question_id for q in category_questions}

        category_responses = [r for r in responses if r.question_id in category_question_ids]

        if not category_responses:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for response in category_responses:
            question = self.questions_by_id.get(response.question_id)
            if not question or question.question_type == QuestionType.TEXT:
                continue

            normalized_value = self.normalize_response_value(response, question)
            adjusted_weight = self.apply_confidence_adjustment(response, question)

            weighted_sum += normalized_value * adjusted_weight
            total_weight += adjusted_weight

        return (weighted_sum / total_weight) if total_weight > 0 else 0.0

    def calculate_overall_score(self, category_scores: Dict[QuestionCategory, float]) -> float:
        """Calculate overall weighted score from category scores."""
        weighted_sum = sum(
            category_scores.get(cat, 0.0) * self.category_weights.get(cat, 0)
            for cat in QuestionCategory
        )
        total_weight = sum(self.category_weights.values())
        return (weighted_sum / total_weight) if total_weight > 0 else 0.0

    def calculate_all_scores(self, responses: List[Response]) -> Dict[str, Any]:
        """Calculate all scores for an interview session."""
        category_scores = {}

        for category in QuestionCategory:
            score = self.calculate_category_score(responses, category)
            category_scores[category.value] = round(score, 2)

        # Convert to enum keys for overall calculation
        enum_scores = {QuestionCategory(k): v for k, v in category_scores.items()}
        overall_score = self.calculate_overall_score(enum_scores)

        return {
            'overall_score': round(overall_score, 2),
            'category_scores': category_scores
        }

    def get_score_rating(self, score: float) -> str:
        """Get rating label for a score."""
        if score >= 8.0:
            return "Excellent"
        elif score >= 6.0:
            return "Good"
        elif score >= 4.0:
            return "Fair"
        elif score >= 2.0:
            return "Poor"
        else:
            return "Critical"

    def analyze_strengths_weaknesses(self, category_scores: Dict[str, float]) -> Dict[str, List[str]]:
        """Identify strengths and weaknesses from category scores."""
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)

        strengths = []
        weaknesses = []

        for category_name, score in sorted_categories:
            category_display = CATEGORY_NAMES.get(
                QuestionCategory(category_name),
                category_name.replace('_', ' ').title()
            )

            if score >= 7.0:
                strengths.append(f"{category_display}: {score}/10")
            elif score < 5.0:
                weaknesses.append(f"{category_display}: {score}/10")

        return {
            'strengths': strengths[:3],  # Top 3 strengths
            'weaknesses': weaknesses[:3]  # Top 3 weaknesses
        }

    def generate_recommendations(self, category_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations based on scores."""
        recommendations = []

        score_thresholds = {
            'business_value': (4.0, "Review business alignment and consider retirement or replacement"),
            'user_satisfaction': (5.0, "Conduct user research and prioritize UX improvements"),
            'technical_health': (4.0, "Urgent technical debt remediation required"),
            'change_readiness': (5.0, "Develop change management and migration strategy"),
            'dependencies': (5.0, "Document integration points and reduce coupling"),
            'cost_awareness': (5.0, "Implement cost tracking and optimization measures"),
            'future_needs': (5.0, "Align with strategic roadmap or plan for replacement")
        }

        for category, (threshold, recommendation) in score_thresholds.items():
            if category_scores.get(category, 10) < threshold:
                recommendations.append(recommendation)

        if not recommendations:
            recommendations.append("Application is performing well across all categories")

        return recommendations


# ============================================================================
# DATA STORE (In-Memory for Demo, Replace with Database)
# ============================================================================

class StakeholderAssessmentStore:
    """In-memory data store for stakeholder assessment data."""

    def __init__(self):
        self.stakeholders: Dict[str, Stakeholder] = {}
        self.interviews: Dict[str, InterviewSession] = {}
        self.responses: Dict[str, Response] = {}
        self.scoring_engine = ScoringEngine()

    # Stakeholder CRUD
    def create_stakeholder(self, **kwargs) -> Stakeholder:
        stakeholder = Stakeholder.create(**kwargs)
        self.stakeholders[stakeholder.stakeholder_id] = stakeholder
        return stakeholder

    def get_stakeholder(self, stakeholder_id: str) -> Optional[Stakeholder]:
        return self.stakeholders.get(stakeholder_id)

    def get_all_stakeholders(self) -> List[Stakeholder]:
        return list(self.stakeholders.values())

    def update_stakeholder(self, stakeholder_id: str, **kwargs) -> Optional[Stakeholder]:
        stakeholder = self.stakeholders.get(stakeholder_id)
        if not stakeholder:
            return None

        for key, value in kwargs.items():
            if hasattr(stakeholder, key):
                setattr(stakeholder, key, value)

        stakeholder.updated_at = datetime.utcnow()
        return stakeholder

    def delete_stakeholder(self, stakeholder_id: str) -> bool:
        if stakeholder_id in self.stakeholders:
            del self.stakeholders[stakeholder_id]
            return True
        return False

    # Interview CRUD
    def create_interview(self, **kwargs) -> InterviewSession:
        interview = InterviewSession.create(**kwargs)
        self.interviews[interview.session_id] = interview
        return interview

    def get_interview(self, session_id: str) -> Optional[InterviewSession]:
        interview = self.interviews.get(session_id)
        if interview:
            interview.responses = [
                r for r in self.responses.values()
                if r.session_id == session_id
            ]
        return interview

    def get_all_interviews(self, status: str = None, application_id: str = None,
                          stakeholder_id: str = None) -> List[InterviewSession]:
        interviews = list(self.interviews.values())

        if status:
            interviews = [i for i in interviews if i.status.value == status]
        if application_id:
            interviews = [i for i in interviews if i.application_id == application_id]
        if stakeholder_id:
            interviews = [i for i in interviews if i.stakeholder_id == stakeholder_id]

        # Attach responses
        for interview in interviews:
            interview.responses = [
                r for r in self.responses.values()
                if r.session_id == interview.session_id
            ]

        return interviews

    def update_interview(self, session_id: str, **kwargs) -> Optional[InterviewSession]:
        interview = self.interviews.get(session_id)
        if not interview:
            return None

        for key, value in kwargs.items():
            if hasattr(interview, key):
                setattr(interview, key, value)

        interview.updated_at = datetime.utcnow()
        return interview

    def delete_interview(self, session_id: str) -> bool:
        if session_id in self.interviews:
            # Delete associated responses
            response_ids = [r.response_id for r in self.responses.values()
                          if r.session_id == session_id]
            for rid in response_ids:
                del self.responses[rid]

            del self.interviews[session_id]
            return True
        return False

    def start_interview(self, session_id: str) -> Optional[InterviewSession]:
        interview = self.interviews.get(session_id)
        if interview:
            interview.status = InterviewStatus.IN_PROGRESS
            interview.conducted_date = datetime.utcnow()
            interview.updated_at = datetime.utcnow()
        return interview

    def complete_interview(self, session_id: str) -> Optional[InterviewSession]:
        interview = self.get_interview(session_id)
        if not interview:
            return None

        # Calculate scores
        scores = self.scoring_engine.calculate_all_scores(interview.responses)
        interview.overall_score = scores['overall_score']
        interview.category_scores = scores['category_scores']
        interview.status = InterviewStatus.COMPLETED
        interview.updated_at = datetime.utcnow()

        return interview

    # Response CRUD
    def add_response(self, session_id: str, question_id: str, **kwargs) -> Response:
        # Check if response already exists
        existing = next(
            (r for r in self.responses.values()
             if r.session_id == session_id and r.question_id == question_id),
            None
        )

        if existing:
            # Update existing
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            return existing
        else:
            # Create new
            response = Response.create(session_id, question_id, **kwargs)
            self.responses[response.response_id] = response
            return response

    def get_interview_responses(self, session_id: str) -> List[Response]:
        return [r for r in self.responses.values() if r.session_id == session_id]

    # Analysis Methods
    def get_interview_analysis(self, session_id: str) -> Dict[str, Any]:
        interview = self.get_interview(session_id)
        if not interview:
            return {}

        scores = self.scoring_engine.calculate_all_scores(interview.responses)
        analysis = self.scoring_engine.analyze_strengths_weaknesses(scores['category_scores'])
        recommendations = self.scoring_engine.generate_recommendations(scores['category_scores'])

        return {
            'session_id': session_id,
            'application_id': interview.application_id,
            'overall_score': scores['overall_score'],
            'overall_rating': self.scoring_engine.get_score_rating(scores['overall_score']),
            'category_scores': scores['category_scores'],
            'strengths': analysis['strengths'],
            'weaknesses': analysis['weaknesses'],
            'recommendations': recommendations
        }

    def get_application_analysis(self, application_id: str) -> Dict[str, Any]:
        interviews = self.get_all_interviews(application_id=application_id)
        completed = [i for i in interviews if i.status == InterviewStatus.COMPLETED]

        if not completed:
            return {
                'application_id': application_id,
                'interviews_count': 0,
                'message': 'No completed interviews'
            }

        scores = [i.overall_score for i in completed if i.overall_score]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Aggregate category scores
        category_totals: Dict[str, List[float]] = {}
        for interview in completed:
            for cat, score in interview.category_scores.items():
                if cat not in category_totals:
                    category_totals[cat] = []
                category_totals[cat].append(score)

        category_averages = {
            cat: round(sum(scores) / len(scores), 2)
            for cat, scores in category_totals.items()
        }

        return {
            'application_id': application_id,
            'interviews_count': len(completed),
            'average_score': round(avg_score, 2),
            'latest_score': completed[-1].overall_score if completed else None,
            'category_averages': category_averages,
            'rating': self.scoring_engine.get_score_rating(avg_score)
        }

    def get_portfolio_analysis(self) -> Dict[str, Any]:
        all_interviews = self.get_all_interviews()
        completed = [i for i in all_interviews if i.status == InterviewStatus.COMPLETED]

        if not completed:
            return {
                'total_applications': 0,
                'total_interviews': 0,
                'message': 'No completed interviews'
            }

        # Group by application
        app_scores: Dict[str, List[float]] = {}
        for interview in completed:
            if interview.overall_score:
                if interview.application_id not in app_scores:
                    app_scores[interview.application_id] = []
                app_scores[interview.application_id].append(interview.overall_score)

        # Calculate averages per application
        app_averages = {
            app: sum(scores) / len(scores)
            for app, scores in app_scores.items()
        }

        sorted_apps = sorted(app_averages.items(), key=lambda x: x[1], reverse=True)

        return {
            'total_applications': len(app_averages),
            'total_interviews': len(completed),
            'average_portfolio_score': round(
                sum(app_averages.values()) / len(app_averages), 2
            ) if app_averages else 0,
            'top_performers': [
                {'application_id': app, 'score': round(score, 2)}
                for app, score in sorted_apps[:5]
            ],
            'at_risk': [
                {'application_id': app, 'score': round(score, 2)}
                for app, score in sorted_apps[-5:] if score < 5.0
            ]
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics for the dashboard."""
        all_interviews = list(self.interviews.values())

        return {
            'total_stakeholders': len(self.stakeholders),
            'total_interviews': len(all_interviews),
            'completed_interviews': len([i for i in all_interviews
                                        if i.status == InterviewStatus.COMPLETED]),
            'in_progress_interviews': len([i for i in all_interviews
                                          if i.status == InterviewStatus.IN_PROGRESS]),
            'scheduled_interviews': len([i for i in all_interviews
                                        if i.status == InterviewStatus.SCHEDULED]),
            'average_score': self._calculate_average_score(all_interviews)
        }

    def _calculate_average_score(self, interviews: List[InterviewSession]) -> float:
        completed = [i for i in interviews
                    if i.status == InterviewStatus.COMPLETED and i.overall_score]
        if not completed:
            return 0.0
        return round(sum(i.overall_score for i in completed) / len(completed), 2)


# Global store instance
assessment_store = StakeholderAssessmentStore()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_questions_by_category(category: QuestionCategory = None) -> List[Question]:
    """Get questions, optionally filtered by category."""
    if category:
        return [q for q in ASSESSMENT_QUESTIONS if q.category == category]
    return ASSESSMENT_QUESTIONS


def get_question_by_id(question_id: str) -> Optional[Question]:
    """Get a single question by ID."""
    for q in ASSESSMENT_QUESTIONS:
        if q.question_id == question_id:
            return q
    return None


def create_sample_data():
    """Create sample data for testing."""
    # Create stakeholders
    stakeholder1 = assessment_store.create_stakeholder(
        name="John Smith",
        email="john.smith@company.com",
        role="Business Analyst",
        department="Finance",
        stakeholder_type=StakeholderType.BUSINESS_OWNER,
        applications=["APP001", "APP002"]
    )

    stakeholder2 = assessment_store.create_stakeholder(
        name="Sarah Johnson",
        email="sarah.johnson@company.com",
        role="IT Manager",
        department="IT Operations",
        stakeholder_type=StakeholderType.TECHNICAL_LEAD,
        applications=["APP001", "APP003"]
    )

    # Create interview
    interview = assessment_store.create_interview(
        stakeholder_id=stakeholder1.stakeholder_id,
        application_id="APP001",
        scheduled_date=datetime.utcnow(),
        interviewer_id="interviewer001"
    )

    # Start interview
    assessment_store.start_interview(interview.session_id)

    # Add some responses
    sample_responses = [
        ("BV01", 8, None),
        ("BV02", None, "$100K-$1M"),
        ("BV03", 7, None),
        ("US01", 6, None),
        ("TH01", 5, None),
    ]

    for qid, numeric, text in sample_responses:
        assessment_store.add_response(
            session_id=interview.session_id,
            question_id=qid,
            numeric_value=numeric,
            text_value=text,
            confidence_level=4
        )

    return {
        'stakeholders': [stakeholder1, stakeholder2],
        'interview': interview
    }
