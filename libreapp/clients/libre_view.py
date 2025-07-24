"""
LibreView Client - Medical Technology API Library
-------------------------------------------------
This module provides a robust, SOLID-compliant implementation for interacting with the LibreView CGM API.
It follows medical technology standards for data handling and security.
"""

import requests
from typing import Any, Dict, Optional, Protocol
from dataclasses import dataclass
from ..utils.logger import setup_logger
from ..utils.data_masking import DataMasker, DefaultDataMasker

# Get loggers
console_log, file_log = setup_logger()

@dataclass
class ApiConfig:
    """Configuration for LibreView API endpoints"""
    base_url: str = "https://libreview-proxy.onrender.com"
    region: str = "us"
    version: str = "4.7"
    product: str = "llu.ios"
    timeout: int = 30

class SecurityHeaders(Protocol):
    """Protocol defining security header requirements"""
    def get_auth_headers(self) -> Dict[str, str]: ...
    def get_default_headers(self) -> Dict[str, str]: ...

class HttpClient(Protocol):
    """Protocol defining HTTP client requirements"""
    def request(self, method: str, url: str, **kwargs) -> Any: ...

class LibreCGMClient:
    """
    Medical-grade LibreView CGM API client implementing SOLID principles.
    """
    
    def __init__(self, email: str, password: str, 
                 config: Optional[ApiConfig] = None,
                 data_masker: Optional[DataMasker] = None):
        """
        Initialize the LibreView client with dependency injection.
        
        Args:
            email: User's email address
            password: User's password
            config: API configuration (optional)
            data_masker: Data masking implementation (optional)
        """
        self.config = config or ApiConfig()
        self.data_masker = data_masker or DefaultDataMasker()
        
        self.base_url = self.config.base_url.rstrip('/')
        if self.config.region:
            self.base_url = f"{self.base_url}/{self.config.region}"
            
        self.email = email
        self.password = password
        self.token: Optional[str] = None
        self.auth_ticket: Optional[Dict[str, Any]] = None
        
        # Set default headers with provided or default values
        self.DEFAULT_HEADERS = {
            "version": self.config.version,
            "product": self.config.product
        }

    def _make_request(self, method: str, endpoint: str, 
                     headers: Dict[str, str] = None,
                     data: Any = None, 
                     params: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Make an HTTP request with proper logging and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            headers: Request headers
            data: Request body data
            params: URL parameters
            
        Returns:
            Dict containing the response data
        """
        url = f"{self.base_url}{endpoint}"
        headers = headers or self.DEFAULT_HEADERS
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            file_log.error(f"Request failed: {str(e)}")
            raise

    def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with the LibreView API.
        
        This method handles:
        1. Initial login attempt
        2. Automatic regional redirects
        3. Terms of use acceptance when required
        4. Secure token management
        
        Returns:
            Dict containing authentication response data
        """
        payload = {
            "email": self.email,
            "password": self.password
        }
        
        data = self._make_request('POST', '/llu/auth/login', data=payload)
        
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
        """
        Accept Terms of Use when required during authentication.
        
        Returns:
            Dict containing the terms acceptance response
        """
        if not self.auth_ticket:
            raise RuntimeError("No auth ticket available. Must authenticate first.")
            
        headers = {
            **self.DEFAULT_HEADERS,
            "Authorization": f"Bearer {self.auth_ticket['token']}"
        }
        
        data = self._make_request('POST', '/auth/continue/tou', headers=headers)
        self.auth_ticket = data['data']['authTicket']
        self.token = self.auth_ticket['token']
        return data

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get headers with authentication token.
        
        Returns:
            Dict containing headers with auth token
        """
        if not self.token:
            raise RuntimeError("Client is not authenticated. Call .authenticate() first.")
        return {
            **self.DEFAULT_HEADERS,
            "Authorization": f"Bearer {self.token}"
        }

    def get_current_user(self) -> Dict[str, Any]:
        """
        Get the current user's profile data.
        
        Returns:
            Dict containing user profile information
        """
        return self._make_request('GET', '/user', headers=self._get_auth_headers())

    def get_account(self) -> Dict[str, Any]:
        """
        Get the current user's account information.
        
        Returns:
            Dict containing account details
        """
        return self._make_request('GET', '/account', headers=self._get_auth_headers())

    def list_connections(self) -> Dict[str, Any]:
        """
        List all patient connections.
        
        Returns:
            Dict containing list of patient connections
        """
        return self._make_request('GET', '/llu/connections', headers=self._get_auth_headers())

    def get_patient_graph(self, patient_id: str) -> Dict[str, Any]:
        """
        Get glucose graph data for a patient.
        
        Args:
            patient_id: The ID of the patient to fetch data for
            
        Returns:
            Dict containing glucose graph data
        """
        if not patient_id:
            raise ValueError("patient_id cannot be empty")
            
        return self._make_request(
            'GET', 
            f'/llu/connections/{patient_id}/graph',
            headers=self._get_auth_headers()
        )

    def get_patient_logbook(self, patient_id: str) -> Dict[str, Any]:
        """
        Get logbook entries for a patient.
        
        Args:
            patient_id: The ID of the patient to fetch logbook for
            
        Returns:
            Dict containing logbook entries
        """
        if not patient_id:
            raise ValueError("patient_id cannot be empty")
            
        return self._make_request(
            'GET',
            f'/llu/connections/{patient_id}/logbook',
            headers=self._get_auth_headers()
        )

    def get_notification_settings(self, connection_id: str) -> Dict[str, Any]:
        """
        Get notification settings for a connection.
        
        Args:
            connection_id: The ID of the connection to fetch settings for
            
        Returns:
            Dict containing notification settings
        """
        if not connection_id:
            raise ValueError("connection_id cannot be empty")
            
        return self._make_request(
            'GET',
            f'/llu/notifications/settings/{connection_id}',
            headers=self._get_auth_headers()
        )

    def get_country_config(self, country_code: str) -> Dict[str, Any]:
        """
        Get configuration for a specific country.
        
        Args:
            country_code: Two-letter country code (ISO 3166-1 alpha-2)
            
        Returns:
            Dict containing country-specific configuration
        """
        if not country_code or len(country_code) != 2:
            raise ValueError("country_code must be a valid 2-letter code")
            
        return self._make_request(
            'GET',
            '/llu/config/country',
            headers=self.DEFAULT_HEADERS,
            params={"country": country_code}
        )
