"""
Module Catalog Page

Comprehensive showcase of all 25+ fraud detection modules with detailed
information about what each module detects, how it works, and its severity.
"""

import streamlit as st
from streamlit_app.api_client import get_api_client
import plotly.graph_objects as go


def render():
    """Render the Module Catalog page"""
    st.title("Fraud Detection Module Catalog")
    st.markdown("### Complete overview of all 25+ fraud detection modules")

    # Get API client
    client = get_api_client()

    try:
        # Fetch module catalog
        catalog_data = client.get_modules_catalog()
        modules = catalog_data.get("modules", [])
        total_count = catalog_data.get("total_modules", 0)

        # Display summary stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Modules", total_count)

        # Count by severity
        severity_counts = {}
        for module in modules:
            severity = module.get("severity", "medium")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        with col2:
            st.metric("Critical Modules", severity_counts.get("critical", 0))
        with col3:
            st.metric("High Risk Modules", severity_counts.get("high", 0))
        with col4:
            st.metric("Medium/Low Modules", severity_counts.get("medium", 0) + severity_counts.get("low", 0))

        st.divider()

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "All Modules",
            "By Category",
            "By Severity",
            "Module Statistics"
        ])

        # Tab 1: All Modules (Grid View)
        with tab1:
            st.markdown("### All Fraud Detection Modules")

            # Add search filter
            search_query = st.text_input("🔍 Search modules", "").lower()

            # Filter modules by search
            if search_query:
                filtered_modules = [
                    m for m in modules
                    if search_query in m.get("name", "").lower() or
                       search_query in m.get("description", "").lower() or
                       search_query in m.get("category", "").lower()
                ]
            else:
                filtered_modules = modules

            st.markdown(f"**Showing {len(filtered_modules)} of {len(modules)} modules**")

            # Display modules in a grid (2 columns)
            for i in range(0, len(filtered_modules), 2):
                col1, col2 = st.columns(2)

                # First module in row
                with col1:
                    render_module_card(filtered_modules[i])

                # Second module in row (if exists)
                if i + 1 < len(filtered_modules):
                    with col2:
                        render_module_card(filtered_modules[i + 1])

        # Tab 2: By Category
        with tab2:
            st.markdown("### Modules Grouped by Category")

            # Fetch grouped by category
            category_data = client.get_modules_catalog(group_by="category")
            categories = category_data.get("data", {})

            for category, category_modules in categories.items():
                with st.expander(f"**{category}** ({len(category_modules)} modules)", expanded=True):
                    for module in category_modules:
                        render_module_compact(module)

        # Tab 3: By Severity
        with tab3:
            st.markdown("### Modules Grouped by Severity")

            # Fetch grouped by severity
            severity_data = client.get_modules_catalog(group_by="severity")
            severity_groups = severity_data.get("data", {})

            # Define severity order and styling
            severity_order = ["critical", "high", "medium", "low"]
            severity_colors = {
                "critical": "#ff0000",
                "high": "#ff6600",
                "medium": "#ffcc00",
                "low": "#00cc66"
            }
            severity_icons = {
                "critical": "🚨",
                "high": "⚠️",
                "medium": "⚡",
                "low": "ℹ️"
            }

            for severity in severity_order:
                if severity in severity_groups:
                    severity_modules = severity_groups[severity]
                    icon = severity_icons.get(severity, "")
                    with st.expander(f"{icon} **{severity.upper()}** ({len(severity_modules)} modules)", expanded=(severity == "critical")):
                        for module in severity_modules:
                            render_module_compact(module)

        # Tab 4: Statistics
        with tab4:
            st.markdown("### Module Statistics & Distribution")

            # Severity distribution pie chart
            col1, col2 = st.columns(2)

            with col1:
                fig = go.Figure(data=[go.Pie(
                    labels=list(severity_counts.keys()),
                    values=list(severity_counts.values()),
                    hole=0.3,
                    marker=dict(colors=["#ff0000", "#ff6600", "#ffcc00", "#00cc66"])
                )])
                fig.update_layout(
                    title="Modules by Severity Level",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Count by category
                category_counts = {}
                for module in modules:
                    category = module.get("category", "Unknown")
                    category_counts[category] = category_counts.get(category, 0) + 1

                fig = go.Figure(data=[go.Bar(
                    x=list(category_counts.values()),
                    y=list(category_counts.keys()),
                    orientation='h',
                    marker=dict(color='#1f77b4')
                )])
                fig.update_layout(
                    title="Modules by Category",
                    xaxis_title="Number of Modules",
                    yaxis_title="Category",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

            # Detailed module breakdown
            st.markdown("### Detailed Module List")

            # Create table data
            table_data = []
            for module in sorted(modules, key=lambda x: x.get("severity", "medium")):
                table_data.append({
                    "Icon": module.get("icon", ""),
                    "Name": module.get("name", ""),
                    "Category": module.get("category", ""),
                    "Severity": module.get("severity", "").upper(),
                    "Detection Types": len(module.get("detects", []))
                })

            st.dataframe(
                table_data,
                use_container_width=True,
                height=400
            )

    except Exception as e:
        st.error(f"Error loading module catalog: {str(e)}")
        st.info("Please ensure the API server is running and you're authenticated.")


def render_module_card(module):
    """
    Render a detailed module card.

    Args:
        module: Module information dictionary
    """
    severity = module.get("severity", "medium")
    severity_colors = {
        "critical": "#ffcccc",
        "high": "#ffddaa",
        "medium": "#ffffcc",
        "low": "#ccffcc"
    }

    bg_color = severity_colors.get(severity, "#f0f2f6")

    icon = module.get("icon", "📋")
    name = module.get("name", "Unknown Module")
    category = module.get("category", "General")
    description = module.get("description", "No description available")
    detects = module.get("detects", [])

    st.markdown(f"""
    <div style="background-color: {bg_color}; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #1f77b4; margin-bottom: 1rem;">
        <h4>{icon} {name}</h4>
        <p><strong>Category:</strong> {category} | <strong>Severity:</strong> {severity.upper()}</p>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)

    # Detection capabilities
    if detects:
        with st.expander("🔍 Detection Capabilities", expanded=False):
            for detection in detects:
                st.markdown(f"- {detection}")

    # Real-world examples
    examples = module.get("examples", [])
    if examples:
        with st.expander("💡 Real-World Fraud Examples", expanded=False):
            for example in examples:
                st.markdown(f"- **{example}**")


def render_module_compact(module):
    """
    Render a compact module view for grouped displays.

    Args:
        module: Module information dictionary
    """
    icon = module.get("icon", "📋")
    name = module.get("name", "Unknown Module")
    description = module.get("description", "No description available")
    detects = module.get("detects", [])
    severity = module.get("severity", "medium")

    st.markdown(f"**{icon} {name}** - *{severity.upper()}*")
    st.markdown(f"_{description}_")

    with st.expander("Show detection capabilities & examples"):
        st.markdown("**What it detects:**")
        for detection in detects:
            st.markdown(f"• {detection}")

        examples = module.get("examples", [])
        if examples:
            st.markdown("")
            st.markdown("**💡 Real-World Examples:**")
            for example in examples:
                st.markdown(f"• **{example}**")

    st.markdown("---")


if __name__ == "__main__" or True:
    render()
