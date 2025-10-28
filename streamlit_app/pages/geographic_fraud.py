"""
Geographic Fraud Heatmap Page

Visualizes fraud activity geographically with interactive maps and charts.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, Any

from streamlit_app.api_client import get_api_client


def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:,.2f}"


def render_geographic_stats(geo_data: Dict[str, Any]):
    """Render geographic overview statistics"""
    col1, col2, col3, col4 = st.columns(4)

    data = geo_data.get("data", [])

    total_transactions = sum(d["transaction_count"] for d in data)
    total_fraud = sum(d["fraud_count"] for d in data)
    total_amount = sum(d["total_amount"] for d in data)
    high_risk_countries = len([d for d in data if d["risk_level"] in ["high", "critical"]])

    with col1:
        st.metric("Countries Active", geo_data.get("total_countries", 0))

    with col2:
        st.metric("Total Transactions", f"{total_transactions:,}")

    with col3:
        st.metric("Fraud Cases", total_fraud,
                 f"{(total_fraud/total_transactions*100) if total_transactions > 0 else 0:.1f}%")

    with col4:
        st.metric("High-Risk Countries", high_risk_countries)


def render_world_map(geo_data: Dict[str, Any]):
    """Render choropleth world map"""
    data = geo_data.get("data", [])

    if not data:
        st.info("No geographic data available for this period")
        return

    df = pd.DataFrame(data)

    # Create choropleth map
    fig = px.choropleth(
        df,
        locations="country_code",
        color="avg_risk_score",
        hover_name="country",
        hover_data={
            "country_code": False,
            "avg_risk_score": ":.3f",
            "transaction_count": True,
            "fraud_count": True,
            "fraud_rate": ":.2%",
            "total_amount": ":,.0f"
        },
        color_continuous_scale="Reds",
        range_color=[0, 1],
        title="Global Fraud Risk Heatmap",
        labels={
            "avg_risk_score": "Avg Risk Score",
            "transaction_count": "Transactions",
            "fraud_count": "Fraud Cases",
            "fraud_rate": "Fraud Rate",
            "total_amount": "Total Amount"
        }
    )

    fig.update_layout(
        height=500,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='natural earth'
        )
    )

    st.plotly_chart(fig, use_container_width=True)


def render_top_countries_chart(geo_data: Dict[str, Any]):
    """Render top countries by fraud activity"""
    data = geo_data.get("data", [])

    if not data:
        return

    # Sort by fraud count
    sorted_data = sorted(data, key=lambda x: x["fraud_count"], reverse=True)[:10]

    df = pd.DataFrame(sorted_data)

    # Create horizontal bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df["country"],
        x=df["fraud_count"],
        name="Fraud Cases",
        orientation='h',
        marker=dict(
            color=df["avg_risk_score"],
            colorscale="Reds",
            showscale=True,
            colorbar=dict(title="Avg Risk")
        ),
        text=df["fraud_count"],
        textposition="auto"
    ))

    fig.update_layout(
        title="Top 10 Countries by Fraud Activity",
        xaxis_title="Number of Fraud Cases",
        yaxis_title="Country",
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)


def render_country_risk_levels(geo_data: Dict[str, Any]):
    """Render risk level breakdown"""
    data = geo_data.get("data", [])

    if not data:
        return

    # Count by risk level
    risk_counts = {}
    for country in data:
        risk_level = country["risk_level"]
        if risk_level not in risk_counts:
            risk_counts[risk_level] = {"count": 0, "transactions": 0, "fraud": 0}

        risk_counts[risk_level]["count"] += 1
        risk_counts[risk_level]["transactions"] += country["transaction_count"]
        risk_counts[risk_level]["fraud"] += country["fraud_count"]

    # Create pie chart
    labels = []
    values = []
    colors = []

    color_map = {
        "low": "#90EE90",
        "medium": "#FFD700",
        "high": "#FF8C00",
        "critical": "#DC143C"
    }

    for level, counts in risk_counts.items():
        labels.append(f"{level.title()} ({counts['count']} countries)")
        values.append(counts["transactions"])
        colors.append(color_map.get(level, "#808080"))

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.3,
        textinfo='label+percent'
    )])

    fig.update_layout(
        title="Transaction Distribution by Country Risk Level",
        height=350
    )

    st.plotly_chart(fig, use_container_width=True)


def render_country_table(geo_data: Dict[str, Any]):
    """Render detailed country statistics table"""
    data = geo_data.get("data", [])

    if not data:
        return

    # Sort by fraud count
    sorted_data = sorted(data, key=lambda x: x["fraud_count"], reverse=True)

    df = pd.DataFrame(sorted_data)

    # Select and format columns
    display_df = df[[
        "country", "transaction_count", "fraud_count",
        "fraud_rate", "avg_risk_score", "total_amount", "risk_level"
    ]].copy()

    display_df.columns = [
        "Country", "Transactions", "Fraud Cases",
        "Fraud Rate", "Avg Risk", "Total Amount", "Risk Level"
    ]

    # Format columns
    display_df["Fraud Rate"] = display_df["Fraud Rate"].apply(lambda x: f"{x*100:.1f}%")
    display_df["Avg Risk"] = display_df["Avg Risk"].apply(lambda x: f"{x:.3f}")
    display_df["Total Amount"] = display_df["Total Amount"].apply(lambda x: format_currency(x))
    display_df["Risk Level"] = display_df["Risk Level"].str.title()

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


def render_fraud_rate_scatter(geo_data: Dict[str, Any]):
    """Render scatter plot of fraud rate vs transaction volume"""
    data = geo_data.get("data", [])

    if not data:
        return

    df = pd.DataFrame(data)

    # Create scatter plot
    fig = px.scatter(
        df,
        x="transaction_count",
        y="fraud_rate",
        size="total_amount",
        color="risk_level",
        hover_name="country",
        hover_data={
            "transaction_count": True,
            "fraud_rate": ":.2%",
            "avg_risk_score": ":.3f",
            "total_amount": ":,.0f"
        },
        color_discrete_map={
            "low": "#90EE90",
            "medium": "#FFD700",
            "high": "#FF8C00",
            "critical": "#DC143C"
        },
        title="Fraud Rate vs Transaction Volume by Country",
        labels={
            "transaction_count": "Number of Transactions",
            "fraud_rate": "Fraud Rate",
            "risk_level": "Risk Level"
        }
    )

    fig.update_layout(height=400)

    st.plotly_chart(fig, use_container_width=True)


def render():
    """Render the Geographic Fraud Heatmap page"""

    # Header
    st.markdown("# 🗺️ Geographic Fraud Heatmap")
    st.markdown("Global fraud activity visualization and geographic risk analysis")

    # Time range selector
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        time_range = st.selectbox(
            "Time Range",
            ["1h", "24h", "7d", "30d"],
            index=1,
            format_func=lambda x: {
                "1h": "Last Hour",
                "24h": "Last 24 Hours",
                "7d": "Last 7 Days",
                "30d": "Last 30 Days"
            }[x]
        )

    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    with col3:
        st.markdown("")  # Spacing

    st.divider()

    # Fetch data
    client = get_api_client()

    try:
        with st.spinner("Loading geographic fraud data..."):
            geo_data = client.get_geographic_fraud_data(time_range)

        # Display timestamp
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Overview statistics
        st.markdown("### 🌍 Geographic Overview")
        render_geographic_stats(geo_data)

        st.divider()

        # World map
        st.markdown("### 🗺️ Global Fraud Risk Distribution")
        render_world_map(geo_data)

        st.divider()

        # Charts row
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📊 Top Fraud Countries")
            render_top_countries_chart(geo_data)

        with col2:
            st.markdown("### 🎯 Risk Level Distribution")
            render_country_risk_levels(geo_data)

        st.divider()

        # Scatter plot
        st.markdown("### 📈 Fraud Rate Analysis")
        render_fraud_rate_scatter(geo_data)

        st.divider()

        # Detailed table
        with st.expander("📋 View Detailed Country Statistics"):
            render_country_table(geo_data)

        # Insights
        st.divider()
        st.markdown("### 💡 Geographic Insights")

        data = geo_data.get("data", [])
        if data:
            # Find highest risk country
            highest_risk_country = max(data, key=lambda x: x["avg_risk_score"])
            # Find country with most fraud
            most_fraud_country = max(data, key=lambda x: x["fraud_count"])

            col1, col2, col3 = st.columns(3)

            with col1:
                st.warning(f"**Highest Risk Country:**\n\n{highest_risk_country['country']}\n\nAvg Risk: {highest_risk_country['avg_risk_score']:.3f}")

            with col2:
                st.error(f"**Most Fraud Cases:**\n\n{most_fraud_country['country']}\n\n{most_fraud_country['fraud_count']} cases")

            with col3:
                high_risk_countries = [d for d in data if d["risk_level"] in ["high", "critical"]]
                st.info(f"**High-Risk Regions:**\n\n{len(high_risk_countries)} countries\n\nRequire monitoring")

    except Exception as e:
        st.error(f"❌ Error loading geographic data: {str(e)}")
        st.exception(e)


if __name__ == "__main__" or True:
    render()
