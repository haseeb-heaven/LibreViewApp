from dotenv import load_dotenv
import os
import sys
import time
import json
from typing import Dict, Any
from client import LibreCGMClient, ApiConfig
from logger_config import setup_logger

# Set up loggers
console_log, file_log = setup_logger()

def log_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive data before logging."""
    if not isinstance(data, dict):
        return data
        
    masked_data = data.copy()
    sensitive_fields = ['token', 'email', 'password', 'firstName', 'lastName', 'Authorization']
    
    for key, value in masked_data.items():
        if key in sensitive_fields and value:
            masked_data[key] = f"{value[:4]}...{value[-4:]}" if len(str(value)) > 8 else "****"
        elif isinstance(value, dict):
            masked_data[key] = log_sensitive_data(value)
        elif isinstance(value, list):
            masked_data[key] = [log_sensitive_data(item) if isinstance(item, dict) else item for item in value]
            
    return masked_data

def load_environment() -> tuple[str, str]:
    """Load credentials from .env file."""
    file_log.debug("Loading environment variables from .env file")
    load_dotenv()

    email = os.getenv("LIBRE_EMAIL")
    password = os.getenv("LIBRE_PASSWORD")

    if not email or not password:
        error_msg = "Error: EMAIL and PASSWORD must be set in .env file"
        file_log.error(error_msg)
        console_log.error(error_msg)
        sys.exit(1)
    
    file_log.debug(f"Loaded credentials for email: {email[:3]}...{email[-8:]}")
    return email, password

def display_auth_info(auth_data: Dict[str, Any]) -> None:
    """Display authentication information."""
    section = "=== Authentication Information ==="
    console_log.info(f"\n{section}")
    
    # Log full auth data to file (with sensitive data masked)
    file_log.debug(f"Full auth response: {json.dumps(log_sensitive_data(auth_data), indent=2)}")
    
    if auth_data.get('status') == 0:  # Success
        console_log.info("✓ Authentication successful")
        ticket = auth_data.get('data', {}).get('authTicket', {})
        expires = time.ctime(ticket.get('expires', 0))
        duration = ticket.get('duration', 0) / 3600
        
        console_log.info(f"Token expires: {expires}")
        console_log.info(f"Token duration: {duration:.1f} hours")
        
        # Log detailed ticket info to file
        file_log.debug(f"Auth ticket details:\n"
                      f"Expires: {expires}\n"
                      f"Duration: {duration:.1f} hours\n"
                      f"Token: {ticket.get('token', '')}")
    else:
        status = auth_data.get('status')
        console_log.warning(f"Status: {status}")
        file_log.warning(f"Authentication returned non-zero status: {status}")
    
    console_log.info("=" * len(section))

def display_user_info(user_data: Dict[str, Any]) -> None:
    """Display user profile information."""
    print("\n=== User Profile ===")
    user = user_data.get('data', {}).get('user', {})
    print(f"Name: {user.get('firstName', '')} {user.get('lastName', '')}")
    print(f"Email: {user.get('email', '')}")
    print(f"Country: {user.get('country', '')}")
    print(f"Account Type: {user.get('accountType', '')}")
    print("=" * 30)

def display_account_info(account_data: Dict[str, Any]) -> None:
    """Display account information."""
    print("\n=== Account Information ===")
    account = account_data.get('data', {}).get('user', {})
    print(f"Last Login: {time.ctime(account.get('lastLogin', 0))}")
    print(f"Account Created: {time.ctime(account.get('created', 0))}")
    print("=" * 30)

def display_connections(connections_data: Dict[str, Any]) -> None:
    """Display patient connections information."""
    print("\n=== Patient Connections ===")
    connections = connections_data.get('data', [])
    if not connections:
        print("No patient connections found")
        return
    
    for conn in connections:
        print(f"\nPatient ID: {conn.get('id', 'N/A')}")
        print(f"Name: {conn.get('firstName', '')} {conn.get('lastName', '')}")
        if conn.get('dateOfBirth'):
            print(f"Date of Birth: {conn.get('dateOfBirth')}")
        print("-" * 20)

def display_glucose_data(graph_data: Dict[str, Any], patient_id: str) -> None:
    """Display glucose readings from graph data."""
    print(f"\n=== Glucose Readings for Patient {patient_id} ===")
    
    # Log the full response structure for debugging
    file_log.debug(f"Full graph data response for patient {patient_id}:\n{json.dumps(log_sensitive_data(graph_data), indent=2)}")
    
    data = graph_data.get('data', {})
    file_log.debug(f"Data object structure:\n{json.dumps(data, indent=2)}")
    
    # Display connection info
    connection = data.get('connection', {})
    print(f"Target Range: {connection.get('targetLow', 'N/A')} - {connection.get('targetHigh', 'N/A')}")
    
    # Display current reading if available
    measurement = data.get('glucoseMeasurement')
    if measurement:
        print("\nLatest Reading:")
        print(f"Time: {measurement.get('Timestamp', 'N/A')}")
        print(f"Value: {measurement.get('Value', 'N/A')} {measurement.get('GlucoseUnits', 'N/A')}")
        print(f"Trend: {measurement.get('TrendMessage', 'N/A')}")
    
    # Display graph data points
    readings = data.get('graphData', [])
    if readings:
        print("\nRecent Readings:")
        for reading in readings:  # Show all readings
            if reading.get('Value'):
                print(f"Time: {reading.get('Timestamp', 'N/A')} - Value: {reading.get('Value')} {reading.get('GlucoseUnits', 'N/A')}")
    print("=" * 30)

def main():
    """Main function to orchestrate the LibreView client operations."""
    session_start = time.time()
    file_log.info("Starting new LibreView CGM Client session")
    
    try:
        console_log.info("\n=== LibreView CGM Client ===")
        
        # Load credentials
        console_log.info("Loading environment variables...")
        start_time = time.time()
        email, password = load_environment()
        duration = time.time() - start_time
        console_log.info(f"✓ Environment variables loaded ({duration:.2f}s)")
        file_log.debug(f"Environment variables loaded in {duration:.2f}s")
        
        # Initialize client with configuration
        console_log.info("\nInitializing client...")
        start_time = time.time()
        config = ApiConfig(
            version=os.getenv("LIBRE_VERSION", "4.7"),
            product="llu." + os.getenv("LIBRE_PRODUCT", "ios")
        )
        client = LibreCGMClient(
            email=email,
            password=password,
            config=config
        )
        duration = time.time() - start_time
        console_log.info(f"✓ Client initialized ({duration:.2f}s)")
        file_log.debug(f"Client initialized with email: {email[:3]}...{email[-8:]} in {duration:.2f}s")
        
        # Authenticate
        print("\nAuthenticating with LibreView API...")
        start_time = time.time()
        try:
            auth_data = client.authenticate()
            print(f"✓ Authentication successful ({time.time() - start_time:.2f}s)")
            display_auth_info(auth_data)
        except Exception as auth_error:
            print(f"✗ Authentication failed: {auth_error}")
            sys.exit(1)
        
        # Get and display user profile
        print("\nFetching user profile...")
        start_time = time.time()
        try:
            user_data = client.get_current_user()
            print(f"✓ User profile retrieved ({time.time() - start_time:.2f}s)")
            display_user_info(user_data)
        except Exception as error:
            print(f"✗ Failed to fetch user profile: {error}")
        
        # Get and display account info
        print("\nFetching account information...")
        start_time = time.time()
        try:
            account_data = client.get_account()
            print(f"✓ Account information retrieved ({time.time() - start_time:.2f}s)")
            display_account_info(account_data)
        except Exception as error:
            print(f"✗ Failed to fetch account information: {error}")
        
        # Get and display connections
        print("\nFetching patient connections...")
        start_time = time.time()
        try:
            connections_data = client.list_connections()
            print(f"✓ Connections retrieved ({time.time() - start_time:.2f}s)")
            display_connections(connections_data)
            
            # Get glucose data for each connection
            connections = connections_data.get('data', [])
            if connections:
                for connection in connections:
                    patient_id = connection.get('patientId')
                    if patient_id:
                        print(f"\nFetching glucose data for patient {patient_id}...")
                        start_time = time.time()
                        try:
                            graph_data = client.get_patient_graph(patient_id)
                            print(f"✓ Glucose data retrieved ({time.time() - start_time:.2f}s)")
                            display_glucose_data(graph_data, patient_id)
                        except Exception as error:
                            print(f"✗ Failed to fetch glucose data: {error}")
        except Exception as error:
            print(f"✗ Failed to fetch connections: {error}")
        
        total_duration = time.time() - session_start
        console_log.info("\n=== Session Complete ===")
        file_log.info(f"Session completed successfully in {total_duration:.2f}s")
        
    except KeyboardInterrupt:
        console_log.warning("\n\nOperation cancelled by user")
        file_log.warning("Session terminated by user interrupt")
        sys.exit(1)
    except Exception as error:
        console_log.error(f"\n✗ Fatal error: {error}")
        file_log.exception("Fatal error occurred during session:")
        sys.exit(1)
    finally:
        file_log.info("=" * 80)  # Session separator in log file

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        file_log.critical(f"Unhandled exception: {str(error)}", exc_info=True)
        raise
