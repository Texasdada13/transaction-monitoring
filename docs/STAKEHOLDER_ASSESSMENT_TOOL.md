# Stakeholder Assessment Tool

## Technical Specification & Implementation Guide

**Version:** 1.0
**Last Updated:** November 2024
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Data Models](#data-models)
3. [Questionnaire Design](#questionnaire-design)
4. [Scoring Methodology](#scoring-methodology)
5. [UI Design Specifications](#ui-design-specifications)
6. [API Endpoint Definitions](#api-endpoint-definitions)
7. [Implementation Plan](#implementation-plan)
8. [Database Schema](#database-schema)

---

## Overview

### Purpose

The Stakeholder Assessment Tool is designed to systematically capture qualitative insights from key stakeholders about their applications within the portfolio. It complements quantitative application data by gathering subjective assessments of business value, user satisfaction, technical health, and strategic alignment.

### Key Features

- **Structured Interviews**: 35+ questions across 7 assessment categories
- **Weighted Scoring**: Configurable category weights for customized scoring
- **Multi-Stakeholder Support**: Track assessments from different perspectives
- **Progress Tracking**: Real-time interview progress and completion status
- **Analysis & Reporting**: Portfolio-wide and application-specific insights
- **Integration**: Seamless integration with existing application portfolio data

---

## Data Models

### Core Entities

#### Stakeholder

```python
@dataclass
class Stakeholder:
    stakeholder_id: str                    # Unique identifier (UUID)
    name: str                              # Full name
    email: str                             # Contact email
    role: str                              # Job title/role
    department: str                        # Department/business unit
    stakeholder_type: StakeholderType      # BUSINESS_OWNER, TECHNICAL_LEAD, END_USER, EXECUTIVE
    applications: List[str]                # List of application IDs they're associated with
    created_at: datetime                   # Record creation timestamp
    updated_at: datetime                   # Last update timestamp
    notes: Optional[str]                   # Additional notes
    phone: Optional[str]                   # Contact phone
    availability: Optional[str]            # Preferred interview times
```

#### Interview Session

```python
@dataclass
class InterviewSession:
    session_id: str                        # Unique identifier (UUID)
    stakeholder_id: str                    # FK to Stakeholder
    application_id: str                    # Application being assessed
    interviewer_id: str                    # Who conducted the interview
    scheduled_date: datetime               # When interview is scheduled
    conducted_date: Optional[datetime]     # When actually conducted
    status: InterviewStatus                # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    duration_minutes: Optional[int]        # Actual duration
    notes: Optional[str]                   # General interview notes
    created_at: datetime                   # Record creation timestamp
    updated_at: datetime                   # Last update timestamp
    completion_percentage: float           # 0-100 progress indicator
```

#### Question

```python
@dataclass
class Question:
    question_id: str                       # Unique identifier
    category: QuestionCategory             # Assessment category
    text: str                              # Question text
    description: Optional[str]             # Help text/context
    question_type: QuestionType            # SCALE, MULTIPLE_CHOICE, TEXT, YES_NO
    options: Optional[List[str]]           # For multiple choice questions
    weight: float                          # Importance weight (default 1.0)
    order: int                             # Display order within category
    required: bool                         # Is response required
    follow_up_trigger: Optional[str]       # Condition for follow-up questions
```

#### Response

```python
@dataclass
class Response:
    response_id: str                       # Unique identifier (UUID)
    session_id: str                        # FK to InterviewSession
    question_id: str                       # FK to Question
    numeric_value: Optional[int]           # For scale questions (1-10)
    text_value: Optional[str]              # For text/multiple choice
    confidence_level: Optional[int]        # How confident in answer (1-5)
    notes: Optional[str]                   # Additional context
    created_at: datetime                   # Record creation timestamp
    updated_at: datetime                   # Last update timestamp
```

### Enumerations

```python
class StakeholderType(Enum):
    BUSINESS_OWNER = "business_owner"
    TECHNICAL_LEAD = "technical_lead"
    END_USER = "end_user"
    EXECUTIVE = "executive"
    IT_OPERATIONS = "it_operations"
    COMPLIANCE = "compliance"

class InterviewStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"

class QuestionCategory(Enum):
    BUSINESS_VALUE = "business_value"
    USER_SATISFACTION = "user_satisfaction"
    TECHNICAL_HEALTH = "technical_health"
    CHANGE_READINESS = "change_readiness"
    DEPENDENCIES = "dependencies"
    COST_AWARENESS = "cost_awareness"
    FUTURE_NEEDS = "future_needs"

class QuestionType(Enum):
    SCALE = "scale"                        # 1-10 numeric scale
    MULTIPLE_CHOICE = "multiple_choice"    # Select from options
    TEXT = "text"                          # Free-form text
    YES_NO = "yes_no"                      # Boolean
    RANKING = "ranking"                    # Order items by preference
```

---

## Questionnaire Design

### Category 1: Business Value & Criticality

**Weight: 20%**

| ID | Question | Type | Scale/Options |
|----|----------|------|---------------|
| BV01 | How critical is this application to your daily business operations? | Scale | 1 (Not critical) - 10 (Mission critical) |
| BV02 | What is the estimated revenue impact if this application is unavailable for 24 hours? | Multiple Choice | No impact / <$10K / $10K-$100K / $100K-$1M / >$1M |
| BV03 | How many business processes depend on this application? | Scale | 1 (Single process) - 10 (Enterprise-wide) |
| BV04 | Does this application provide competitive advantage? | Scale | 1 (Commodity) - 10 (Strategic differentiator) |
| BV05 | How well does this application support regulatory compliance requirements? | Scale | 1 (Not applicable) - 10 (Essential for compliance) |
| BV06 | Rate the business value delivered relative to the cost of maintaining this application | Scale | 1 (Poor ROI) - 10 (Excellent ROI) |

### Category 2: User Satisfaction & Experience

**Weight: 15%**

| ID | Question | Type | Scale/Options |
|----|----------|------|---------------|
| US01 | How satisfied are end users with this application's functionality? | Scale | 1 (Very dissatisfied) - 10 (Very satisfied) |
| US02 | How would you rate the application's ease of use? | Scale | 1 (Very difficult) - 10 (Very intuitive) |
| US03 | How often do users report issues or complaints about this application? | Multiple Choice | Daily / Weekly / Monthly / Rarely / Never |
| US04 | How well does the application meet users' current needs? | Scale | 1 (Poorly) - 10 (Completely) |
| US05 | Rate the quality of available training and documentation | Scale | 1 (Non-existent) - 10 (Excellent) |
| US06 | How responsive is support when users encounter issues? | Scale | 1 (Very slow) - 10 (Immediate) |

### Category 3: Technical Health & Sustainability

**Weight: 20%**

| ID | Question | Type | Scale/Options |
|----|----------|------|---------------|
| TH01 | How would you rate the overall technical condition of this application? | Scale | 1 (Critical issues) - 10 (Excellent health) |
| TH02 | How frequently does this application experience outages or performance issues? | Multiple Choice | Daily / Weekly / Monthly / Quarterly / Rarely |
| TH03 | Is the underlying technology stack current and supported? | Scale | 1 (End of life) - 10 (Current/modern) |
| TH04 | How easy is it to find qualified resources to support this application? | Scale | 1 (Nearly impossible) - 10 (Readily available) |
| TH05 | Rate the quality and completeness of technical documentation | Scale | 1 (Non-existent) - 10 (Comprehensive) |
| TH06 | How well does the application integrate with security standards and protocols? | Scale | 1 (Major vulnerabilities) - 10 (Fully compliant) |

### Category 4: Change Readiness & Migration Potential

**Weight: 15%**

| ID | Question | Type | Scale/Options |
|----|----------|------|---------------|
| CR01 | How modular and well-architected is this application for potential changes? | Scale | 1 (Monolithic/rigid) - 10 (Highly modular) |
| CR02 | What is the estimated effort to migrate data from this application? | Multiple Choice | Minimal / Moderate / Significant / Major undertaking / Unknown |
| CR03 | Are there viable alternative solutions available in the market? | Scale | 1 (No alternatives) - 10 (Many quality options) |
| CR04 | How resistant would users be to transitioning to a new solution? | Scale | 1 (Very resistant) - 10 (Very receptive) |
| CR05 | Is there executive sponsorship for modernizing this application? | Yes/No | Yes / No / Uncertain |
| CR06 | Rate the organization's capacity to manage change for this application | Scale | 1 (No capacity) - 10 (Well-prepared) |

### Category 5: Dependencies & Integration

**Weight: 10%**

| ID | Question | Type | Scale/Options |
|----|----------|------|---------------|
| DI01 | How many other applications depend on this application's data or services? | Multiple Choice | None / 1-3 / 4-6 / 7-10 / >10 |
| DI02 | How critical are the upstream dependencies to this application's function? | Scale | 1 (Not dependent) - 10 (Completely dependent) |
| DI03 | Rate the complexity of integrations with other systems | Scale | 1 (Simple) - 10 (Highly complex) |
| DI04 | How well documented are the integration points and data flows? | Scale | 1 (Undocumented) - 10 (Fully documented) |
| DI05 | Are there any single points of failure in the integration architecture? | Yes/No | Yes / No / Unknown |

### Category 6: Cost & Resource Awareness

**Weight: 10%**

| ID | Question | Type | Scale/Options |
|----|----------|------|---------------|
| CA01 | How well do you understand the total cost of ownership for this application? | Scale | 1 (Not at all) - 10 (Complete visibility) |
| CA02 | What is the trend of operational costs for this application? | Multiple Choice | Decreasing / Stable / Slowly increasing / Rapidly increasing / Unknown |
| CA03 | Are there hidden costs that are not typically accounted for? | Text | Free response |
| CA04 | Rate the efficiency of resource utilization (servers, licenses, etc.) | Scale | 1 (Very inefficient) - 10 (Optimally utilized) |
| CA05 | How predictable are the costs associated with this application? | Scale | 1 (Highly variable) - 10 (Very predictable) |

### Category 7: Future Needs & Strategic Alignment

**Weight: 10%**

| ID | Question | Type | Scale/Options |
|----|----------|------|---------------|
| FN01 | How well does this application align with the organization's strategic direction? | Scale | 1 (Misaligned) - 10 (Perfectly aligned) |
| FN02 | What new capabilities will the business need from this application in 2-3 years? | Text | Free response |
| FN03 | Is this application positioned to support expected business growth? | Scale | 1 (Cannot scale) - 10 (Highly scalable) |
| FN04 | Rate the likelihood of significant functionality changes in the next 12 months | Multiple Choice | None expected / Minor changes / Moderate changes / Major changes / Complete replacement |
| FN05 | How important is this application to digital transformation initiatives? | Scale | 1 (Not relevant) - 10 (Central to transformation) |
| FN06 | Does the current vendor/solution have a strong product roadmap? | Scale | 1 (No roadmap/EOL) - 10 (Strong innovation) |

---

## Scoring Methodology

### Category Weights

| Category | Default Weight | Configurable Range |
|----------|---------------|-------------------|
| Business Value & Criticality | 20% | 10-30% |
| User Satisfaction & Experience | 15% | 5-25% |
| Technical Health & Sustainability | 20% | 10-30% |
| Change Readiness & Migration Potential | 15% | 5-25% |
| Dependencies & Integration | 10% | 5-20% |
| Cost & Resource Awareness | 10% | 5-20% |
| Future Needs & Strategic Alignment | 10% | 5-20% |

### Score Calculation

#### Question Score Normalization

All responses are normalized to a 0-10 scale:

- **Scale questions (1-10)**: Direct value
- **Yes/No questions**: Yes = 10, No = 0, Uncertain = 5
- **Multiple Choice**: Mapped to scale values (configured per question)

#### Category Score

```python
def calculate_category_score(responses: List[Response], category: QuestionCategory) -> float:
    category_responses = [r for r in responses if r.question.category == category]

    if not category_responses:
        return 0.0

    weighted_sum = sum(r.normalized_value * r.question.weight for r in category_responses)
    total_weight = sum(r.question.weight for r in category_responses)

    return (weighted_sum / total_weight) if total_weight > 0 else 0.0
```

#### Overall Score

```python
def calculate_overall_score(category_scores: Dict[str, float], weights: Dict[str, float]) -> float:
    weighted_sum = sum(
        category_scores[cat] * weights[cat]
        for cat in category_scores
    )
    return weighted_sum / 100  # Normalize to 0-10 scale
```

### Score Interpretation

| Score Range | Rating | Description |
|-------------|--------|-------------|
| 8.0 - 10.0 | Excellent | High-performing, strategic asset |
| 6.0 - 7.9 | Good | Meeting expectations, minor improvements needed |
| 4.0 - 5.9 | Fair | Significant gaps, requires attention |
| 2.0 - 3.9 | Poor | Critical issues, immediate action required |
| 0.0 - 1.9 | Critical | Severe problems, consider replacement |

### Confidence Adjustment

Responses with low confidence (1-2) are weighted at 50% of their normal weight:

```python
def apply_confidence_adjustment(response: Response) -> float:
    if response.confidence_level and response.confidence_level <= 2:
        return response.question.weight * 0.5
    return response.question.weight
```

---

## UI Design Specifications

### Dashboard View

#### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  STAKEHOLDER ASSESSMENT                                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Total   │  │ Complete│  │ In      │  │ Avg     │        │
│  │ 24      │  │ 18      │  │ Progress│  │ Score   │        │
│  │Interviews│ │ (75%)   │  │ 4       │  │ 7.2     │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
├─────────────────────────────────────────────────────────────┤
│  [Interviews] [Stakeholders] [Analysis] [Settings]          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tab Content Area                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Tab: Interviews

#### Interview List View

- Sortable table with columns: Application, Stakeholder, Status, Date, Score, Actions
- Filter by: Status, Application, Stakeholder, Date Range
- Actions: View, Edit, Delete, Export
- Quick-add button for new interviews

#### Interview Conduct Interface

```
┌─────────────────────────────────────────────────────────────┐
│  Interview: [App Name] with [Stakeholder]                   │
│  Progress: ████████████░░░░░░░░ 60% (21/35 questions)       │
├─────────────────────────────────────────────────────────────┤
│  Category: Business Value & Criticality (4/6)               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Q4: Does this application provide competitive advantage?   │
│  ─────────────────────────────────────────────────────────  │
│  Help: Consider whether the application provides unique     │
│  capabilities that differentiate your business              │
│                                                             │
│  ○ 1 ○ 2 ○ 3 ○ 4 ○ 5 ○ 6 ○ 7 ● 8 ○ 9 ○ 10                  │
│  [Commodity]                    [Strategic Differentiator]  │
│                                                             │
│  Confidence: ○ 1 ○ 2 ● 3 ○ 4 ○ 5                           │
│  [Low]                                             [High]   │
│                                                             │
│  Notes: ________________________________________________   │
│         ________________________________________________   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  [← Previous]                    [Save & Continue →]        │
│                                                             │
│  [Save Draft]  [Skip Question]  [Complete Interview]        │
└─────────────────────────────────────────────────────────────┘
```

### Tab: Stakeholders

#### Stakeholder List View

- Card or table view toggle
- Search by name, email, department
- Filter by type, associated applications
- Actions: View Profile, Schedule Interview, Edit, Delete

#### Stakeholder Modal (Add/Edit)

```
┌─────────────────────────────────────────────────────────────┐
│  Add New Stakeholder                              [X]       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Name:        [________________________________]            │
│  Email:       [________________________________]            │
│  Phone:       [________________________________]            │
│  Role:        [________________________________]            │
│  Department:  [________________________________]            │
│                                                             │
│  Stakeholder Type:                                          │
│  [▼ Business Owner                              ]           │
│                                                             │
│  Associated Applications:                                   │
│  [✓] App A    [✓] App B    [ ] App C    [ ] App D          │
│                                                             │
│  Availability Notes:                                        │
│  [________________________________________________]        │
│  [________________________________________________]        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                              [Cancel]  [Save Stakeholder]   │
└─────────────────────────────────────────────────────────────┘
```

### Tab: Analysis

#### Analysis Dashboard Components

1. **Score Distribution Chart**
   - Box plot or histogram showing score distribution across applications
   - Color-coded by rating tier

2. **Category Comparison Radar**
   - Radar/spider chart comparing categories for selected application(s)
   - Overlay multiple applications for comparison

3. **Trend Analysis**
   - Line chart showing score changes over time
   - By application or portfolio-wide

4. **Heat Map**
   - Applications vs Categories matrix
   - Color intensity indicates score

5. **Gap Analysis**
   - Bar chart showing gap between current and target scores
   - Prioritized by impact

### Color Scheme (aligned with existing theme)

```css
/* Score Ratings */
--score-excellent: #28a745;    /* Green */
--score-good: #17a2b8;         /* Teal */
--score-fair: #ffc107;         /* Yellow */
--score-poor: #fd7e14;         /* Orange */
--score-critical: #dc3545;     /* Red */

/* UI Elements */
--primary: #0A5CAD;            /* Medium Blue */
--secondary: #002B5B;          /* Dark Blue */
--accent: #7C3AED;             /* Purple */
--background: #f8f9fa;
--text: #333333;
```

---

## API Endpoint Definitions

### Base URL

```
/api/v1/stakeholder-assessment
```

### Stakeholder Management

#### List Stakeholders
```
GET /stakeholders
Query params: page, limit, search, type, application_id
Response: { stakeholders: [], total: int, page: int, pages: int }
```

#### Get Stakeholder
```
GET /stakeholders/{stakeholder_id}
Response: Stakeholder object with interview history
```

#### Create Stakeholder
```
POST /stakeholders
Body: { name, email, role, department, stakeholder_type, applications, ... }
Response: Created Stakeholder object
```

#### Update Stakeholder
```
PUT /stakeholders/{stakeholder_id}
Body: Partial Stakeholder object
Response: Updated Stakeholder object
```

#### Delete Stakeholder
```
DELETE /stakeholders/{stakeholder_id}
Response: { success: true, message: string }
```

### Interview Management

#### List Interviews
```
GET /interviews
Query params: page, limit, status, stakeholder_id, application_id, date_from, date_to
Response: { interviews: [], total: int, page: int, pages: int }
```

#### Get Interview
```
GET /interviews/{session_id}
Response: InterviewSession with responses
```

#### Create Interview
```
POST /interviews
Body: { stakeholder_id, application_id, scheduled_date, interviewer_id }
Response: Created InterviewSession object
```

#### Update Interview
```
PUT /interviews/{session_id}
Body: Partial InterviewSession object
Response: Updated InterviewSession object
```

#### Delete Interview
```
DELETE /interviews/{session_id}
Response: { success: true, message: string }
```

#### Start Interview
```
POST /interviews/{session_id}/start
Response: InterviewSession with status = IN_PROGRESS
```

#### Complete Interview
```
POST /interviews/{session_id}/complete
Response: InterviewSession with calculated scores
```

### Response Management

#### Get Interview Responses
```
GET /interviews/{session_id}/responses
Response: { responses: [], completion_percentage: float }
```

#### Submit Response
```
POST /interviews/{session_id}/responses
Body: { question_id, numeric_value?, text_value?, confidence_level?, notes? }
Response: Created Response object
```

#### Update Response
```
PUT /interviews/{session_id}/responses/{response_id}
Body: Partial Response object
Response: Updated Response object
```

#### Batch Submit Responses
```
POST /interviews/{session_id}/responses/batch
Body: { responses: [{ question_id, value, confidence, notes }, ...] }
Response: { success: int, failed: int, errors: [] }
```

### Questions

#### Get All Questions
```
GET /questions
Query params: category
Response: { questions: [] }
```

#### Get Questions by Category
```
GET /questions/category/{category}
Response: { questions: [], category_info: {} }
```

### Analysis Endpoints

#### Interview Analysis
```
GET /analysis/interview/{session_id}
Response: {
  overall_score: float,
  category_scores: { category: score },
  strengths: [],
  weaknesses: [],
  recommendations: []
}
```

#### Application Analysis
```
GET /analysis/application/{application_id}
Query params: include_history (bool)
Response: {
  application_id: string,
  interviews_count: int,
  average_score: float,
  latest_score: float,
  category_scores: {},
  score_trend: [],
  stakeholder_perspectives: []
}
```

#### Portfolio Analysis
```
GET /analysis/portfolio
Query params: application_ids (optional list)
Response: {
  total_applications: int,
  total_interviews: int,
  average_portfolio_score: float,
  score_distribution: {},
  category_averages: {},
  top_performers: [],
  at_risk: [],
  recommendations: []
}
```

#### Comparison Analysis
```
POST /analysis/compare
Body: { application_ids: [], metrics: [] }
Response: {
  applications: [{ id, scores }],
  comparison_matrix: []
}
```

### Export

#### Export Interview
```
GET /export/interview/{session_id}
Query params: format (pdf, csv, json)
Response: File download
```

#### Export Analysis
```
GET /export/analysis/{application_id}
Query params: format (pdf, xlsx)
Response: File download
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

#### Database Schema
- [ ] Create migration for stakeholder tables
- [ ] Define SQLAlchemy models
- [ ] Seed question data
- [ ] Create indexes for performance

#### Core Backend
- [ ] Implement dataclass models
- [ ] Create repository layer for CRUD operations
- [ ] Build scoring engine
- [ ] Unit tests for core logic

### Phase 2: API Development (Week 2-3)

#### Endpoints
- [ ] Stakeholder CRUD endpoints
- [ ] Interview management endpoints
- [ ] Response capture endpoints
- [ ] Analysis endpoints
- [ ] Export endpoints

#### Integration
- [ ] Authentication integration
- [ ] Input validation
- [ ] Error handling
- [ ] API documentation (OpenAPI)

### Phase 3: Frontend Development (Week 3-4)

#### Dashboard
- [ ] Main dashboard layout
- [ ] Statistics cards
- [ ] Tab navigation

#### Interview Module
- [ ] Interview list view
- [ ] Interview conduct interface
- [ ] Progress tracking
- [ ] Auto-save functionality

#### Stakeholder Module
- [ ] Stakeholder list/table
- [ ] Add/Edit modal
- [ ] Profile view with history

#### Analysis Module
- [ ] Score distribution chart
- [ ] Category radar chart
- [ ] Trend analysis
- [ ] Heat map visualization
- [ ] Export functionality

### Phase 4: Testing & Refinement (Week 4-5)

- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] UX refinement
- [ ] Documentation completion
- [ ] User acceptance testing

### Phase 5: Deployment (Week 5)

- [ ] Production deployment
- [ ] Monitoring setup
- [ ] User training materials
- [ ] Support documentation

---

## Database Schema

### Table: stakeholders

```sql
CREATE TABLE stakeholders (
    stakeholder_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(50),
    role VARCHAR(255),
    department VARCHAR(255),
    stakeholder_type VARCHAR(50) NOT NULL,
    applications JSON,
    availability TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_stakeholder_email (email),
    INDEX idx_stakeholder_type (stakeholder_type),
    INDEX idx_stakeholder_department (department)
);
```

### Table: interview_sessions

```sql
CREATE TABLE interview_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    stakeholder_id VARCHAR(36) NOT NULL,
    application_id VARCHAR(36) NOT NULL,
    interviewer_id VARCHAR(36),
    scheduled_date TIMESTAMP,
    conducted_date TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled',
    duration_minutes INT,
    notes TEXT,
    overall_score DECIMAL(4,2),
    category_scores JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(stakeholder_id) ON DELETE CASCADE,
    INDEX idx_interview_stakeholder (stakeholder_id),
    INDEX idx_interview_application (application_id),
    INDEX idx_interview_status (status),
    INDEX idx_interview_date (scheduled_date)
);
```

### Table: interview_responses

```sql
CREATE TABLE interview_responses (
    response_id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    question_id VARCHAR(20) NOT NULL,
    numeric_value INT,
    text_value TEXT,
    confidence_level INT DEFAULT 3,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (session_id) REFERENCES interview_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_response_session (session_id),
    INDEX idx_response_question (question_id),
    UNIQUE KEY unique_session_question (session_id, question_id)
);
```

### Table: assessment_questions (Static/Reference)

```sql
CREATE TABLE assessment_questions (
    question_id VARCHAR(20) PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    question_text TEXT NOT NULL,
    description TEXT,
    question_type VARCHAR(50) NOT NULL,
    options JSON,
    weight DECIMAL(3,2) DEFAULT 1.00,
    display_order INT,
    required BOOLEAN DEFAULT TRUE,
    active BOOLEAN DEFAULT TRUE,

    INDEX idx_question_category (category),
    INDEX idx_question_order (display_order)
);
```

---

## Security Considerations

### Access Control

- All endpoints require authentication
- Role-based access:
  - **Analyst**: Can view stakeholders and interviews they created
  - **Manager**: Full access to all stakeholder assessment features
- Audit logging for all modifications

### Data Protection

- PII (emails, phones) encrypted at rest
- Interview responses anonymization option for reporting
- Export permissions controlled by role

### Input Validation

- All inputs sanitized and validated
- SQL injection prevention via parameterized queries
- XSS prevention in text responses

---

## Appendix

### Multiple Choice Value Mappings

| Question | Options and Values |
|----------|--------------------|
| BV02 (Revenue Impact) | No impact=1, <$10K=3, $10K-$100K=5, $100K-$1M=8, >$1M=10 |
| US03 (Issue Frequency) | Never=10, Rarely=8, Monthly=6, Weekly=3, Daily=1 |
| TH02 (Outage Frequency) | Rarely=10, Quarterly=8, Monthly=5, Weekly=3, Daily=1 |
| CR02 (Migration Effort) | Minimal=9, Moderate=7, Significant=5, Major=3, Unknown=5 |
| DI01 (Downstream Deps) | None=2, 1-3=4, 4-6=6, 7-10=8, >10=10 |
| CA02 (Cost Trend) | Decreasing=9, Stable=7, Slow increase=5, Rapid increase=2, Unknown=5 |
| FN04 (Change Likelihood) | None=2, Minor=4, Moderate=6, Major=8, Replacement=10 |

### Integration with Existing Modules

The Stakeholder Assessment Tool integrates with:

1. **Application Portfolio**: Links to application metadata
2. **User Management**: Interviewer identification
3. **Reporting Engine**: Export and visualization
4. **Notification System**: Interview reminders and alerts

---

*Document maintained by: Architecture Team*
*For questions: architecture@company.com*
