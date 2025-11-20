"""
Chart with Tooltip Component

Provides a global toggle for chart explanations and a wrapper function
to add consistent tooltips to all visualizations.
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Optional


def init_tooltip_toggle():
    """
    Initialize the global tooltip toggle in the sidebar.
    Call this once at the start of each page.
    """
    if "tooltips_enabled" not in st.session_state:
        st.session_state.tooltips_enabled = True

    # Add divider and toggle to sidebar for visibility
    st.sidebar.divider()
    st.sidebar.markdown("**Chart Options**")

    # Add toggle to sidebar
    toggled = st.sidebar.toggle(
        "Show Chart Explanations",
        value=st.session_state.tooltips_enabled,
        help="Toggle explanatory tooltips for all charts on this page"
    )

    # Update session state from toggle
    st.session_state.tooltips_enabled = toggled


def get_tooltips_enabled() -> bool:
    """
    Check if tooltips are currently enabled.

    Returns:
        bool: True if tooltips are enabled, False otherwise
    """
    return st.session_state.get("tooltips_enabled", True)


def chart_with_explanation(
    fig: go.Figure,
    title: str = "",
    what_it_shows: str = "",
    why_it_matters: str = "",
    what_to_do: Optional[str] = None,
    expanded: bool = False
):
    """
    Render a Plotly chart with an optional explanation panel.

    Args:
        fig: Plotly figure object to display
        title: Title for the explanation section
        what_it_shows: Description of what the visualization displays
        why_it_matters: Explanation of why this data is important for fraud detection
        what_to_do: Optional action items or recommendations
        expanded: Whether the explanation expander starts expanded (default False)

    Example:
        ```python
        fig = px.bar(df, x='category', y='count')
        chart_with_explanation(
            fig,
            title="Transaction Categories",
            what_it_shows="Distribution of transactions across different categories",
            why_it_matters="Unusual category distributions may indicate fraud patterns",
            what_to_do="Investigate categories with >20% deviation from baseline"
        )
        ```
    """
    # Show explanation if tooltips are enabled
    if get_tooltips_enabled() and (what_it_shows or why_it_matters):
        expander_title = f"About this chart" if not title else f"About: {title}"

        with st.expander(expander_title, expanded=expanded):
            if what_it_shows:
                st.markdown(f"**What it shows:** {what_it_shows}")

            if why_it_matters:
                st.markdown(f"**Why it matters:** {why_it_matters}")

            if what_to_do:
                st.markdown(f"**What to do:** {what_to_do}")

    # Render the chart
    st.plotly_chart(fig, use_container_width=True)


def metric_with_explanation(
    label: str,
    value: str,
    delta: Optional[str] = None,
    what_it_shows: str = "",
    why_it_matters: str = "",
    what_to_do: Optional[str] = None
):
    """
    Render a Streamlit metric with an optional explanation tooltip.

    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta value (e.g., "+5%")
        what_it_shows: Description of what this metric represents
        why_it_matters: Why this metric is important
        what_to_do: Recommended actions based on this metric
    """
    # Show metric
    st.metric(label=label, value=value, delta=delta)

    # Show explanation if tooltips are enabled
    if get_tooltips_enabled() and (what_it_shows or why_it_matters):
        with st.expander(f"About: {label}", expanded=False):
            if what_it_shows:
                st.markdown(f"**What it shows:** {what_it_shows}")

            if why_it_matters:
                st.markdown(f"**Why it matters:** {why_it_matters}")

            if what_to_do:
                st.markdown(f"**What to do:** {what_to_do}")


def dataframe_with_explanation(
    df,
    title: str = "",
    what_it_shows: str = "",
    why_it_matters: str = "",
    what_to_do: Optional[str] = None,
    **kwargs
):
    """
    Render a Streamlit dataframe with an optional explanation panel.

    Args:
        df: Pandas DataFrame to display
        title: Title for the explanation section
        what_it_shows: Description of what the data represents
        why_it_matters: Why this data is important
        what_to_do: Recommended actions
        **kwargs: Additional arguments passed to st.dataframe()
    """
    # Show explanation if tooltips are enabled
    if get_tooltips_enabled() and (what_it_shows or why_it_matters):
        expander_title = f"About this data" if not title else f"About: {title}"

        with st.expander(expander_title, expanded=False):
            if what_it_shows:
                st.markdown(f"**What it shows:** {what_it_shows}")

            if why_it_matters:
                st.markdown(f"**Why it matters:** {why_it_matters}")

            if what_to_do:
                st.markdown(f"**What to do:** {what_to_do}")

    # Render the dataframe
    st.dataframe(df, **kwargs)
