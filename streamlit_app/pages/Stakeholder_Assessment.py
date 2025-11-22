"""
Stakeholder Assessment Page

Provides UI for conducting stakeholder interviews, managing stakeholders,
and analyzing assessment results.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

from streamlit_app.theme import apply_master_theme
from streamlit_app.explainability import init_tooltip_toggle
from streamlit_app.components.chart_with_tooltip import chart_with_explanation, metric_with_explanation

# Import the assessment engine
from app.services.stakeholder_assessment import (
    assessment_store,
    StakeholderType,
    InterviewStatus,
    QuestionCategory,
    ASSESSMENT_QUESTIONS,
    CATEGORY_NAMES,
    CATEGORY_WEIGHTS,
    get_questions_by_category,
    create_sample_data
)


def render():
    """Main render function for Stakeholder Assessment page."""
    apply_master_theme()
    init_tooltip_toggle()

    st.markdown("# Stakeholder Assessment Tool")
    st.markdown("Conduct structured interviews to gather qualitative insights about applications")

    # Initialize sample data if empty
    if not assessment_store.stakeholders:
        create_sample_data()

    # Get statistics
    stats = assessment_store.get_statistics()

    # Dashboard metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_with_explanation(
            label="Total Interviews",
            value=stats['total_interviews'],
            delta=None,
            title="Total Interviews",
            what_it_shows="Count of all interview sessions",
            why_it_matters="Indicates assessment coverage across the portfolio"
        )

    with col2:
        completed_pct = (stats['completed_interviews'] / stats['total_interviews'] * 100) if stats['total_interviews'] > 0 else 0
        metric_with_explanation(
            label="Completed",
            value=f"{stats['completed_interviews']} ({completed_pct:.0f}%)",
            delta=None,
            title="Completed Interviews",
            what_it_shows="Number and percentage of completed interviews",
            why_it_matters="Shows progress toward assessment goals"
        )

    with col3:
        metric_with_explanation(
            label="In Progress",
            value=stats['in_progress_interviews'],
            delta=None,
            title="In Progress",
            what_it_shows="Interviews currently being conducted",
            why_it_matters="Indicates active assessment work"
        )

    with col4:
        metric_with_explanation(
            label="Avg Score",
            value=f"{stats['average_score']:.1f}/10" if stats['average_score'] > 0 else "N/A",
            delta=None,
            title="Average Score",
            what_it_shows="Mean score across completed interviews",
            why_it_matters="Overall portfolio health indicator"
        )

    st.markdown("---")

    # Tab navigation
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Interviews", "👥 Stakeholders", "📊 Analysis", "⚙️ Settings"])

    with tab1:
        render_interviews_tab()

    with tab2:
        render_stakeholders_tab()

    with tab3:
        render_analysis_tab()

    with tab4:
        render_settings_tab()


def render_interviews_tab():
    """Render the interviews management tab."""
    st.subheader("Interview Sessions")

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("➕ New Interview", key="new_interview_btn"):
            st.session_state.show_new_interview_modal = True

    with col2:
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Scheduled", "In Progress", "Completed", "Cancelled"],
            key="interview_status_filter"
        )

    # Get interviews
    status_map = {
        "All": None,
        "Scheduled": "scheduled",
        "In Progress": "in_progress",
        "Completed": "completed",
        "Cancelled": "cancelled"
    }
    interviews = assessment_store.get_all_interviews(status=status_map.get(status_filter))

    if not interviews:
        st.info("No interviews found. Click 'New Interview' to schedule one.")
    else:
        # Display interviews as cards
        for interview in sorted(interviews, key=lambda x: x.created_at, reverse=True):
            stakeholder = assessment_store.get_stakeholder(interview.stakeholder_id)
            stakeholder_name = stakeholder.name if stakeholder else "Unknown"

            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

                with col1:
                    st.markdown(f"**{interview.application_id}**")
                    st.caption(f"Stakeholder: {stakeholder_name}")

                with col2:
                    status_colors = {
                        InterviewStatus.SCHEDULED: "🔵",
                        InterviewStatus.IN_PROGRESS: "🟡",
                        InterviewStatus.COMPLETED: "🟢",
                        InterviewStatus.CANCELLED: "🔴"
                    }
                    st.markdown(f"{status_colors.get(interview.status, '⚪')} {interview.status.value.replace('_', ' ').title()}")
                    if interview.scheduled_date:
                        st.caption(interview.scheduled_date.strftime("%Y-%m-%d"))

                with col3:
                    st.markdown(f"**{interview.completion_percentage:.0f}%** complete")
                    if interview.overall_score:
                        st.caption(f"Score: {interview.overall_score:.1f}/10")

                with col4:
                    if interview.status == InterviewStatus.SCHEDULED:
                        if st.button("▶️ Start", key=f"start_{interview.session_id}"):
                            assessment_store.start_interview(interview.session_id)
                            st.rerun()
                    elif interview.status == InterviewStatus.IN_PROGRESS:
                        if st.button("📝 Continue", key=f"continue_{interview.session_id}"):
                            st.session_state.active_interview = interview.session_id
                            st.rerun()
                    elif interview.status == InterviewStatus.COMPLETED:
                        if st.button("📊 Results", key=f"results_{interview.session_id}"):
                            st.session_state.view_results = interview.session_id
                            st.rerun()

                st.markdown("---")

    # New Interview Modal
    if st.session_state.get('show_new_interview_modal', False):
        render_new_interview_modal()

    # Active Interview Conduct
    if st.session_state.get('active_interview'):
        render_interview_conduct(st.session_state.active_interview)

    # View Results Modal
    if st.session_state.get('view_results'):
        render_interview_results(st.session_state.view_results)


def render_new_interview_modal():
    """Render modal for creating a new interview."""
    st.markdown("### Schedule New Interview")

    with st.form("new_interview_form"):
        stakeholders = assessment_store.get_all_stakeholders()
        stakeholder_options = {s.name: s.stakeholder_id for s in stakeholders}

        if not stakeholders:
            st.warning("No stakeholders found. Please add a stakeholder first.")
            if st.form_submit_button("Close"):
                st.session_state.show_new_interview_modal = False
                st.rerun()
            return

        selected_stakeholder = st.selectbox(
            "Select Stakeholder",
            options=list(stakeholder_options.keys())
        )

        application_id = st.text_input("Application ID", placeholder="e.g., APP001")

        scheduled_date = st.date_input("Scheduled Date", value=datetime.now().date())
        scheduled_time = st.time_input("Scheduled Time", value=datetime.now().time())

        notes = st.text_area("Notes", placeholder="Optional notes about this interview...")

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Schedule Interview"):
                if application_id:
                    scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)
                    interview = assessment_store.create_interview(
                        stakeholder_id=stakeholder_options[selected_stakeholder],
                        application_id=application_id,
                        scheduled_date=scheduled_datetime,
                        notes=notes
                    )
                    st.success(f"Interview scheduled successfully!")
                    st.session_state.show_new_interview_modal = False
                    st.rerun()
                else:
                    st.error("Please enter an Application ID")

        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state.show_new_interview_modal = False
                st.rerun()


def render_interview_conduct(session_id: str):
    """Render the interview conduct interface."""
    interview = assessment_store.get_interview(session_id)
    if not interview:
        st.error("Interview not found")
        return

    stakeholder = assessment_store.get_stakeholder(interview.stakeholder_id)

    st.markdown("### Conduct Interview")
    st.markdown(f"**Application:** {interview.application_id} | **Stakeholder:** {stakeholder.name if stakeholder else 'Unknown'}")

    # Progress bar
    progress = interview.completion_percentage / 100
    st.progress(progress)
    st.caption(f"{interview.completion_percentage:.0f}% Complete ({len(interview.responses)}/{len(ASSESSMENT_QUESTIONS)} questions)")

    # Category selector
    categories = list(QuestionCategory)
    category_names = [CATEGORY_NAMES.get(c, c.value) for c in categories]

    selected_category_idx = st.selectbox(
        "Select Category",
        range(len(categories)),
        format_func=lambda x: category_names[x]
    )
    selected_category = categories[selected_category_idx]

    # Get questions for this category
    questions = get_questions_by_category(selected_category)

    # Get existing responses
    existing_responses = {r.question_id: r for r in interview.responses}

    st.markdown(f"#### {CATEGORY_NAMES.get(selected_category, selected_category.value)}")
    st.caption(f"Weight: {CATEGORY_WEIGHTS.get(selected_category, 10)}%")

    # Question form
    with st.form(f"questions_form_{selected_category.value}"):
        responses_to_save = []

        for q in questions:
            st.markdown(f"**{q.question_id}: {q.text}**")
            if q.description:
                st.caption(q.description)

            existing = existing_responses.get(q.question_id)

            if q.question_type.value == "scale":
                value = st.slider(
                    "Score",
                    min_value=1,
                    max_value=10,
                    value=existing.numeric_value if existing and existing.numeric_value else 5,
                    key=f"q_{q.question_id}"
                )
                responses_to_save.append({
                    'question_id': q.question_id,
                    'numeric_value': value
                })

            elif q.question_type.value in ["multiple_choice", "yes_no"]:
                options = q.options or ["Yes", "No"]
                current_value = existing.text_value if existing else options[0]
                if current_value not in options:
                    current_value = options[0]

                value = st.selectbox(
                    "Select option",
                    options,
                    index=options.index(current_value) if current_value in options else 0,
                    key=f"q_{q.question_id}"
                )
                responses_to_save.append({
                    'question_id': q.question_id,
                    'text_value': value
                })

            elif q.question_type.value == "text":
                value = st.text_area(
                    "Response",
                    value=existing.text_value if existing else "",
                    key=f"q_{q.question_id}"
                )
                responses_to_save.append({
                    'question_id': q.question_id,
                    'text_value': value
                })

            # Confidence level
            confidence = st.select_slider(
                "Confidence",
                options=[1, 2, 3, 4, 5],
                value=existing.confidence_level if existing else 3,
                format_func=lambda x: ["Very Low", "Low", "Medium", "High", "Very High"][x-1],
                key=f"conf_{q.question_id}"
            )
            responses_to_save[-1]['confidence_level'] = confidence

            st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.form_submit_button("💾 Save Responses"):
                for resp in responses_to_save:
                    assessment_store.add_response(session_id=session_id, **resp)
                st.success("Responses saved!")
                st.rerun()

        with col2:
            if st.form_submit_button("✅ Complete Interview"):
                for resp in responses_to_save:
                    assessment_store.add_response(session_id=session_id, **resp)
                assessment_store.complete_interview(session_id)
                st.success("Interview completed!")
                st.session_state.active_interview = None
                st.rerun()

        with col3:
            if st.form_submit_button("❌ Close"):
                st.session_state.active_interview = None
                st.rerun()


def render_interview_results(session_id: str):
    """Render interview results and analysis."""
    analysis = assessment_store.get_interview_analysis(session_id)
    if not analysis:
        st.error("Analysis not found")
        return

    interview = assessment_store.get_interview(session_id)

    st.markdown("### Interview Results")
    st.markdown(f"**Application:** {analysis['application_id']}")

    # Overall Score
    col1, col2 = st.columns(2)

    with col1:
        score = analysis['overall_score']
        rating = analysis['overall_rating']

        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 10]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 2], 'color': "#dc3545"},
                    {'range': [2, 4], 'color': "#fd7e14"},
                    {'range': [4, 6], 'color': "#ffc107"},
                    {'range': [6, 8], 'color': "#17a2b8"},
                    {'range': [8, 10], 'color': "#28a745"}
                ]
            },
            title={'text': f"Overall Score<br><span style='font-size:0.8em'>{rating}</span>"}
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Category scores radar chart
        categories = list(analysis['category_scores'].keys())
        values = list(analysis['category_scores'].values())

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=[CATEGORY_NAMES.get(QuestionCategory(c), c)[:15] for c in categories] + [CATEGORY_NAMES.get(QuestionCategory(categories[0]), categories[0])[:15]],
            fill='toself',
            name='Category Scores'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=False,
            height=300,
            title="Category Breakdown"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Strengths and Weaknesses
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 💪 Strengths")
        for strength in analysis.get('strengths', []):
            st.markdown(f"✅ {strength}")
        if not analysis.get('strengths'):
            st.info("No significant strengths identified")

    with col2:
        st.markdown("#### ⚠️ Areas for Improvement")
        for weakness in analysis.get('weaknesses', []):
            st.markdown(f"🔸 {weakness}")
        if not analysis.get('weaknesses'):
            st.info("No significant weaknesses identified")

    # Recommendations
    st.markdown("#### 📋 Recommendations")
    for rec in analysis.get('recommendations', []):
        st.markdown(f"• {rec}")

    if st.button("Close Results"):
        st.session_state.view_results = None
        st.rerun()


def render_stakeholders_tab():
    """Render the stakeholders management tab."""
    st.subheader("Stakeholder Management")

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("➕ Add Stakeholder", key="add_stakeholder_btn"):
            st.session_state.show_add_stakeholder = True

    stakeholders = assessment_store.get_all_stakeholders()

    if not stakeholders:
        st.info("No stakeholders found. Click 'Add Stakeholder' to create one.")
    else:
        # Display as table
        data = []
        for s in stakeholders:
            interviews = assessment_store.get_all_interviews(stakeholder_id=s.stakeholder_id)
            completed = len([i for i in interviews if i.status == InterviewStatus.COMPLETED])

            data.append({
                "Name": s.name,
                "Email": s.email,
                "Role": s.role,
                "Department": s.department,
                "Type": s.stakeholder_type.value.replace("_", " ").title(),
                "Applications": len(s.applications),
                "Interviews": f"{completed}/{len(interviews)}"
            })

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

    # Add Stakeholder Form
    if st.session_state.get('show_add_stakeholder', False):
        st.markdown("### Add New Stakeholder")

        with st.form("add_stakeholder_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Name*")
                email = st.text_input("Email*")
                phone = st.text_input("Phone")

            with col2:
                role = st.text_input("Role/Title*")
                department = st.text_input("Department*")
                stakeholder_type = st.selectbox(
                    "Stakeholder Type*",
                    [t.value for t in StakeholderType],
                    format_func=lambda x: x.replace("_", " ").title()
                )

            applications = st.text_input(
                "Associated Applications",
                placeholder="Comma-separated, e.g., APP001, APP002"
            )
            availability = st.text_input("Availability Notes")
            notes = st.text_area("Additional Notes")

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Save Stakeholder"):
                    if name and email and role and department:
                        app_list = [a.strip() for a in applications.split(",")] if applications else []
                        assessment_store.create_stakeholder(
                            name=name,
                            email=email,
                            role=role,
                            department=department,
                            stakeholder_type=StakeholderType(stakeholder_type),
                            applications=app_list,
                            phone=phone,
                            availability=availability,
                            notes=notes
                        )
                        st.success("Stakeholder added successfully!")
                        st.session_state.show_add_stakeholder = False
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields")

            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_add_stakeholder = False
                    st.rerun()


def render_analysis_tab():
    """Render the analysis and reporting tab."""
    st.subheader("Portfolio Analysis")

    # Portfolio overview
    portfolio = assessment_store.get_portfolio_analysis()

    if portfolio.get('total_interviews', 0) == 0:
        st.info("No completed interviews to analyze. Complete some interviews to see portfolio analysis.")
        return

    # Summary metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Applications", portfolio.get('total_applications', 0))

    with col2:
        st.metric("Total Interviews", portfolio.get('total_interviews', 0))

    with col3:
        avg_score = portfolio.get('average_portfolio_score', 0)
        st.metric("Portfolio Avg Score", f"{avg_score:.1f}/10")

    st.markdown("---")

    # Top Performers
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏆 Top Performers")
        top = portfolio.get('top_performers', [])
        if top:
            for item in top:
                score = item['score']
                color = "#28a745" if score >= 7 else "#17a2b8" if score >= 5 else "#ffc107"
                st.markdown(f"**{item['application_id']}**: <span style='color:{color}'>{score}/10</span>", unsafe_allow_html=True)
        else:
            st.info("No data available")

    with col2:
        st.markdown("#### ⚠️ At Risk")
        at_risk = portfolio.get('at_risk', [])
        if at_risk:
            for item in at_risk:
                score = item['score']
                color = "#dc3545" if score < 3 else "#fd7e14" if score < 5 else "#ffc107"
                st.markdown(f"**{item['application_id']}**: <span style='color:{color}'>{score}/10</span>", unsafe_allow_html=True)
        else:
            st.success("No at-risk applications")

    st.markdown("---")

    # Score Distribution
    st.markdown("#### Score Distribution")

    completed_interviews = assessment_store.get_all_interviews(status="completed")
    if completed_interviews:
        scores = [i.overall_score for i in completed_interviews if i.overall_score]
        if scores:
            fig = px.histogram(
                x=scores,
                nbins=10,
                labels={'x': 'Score', 'y': 'Count'},
                title="Interview Score Distribution"
            )
            fig.update_layout(showlegend=False)
            chart_with_explanation(
                fig,
                title="Score Distribution",
                what_it_shows="Histogram of all interview scores",
                why_it_matters="Reveals the overall health profile of the application portfolio"
            )


def render_settings_tab():
    """Render the settings tab."""
    st.subheader("Assessment Settings")

    st.markdown("#### Category Weights")
    st.caption("Adjust the weight of each category in the overall score calculation")

    # Display current weights
    for category in QuestionCategory:
        current_weight = CATEGORY_WEIGHTS.get(category, 10)
        new_weight = st.slider(
            CATEGORY_NAMES.get(category, category.value),
            min_value=5,
            max_value=30,
            value=current_weight,
            key=f"weight_{category.value}"
        )

    st.markdown("---")

    st.markdown("#### Data Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Reset Sample Data"):
            # Clear and recreate sample data
            assessment_store.stakeholders.clear()
            assessment_store.interviews.clear()
            assessment_store.responses.clear()
            create_sample_data()
            st.success("Sample data reset successfully!")
            st.rerun()

    with col2:
        if st.button("📥 Export All Data"):
            st.info("Export functionality coming soon")

    st.markdown("---")

    st.markdown("#### Question Library")
    st.caption(f"Total questions: {len(ASSESSMENT_QUESTIONS)}")

    # Display questions by category
    for category in QuestionCategory:
        with st.expander(f"{CATEGORY_NAMES.get(category, category.value)} ({len(get_questions_by_category(category))} questions)"):
            for q in get_questions_by_category(category):
                st.markdown(f"**{q.question_id}**: {q.text}")
                st.caption(f"Type: {q.question_type.value} | Weight: {q.weight}")


# Initialize session state
if 'show_new_interview_modal' not in st.session_state:
    st.session_state.show_new_interview_modal = False
if 'show_add_stakeholder' not in st.session_state:
    st.session_state.show_add_stakeholder = False
if 'active_interview' not in st.session_state:
    st.session_state.active_interview = None
if 'view_results' not in st.session_state:
    st.session_state.view_results = None

# Run the page
render()
