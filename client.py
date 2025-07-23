"""
LibreView CGM Client - Medical Technology API Library
-------------------------------------------------
This module provides a robust, SOLID-compliant implementation for interacting with the LibreView CGM API.
It follows medical technology standards for data handling and security.
"""

import requests
from typing import Any, Dict, Optional, Protocol
from logger_config import setup_logger
from dataclasses import dataclass

# Get loggers
console_log, file_log = setup_logger()

@dataclass
class ApiConfig:
    """Configuration for API endpoints"""
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

class DataMasker(Protocol):
    """Protocol for sensitive data masking"""
    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]: ...

class ApiLogger(Protocol):
    """Protocol for API logging"""
    def log_request(self, method: str, url: str, headers: Dict[str, str], data: Any = None) -> None: ...
    def log_response(self, response: Any) -> None: ...

class DefaultDataMasker:
    """Default implementation of data masking"""
    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
            
        masked_data = data.copy()
        sensitive_fields = ['token', 'email', 'password', 'firstName', 'lastName', 'Authorization']
        
        for key, value in masked_data.items():
            if key in sensitive_fields and value:
                masked_data[key] = f"{str(value)[:3]}...{str(value)[-4:]}" if len(str(value)) > 8 else "****"
        return masked_data

class LibreViewApiLogger:
    """Implementation of API logging"""
    def __init__(self, data_masker: DataMasker):
        self.data_masker = data_masker

    def log_request(self, method: str, url: str, headers: Dict[str, str], data: Any = None) -> None:
        masked_headers = self.data_masker.mask_sensitive_data(headers)
        masked_data = self.data_masker.mask_sensitive_data(data) if data else None
        
        http_data = {
            'request': {
                'method': method,
                'url': url,
                'headers': masked_headers,
                'body': masked_data
            }
        }
        file_log.debug("Making HTTP request", extra={'http_data': http_data})
    
    def log_response(self, response: requests.Response) -> None:
        try:
            response_body = response.json()
        except ValueError:
            response_body = response.text
            
        http_data = {
            'response': {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response_body
            }
        }
        file_log.debug("Received HTTP response", extra={'http_data': http_data})

class LibreCGMClient:

    """
    Medical-grade LibreView CGM API client implementing SOLID principles.
    """
    
    def __init__(self, email: str, password: str, 
                 config: Optional[ApiConfig] = None,
                 logger: Optional[ApiLogger] = None,
                 data_masker: Optional[DataMasker] = None):
        """
        Initialize the LibreView client with dependency injection.
        
        Args:
            email: User's email address
            password: User's password
            config: API configuration (optional)
            logger: API logger implementation (optional)
            data_masker: Data masking implementation (optional)
        """
        self.config = config or ApiConfig()
        self.data_masker = data_masker or DefaultDataMasker()
        self.logger = logger or LibreViewApiLogger(self.data_masker)
        
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

    def _make_request(self, method: str, url: str, headers: Dict[str, str] = None, 
                       data: Any = None, params: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Make an HTTP request with proper logging and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            data: Request body data
            params: URL parameters
            
        Returns:
            Dict containing the response data
            
        Raises:
            requests.exceptions.RequestException: For any HTTP-related errors
        """
        headers = headers or self.DEFAULT_HEADERS
        self.logger.log_request(method, url, headers, data)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=self.config.timeout
            )
            self.logger.log_response(response)
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
            
        Raises:
            requests.exceptions.RequestException: For authentication failures
            RuntimeError: For invalid authentication states
        """
        url = f"{self.base_url}/llu/auth/login"
        payload = {
            "email": self.email,
            "password": self.password
        }
        
        data = self._make_request('POST', url, self.DEFAULT_HEADERS, payload)
        
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
            
        Raises:
            requests.exceptions.RequestException: For request failures
            RuntimeError: If no auth ticket is present
        """
        if not self.auth_ticket:
            raise RuntimeError("No auth ticket available. Must authenticate first.")
            
        url = f"{self.base_url}/auth/continue/tou"
        headers = {
            **self.DEFAULT_HEADERS,
            "Authorization": f"Bearer {self.auth_ticket['token']}"
        }
        
        data = self._make_request('POST', url, headers)
        self.auth_ticket = data['data']['authTicket']
        self.token = self.auth_ticket['token']
        return data

    def _headers(self) -> Dict[str, str]:
        """
        Get headers with authentication token.
        
        Returns:
            Dict containing headers with auth token
            
        Raises:
            RuntimeError: If client is not authenticated
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
            
        Raises:
            requests.exceptions.RequestException: For request failures
        """
        url = f"{self.base_url}/user"
        return self._make_request('GET', url, self._headers())

    def get_account(self) -> Dict[str, Any]:
        """
        Get the current user's account information.
        
        Returns:
            Dict containing account details
            
        Raises:
            requests.exceptions.RequestException: For request failures
        """
        url = f"{self.base_url}/account"
        return self._make_request('GET', url, self._headers())

    def list_connections(self) -> Dict[str, Any]:
        """
        List all patient connections.
        
        Returns:
            Dict containing list of patient connections
            
        Raises:
            requests.exceptions.RequestException: For request failures
        """
        url = f"{self.base_url}/llu/connections"
        return self._make_request('GET', url, self._headers())

    def get_patient_graph(self, patient_id: str) -> Dict[str, Any]:
        """
        Get glucose graph data for a patient.
        
        Args:
            patient_id: The ID of the patient to fetch data for
            
        Returns:
            Dict containing glucose graph data
            
        Raises:
            requests.exceptions.RequestException: For request failures
            ValueError: If patient_id is invalid
        """
        if not patient_id:
            raise ValueError("patient_id cannot be empty")
            
        url = f"{self.base_url}/llu/connections/{patient_id}/graph"
        return self._make_request('GET', url, self._headers())

    def get_patient_logbook(self, patient_id: str) -> Dict[str, Any]:
        """
        Get logbook entries for a patient.
        
        Args:
            patient_id: The ID of the patient to fetch logbook for
            
        Returns:
            Dict containing logbook entries
            
        Raises:
            requests.exceptions.RequestException: For request failures
            ValueError: If patient_id is invalid
        """
        if not patient_id:
            raise ValueError("patient_id cannot be empty")
            
        url = f"{self.base_url}/llu/connections/{patient_id}/logbook"
        return self._make_request('GET', url, self._headers())

    def get_notification_settings(self, connection_id: str) -> Dict[str, Any]:
        """
        Get notification settings for a connection.
        
        Args:
            connection_id: The ID of the connection to fetch settings for
            
        Returns:
            Dict containing notification settings
            
        Raises:
            requests.exceptions.RequestException: For request failures
            ValueError: If connection_id is invalid
        """
        if not connection_id:
            raise ValueError("connection_id cannot be empty")
            
        url = f"{self.base_url}/llu/notifications/settings/{connection_id}"
        return self._make_request('GET', url, self._headers())

    def get_country_config(self, country_code: str) -> Dict[str, Any]:
        """
        Get configuration for a specific country.
        
        Args:
            country_code: Two-letter country code (ISO 3166-1 alpha-2)
            
        Returns:
            Dict containing country-specific configuration
            
        Raises:
            requests.exceptions.RequestException: For request failures
            ValueError: If country_code is invalid
        """
        if not country_code or len(country_code) != 2:
            raise ValueError("country_code must be a valid 2-letter code")
            
        url = f"{self.base_url}/llu/config/country"
        return self._make_request('GET', url, self.DEFAULT_HEADERS, 
                                params={"country": country_code})
