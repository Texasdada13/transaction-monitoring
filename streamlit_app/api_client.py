"""
API Client for Streamlit Dashboard

Handles all communication with the FastAPI backend.
Manages authentication tokens and API requests.
"""

import requests
from typing import Optional, Dict, Any, List
import streamlit as st

class FraudAPIClient:
    """
    Client for interacting with the Transaction Monitoring API.

    Handles authentication, token management, and API requests.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client.

        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip("/")
        self.token = None
        self.user_info = {}

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and obtain JWT token.

        Args:
            username: Username
            password: Password

        Returns:
            User information and token

        Raises:
            requests.HTTPError: If login fails
        """
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            data={"username": username, "password": password}
        )
        response.raise_for_status()

        data = response.json()
        self.token = data["access_token"]
        self.user_info = {
            "user_id": data["user_id"],
            "role": data["role"],
            "username": username
        }

        return self.user_info

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication token"""
        if not self.token:
            raise ValueError("Not authenticated. Please login first.")

        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        response = requests.get(f"{self.base_url}/")
        response.raise_for_status()
        return response.json()

    def get_overview_stats(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Get overview statistics.

        Args:
            time_window_hours: Time window for stats (default 24)

        Returns:
            Overview statistics
        """
        response = requests.get(
            f"{self.base_url}/api/v1/overview",
            headers=self._get_headers(),
            params={"time_window_hours": time_window_hours}
        )
        response.raise_for_status()
        return response.json()

    def get_live_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get live fraud alerts (manual review queue).

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of alerts
        """
        response = requests.get(
            f"{self.base_url}/api/v1/alerts/live",
            headers=self._get_headers(),
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()

    def get_top_triggered_rules(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most frequently triggered rules.

        Args:
            limit: Number of rules to return

        Returns:
            List of rule statistics
        """
        response = requests.get(
            f"{self.base_url}/api/v1/rules/top",
            headers=self._get_headers(),
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()

    def get_scenario_breakdown(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Get fraud activity breakdown by scenario.

        Args:
            time_window_hours: Time window for analysis

        Returns:
            Scenario breakdown data
        """
        response = requests.get(
            f"{self.base_url}/api/v1/scenarios/breakdown",
            headers=self._get_headers(),
            params={"time_window_hours": time_window_hours}
        )
        response.raise_for_status()
        return response.json()

    def get_recent_account_changes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent account changes.

        Args:
            limit: Number of changes to return

        Returns:
            List of account changes
        """
        response = requests.get(
            f"{self.base_url}/api/v1/account-changes/recent",
            headers=self._get_headers(),
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()

    def get_transaction_details(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get detailed transaction information.

        Args:
            transaction_id: Transaction ID to lookup

        Returns:
            Transaction details
        """
        response = requests.get(
            f"{self.base_url}/api/v1/transaction/{transaction_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def update_alert_status(
        self,
        assessment_id: str,
        action: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update alert status (approve, reject, escalate).

        Args:
            assessment_id: Risk assessment ID
            action: Action to take (approved, rejected, escalated)
            notes: Optional review notes

        Returns:
            Updated status
        """
        response = requests.post(
            f"{self.base_url}/api/v1/alert/{assessment_id}/action",
            headers=self._get_headers(),
            params={"action": action, "notes": notes}
        )
        response.raise_for_status()
        return response.json()

    def get_time_series_metrics(self, time_range: str = "24h") -> Dict[str, Any]:
        """
        Get time-series metrics for trend analysis.

        Args:
            time_range: Time range (1h, 24h, 7d, 30d)

        Returns:
            Time-series data
        """
        response = requests.get(
            f"{self.base_url}/api/v1/metrics/time-series",
            headers=self._get_headers(),
            params={"time_range": time_range}
        )
        response.raise_for_status()
        return response.json()


# ==================== Streamlit Session State Management ====================

def get_api_client() -> FraudAPIClient:
    """
    Get or create API client from Streamlit session state.

    Returns:
        Configured API client instance
    """
    if "api_client" not in st.session_state:
        # Get API URL from environment or use default
        import os
        api_url = os.getenv("API_URL", "http://localhost:8000")
        st.session_state.api_client = FraudAPIClient(api_url)

    return st.session_state.api_client


def is_authenticated() -> bool:
    """
    Check if user is authenticated.

    Returns:
        True if authenticated, False otherwise
    """
    client = get_api_client()
    return client.token is not None


def get_user_info() -> Dict[str, Any]:
    """
    Get authenticated user information.

    Returns:
        User info dictionary
    """
    client = get_api_client()
    return client.user_info


def logout():
    """Logout current user"""
    client = get_api_client()
    client.token = None
    client.user_info = {}
    st.session_state.clear()
