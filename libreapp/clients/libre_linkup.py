"""
LibreLinkUp Client - Medical Technology API Library
------------------------------------------------
Client implementation for the LibreLinkUp CGM sharing service.
"""

import requests
from typing import Any, Dict, Optional, Protocol
from dataclasses import dataclass
from ..utils.logger import setup_logger
from ..utils.data_masking import DataMasker

# Get loggers
console_log, file_log = setup_logger()

@dataclass
class LibreLinkUpConfig:
    """Configuration for LibreLinkUp API"""
    base_url: str = "https://api.libreview.io"
    client_version: str = "4.9.0"
    product: str = "llu.ios"  # Default product type
    timeout: int = 30

class LibreLinkUpClient:
    """Client implementation for the LibreLinkUp API"""

    def __init__(self, username: str, password: str, 
                 config: Optional[LibreLinkUpConfig] = None,
                 data_masker: Optional[DataMasker] = None):
        """
        Initialize the LibreLinkUp client.
        
        Args:
            username: User's email address
            password: User's password
            config: API configuration (optional)
            data_masker: Data masking implementation (optional)
        """
        self.config = config or LibreLinkUpConfig()
        self.data_masker = data_masker
        
        self.username = username
        self.password = password
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None

    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an HTTP request to the LibreLinkUp API"""
        url = f"{self.config.base_url}{endpoint}"
        headers = {
            "version": self.config.client_version,
            "product": self.config.product
        }
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            
        try:
            # Log request details for debugging
            file_log.debug(f"Request URL: {url}")
            file_log.debug(f"Request Headers: {headers}")
            file_log.debug(f"Request Data: {data}")

            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=self.config.timeout
            )
            
            if not response.ok:
                file_log.error(f"Response Status: {response.status_code}")
                file_log.error(f"Response Text: {response.text}")
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            file_log.error(f"Request failed: {str(e)}")
            raise

    def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with the LibreLinkUp API.
        
        Returns:
            Dict containing authentication response data
        """
        payload = {
            "username": self.username,
            "password": self.password,
            "clientVersion": self.config.client_version
        }
        
        data = self._make_request('POST', '/llu/auth/login', payload)
        self.token = data.get('token')
        self.user_id = data.get('userId')
        return data

    def list_connections(self) -> Dict[str, Any]:
        """
        List all patient connections.
        
        Returns:
            Dict containing list of connections
        """
        return self._make_request('GET', '/llu/connections')

    def get_connection_graph(self, connection_id: str) -> Dict[str, Any]:
        """
        Get CGM graph data for a connection.
        
        Args:
            connection_id: The ID of the connection
            
        Returns:
            Dict containing CGM graph data
        """
        if not connection_id:
            raise ValueError("connection_id cannot be empty")
            
        return self._make_request('GET', f'/llu/connections/{connection_id}/graph')
