"""Dashboard Pages"""

# Import all page modules
from streamlit_app.pages import real_time_monitoring as Real_Time_Monitoring
from streamlit_app.pages import Risk_Intelligence
from streamlit_app.pages import Case_Investigation_Center
from streamlit_app.pages import QuantShield_AI_Modules

__all__ = [
    'Real_Time_Monitoring',
    'Risk_Intelligence',
    'Case_Investigation_Center',
    'QuantShield_AI_Modules'
]
