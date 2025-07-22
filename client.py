import requests
from typing import Any, Dict, Optional
import time

class LibreCGMClient:
	"""
	Minimal client for the LibreView API (via the libreview-proxy).
	"""

	DEFAULT_HEADERS = {
		"version": "4.7",
		"product": "llu.android"
	}

	def __init__(self, email: str, password: str, 
				 base_url: str = "https://libreview-proxy.onrender.com/api/v1",
				 region: str = "us"):
		self.base_url = base_url.rstrip('/')
		self.email = email
		self.password = password
		self.token: Optional[str] = None
		self.region = region
		self.timeout = 30  # seconds

	def authenticate(self) -> str:
		"""
		Obtain a bearer token by logging in.
		
		According to the API spec, this endpoint handles:
		1. Initial login
		2. Regional redirects
		3. Terms of use acceptance
		"""
		url = f"{self.base_url}/llu/auth/login"
		payload = {"email": self.email, "password": self.password}
		response = requests.post(url, json=payload, headers=self.DEFAULT_HEADERS, timeout=self.timeout)
		response.raise_for_status()
		data = response.json()
		# The API returns {"token": "<JWT‑token>"}
		self.token = data["token"]
		return self.token

	def _headers(self) -> Dict[str, str]:
		if not self.token:
			raise RuntimeError("Client is not authenticated. Call .authenticate() first.")
		headers = self.DEFAULT_HEADERS.copy()
		headers["Authorization"] = f"Bearer {self.token}"
		return headers

	def get_current_user(self) -> Dict[str, Any]:
		"""
		Fetch the authenticated user's profile.
		
		Returns user data according to the /user endpoint specification.
		"""
		url = f"{self.base_url}/user"
		resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
		resp.raise_for_status()
		return resp.json()

	def list_patients(self) -> Dict[str, Any]:
		"""
		Retrieve all patients under this account.
		
		Uses the /llu/connections endpoint to get patient connections.
		"""
		url = f"{self.base_url}/llu/connections"
		resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
		resp.raise_for_status()
		return resp.json()

	def get_patient_readings(self, patient_id: str, limit: int = 100) -> Dict[str, Any]:
		"""
		Fetch the latest glucose readings for a given patient.
		
		Uses the /llu/connections/{patientId}/graph endpoint for glucose data.
		"""
		url = f"{self.base_url}/llu/connections/{patient_id}/graph"
		resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
		resp.raise_for_status()
		return resp.json()

