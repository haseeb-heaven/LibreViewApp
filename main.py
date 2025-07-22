from dotenv import load_dotenv
import os
import sys
import time
import requests
from typing import Dict, Any
from client import LibreCGMClient

def load_environment() -> tuple[str, str]:
	"""Load credentials from .env file"""
	load_dotenv()
	email = os.getenv('EMAIL')
	password = os.getenv('PASSWORD')
	
	if not email or not password:
		print("Error: EMAIL and PASSWORD must be set in .env file")
		sys.exit(1)
	
	return email, password

def display_user_profile(user_data: Dict[str, Any]) -> None:
	"""Display user profile information"""
	print("\n=== User Profile ===")
	print(f"Name: {user_data.get('firstName', '')} {user_data.get('lastName', '')}")
	print(f"Email: {user_data.get('email', '')}")
	print("==================")

def display_patients(patients_data: Dict[str, Any]) -> None:
	"""Display patients information"""
	print("\n=== Patients List ===")
	for patient in patients_data.get('patients', []):
		print(f"Patient ID: {patient.get('id', '')}")
		print(f"Name: {patient.get('firstName', '')} {patient.get('lastName', '')}")
		print("-------------------")

def display_readings(readings_data: Dict[str, Any], patient_id: str) -> None:
	"""Display glucose readings for a patient"""
	print(f"\n=== Glucose Readings for Patient {patient_id} ===")
	for reading in readings_data.get('readings', []):
		print(f"Timestamp: {reading.get('timestamp', '')}")
		print(f"Value: {reading.get('value', '')} {reading.get('unit', '')}")
		print("-------------------")

def main():
	try:
		print("\n=== LibreView CGM Client ===")
		
		# Load credentials
		print("Loading environment variables...")
		email, password = load_environment()
		print("✓ Environment variables loaded successfully")
		
		# Initialize client
		print("\nInitializing client...")
		start_time = time.time()
		client = LibreCGMClient(email, password)
		print(f"✓ Client initialized ({time.time() - start_time:.2f}s)")
		
		# Authenticate
		print("\nAuthenticating with LibreView API...")
		start_time = time.time()
		try:
			client.authenticate()
			print(f"✓ Authentication successful ({time.time() - start_time:.2f}s)")
		except requests.exceptions.ConnectionError:
			print("✗ Connection failed. Please check your internet connection.")
			sys.exit(1)
		except requests.exceptions.Timeout:
			print("✗ Connection timed out. Server might be busy, please try again.")
			sys.exit(1)
		except requests.exceptions.RequestException as e:
			print(f"✗ Authentication failed: {str(e)}")
			sys.exit(1)
		
		# Get and display user profile
		print("\nFetching user profile...")
		start_time = time.time()
		try:
			user_data = client.get_current_user()
			print(f"✓ User profile retrieved ({time.time() - start_time:.2f}s)")
			display_user_profile(user_data)
		except Exception as error:
			print(f"✗ Failed to fetch user profile: {str(error)}")
			sys.exit(1)
		
		# Get and display patients
		print("\nFetching patient list...")
		start_time = time.time()
		try:
			patients_data = client.list_patients()
			print(f"✓ Patient list retrieved ({time.time() - start_time:.2f}s)")
			display_patients(patients_data)
		except Exception as error:
			print(f"✗ Failed to fetch patient list: {str(error)}")
			sys.exit(1)
		
		# Get readings for each patient
		patient_count = len(patients_data.get('patients', []))
		if patient_count == 0:
			print("\nNo patients found in your account.")
		else:
			print(f"\nFetching readings for {patient_count} patient(s)...")
			
		for index, patient in enumerate(patients_data.get('patients', []), 1):
			patient_id = patient.get('id')
			if patient_id:
				print(f"\nFetching readings for patient {index}/{patient_count} (ID: {patient_id})...")
				start_time = time.time()
				try:
					readings = client.get_patient_readings(patient_id, limit=10)
					print(f"✓ Readings retrieved ({time.time() - start_time:.2f}s)")
					display_readings(readings, patient_id)
				except requests.exceptions.RequestException as error:
					print(f"✗ Error fetching readings for patient {patient_id}: {str(error)}")
				except Exception as error:
					print(f"✗ Unexpected error for patient {patient_id}: {str(error)}")
		
		print("\n=== Session Complete ===")
		
	except KeyboardInterrupt:
		print("\n\nOperation cancelled by user.")
		sys.exit(1)
	except Exception as error:
		print(f"\n✗ Fatal error: {str(error)}")
		sys.exit(1)

if __name__ == "__main__":
	main()
