import requests
from typing import Any, Dict, Optional
import time

class LibreCGMClient:
    """
    Client implementation for the LibreView API according to OpenAPI specification.
    """

    DEFAULT_HEADERS = {
        "version": "4.7",
        "product": "llu.android"
    }

    def __init__(self, email: str, password: str, 
                 base_url: str = "https://libreview-proxy.onrender.com",
                 region: str = "us"):
        """
        Initialize the LibreView client.
        
        Args:
            email: User's email address
            password: User's password
            base_url: Base URL for the API (default: libreview-proxy)
            region: Region code (default: us)
        """
        self.base_url = base_url.rstrip('/')
        if region:
            self.base_url = f"{self.base_url}/{region}"
        self.email = email
        self.password = password
        self.token: Optional[str] = None
        self.auth_ticket: Optional[Dict[str, Any]] = None
        self.timeout = 30  # seconds

    def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with the LibreView API.
        
        Handles:
        1. Initial login
        2. Regional redirects
        3. Terms of use acceptance if needed
        
        Returns:
            Dict containing auth response data
        """
        url = f"{self.base_url}/llu/auth/login"
        payload = {
            "email": self.email,
            "password": self.password
        }
        response = requests.post(
            url, 
            json=payload, 
            headers=self.DEFAULT_HEADERS,
            timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()
        
        # Handle region redirect if needed
        if data.get('data', {}).get('redirect'):
            new_region = data['data']['region']
            self.base_url = f"{self.base_url.rsplit('/', 1)[0]}/{new_region}"
            return self.authenticate()
        
        # Handle terms of use acceptance if needed
        if data.get('status') == 4:
            self.auth_ticket = data['data']['authTicket']
            return self.accept_terms()
            
        # Normal login success
        self.auth_ticket = data['data']['authTicket']
        self.token = self.auth_ticket['token']
        return data

    def accept_terms(self) -> Dict[str, Any]:
        """Accept Terms of Use when required."""
        url = f"{self.base_url}/auth/continue/tou"
        response = requests.post(
            url,
            headers={
                **self.DEFAULT_HEADERS,
                "Authorization": f"Bearer {self.auth_ticket['token']}"
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()
        self.auth_ticket = data['data']['authTicket']
        self.token = self.auth_ticket['token']
        return data

    def _headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        if not self.token:
            raise RuntimeError("Client is not authenticated. Call .authenticate() first.")
        return {
            **self.DEFAULT_HEADERS,
            "Authorization": f"Bearer {self.token}"
        }

    def get_current_user(self) -> Dict[str, Any]:
        """Get the current user's profile data."""
        url = f"{self.base_url}/user"
        resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_account(self) -> Dict[str, Any]:
        """Get the current user's account information."""
        url = f"{self.base_url}/account"
        resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def list_connections(self) -> Dict[str, Any]:
        """List all patient connections."""
        url = f"{self.base_url}/llu/connections"
        resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_patient_graph(self, patient_id: str) -> Dict[str, Any]:
        """Get glucose graph data for a patient."""
        url = f"{self.base_url}/llu/connections/{patient_id}/graph"
        resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_patient_logbook(self, patient_id: str) -> Dict[str, Any]:
        """Get logbook entries for a patient."""
        url = f"{self.base_url}/llu/connections/{patient_id}/logbook"
        resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_notification_settings(self, connection_id: str) -> Dict[str, Any]:
        """Get notification settings for a connection."""
        url = f"{self.base_url}/llu/notifications/settings/{connection_id}"
        resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_country_config(self, country_code: str) -> Dict[str, Any]:
        """Get configuration for a specific country."""
        url = f"{self.base_url}/llu/config/country"
        params = {"country": country_code}
        resp = requests.get(
            url,
            headers=self.DEFAULT_HEADERS,
            params=params,
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()
