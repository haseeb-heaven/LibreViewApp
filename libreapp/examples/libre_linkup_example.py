"""Example usage of the LibreLinkUp client."""
from dotenv import load_dotenv
import os
import sys
import time
import json
from typing import Dict, Any, Optional
from libreapp.clients.libre_linkup import LibreLinkUpClient, LibreLinkUpConfig
from libreapp.utils.data_masking import DefaultDataMasker
from libreapp.utils.logger import setup_logger

# Set up loggers
console_log, file_log = setup_logger()

def load_environment() -> tuple[str, str, str, str]:
    """Load credentials from .env file."""
    file_log.debug("Loading environment variables from .env file")
    load_dotenv()

    username = os.getenv("LIBRE_USERNAME")
    password = os.getenv("LIBRE_PASSWORD")
    version = os.getenv("LIBRE_VERSION", "4.9.0")  # LibreLinkUp uses a different default version
    product = os.getenv("LIBRE_PRODUCT", "llu.ios")  # Default to iOS client

    if not username or not password:
        error_msg = "Error: LIBRE_USERNAME and LIBRE_PASSWORD must be set in .env file"
        file_log.error(error_msg)
        console_log.error(error_msg)
        sys.exit(1)
    
    file_log.debug(f"Loaded credentials for username: {username[:3]}...{username[-8:]}")
    file_log.debug(f"Using version: {version}, product: {product}")
    return username, password, version, product

def display_auth_info(auth_data: Dict[str, Any]) -> None:
    """Display authentication information."""
    section = "=== Authentication Information ==="
    console_log.info(f"\n{section}")
    
    # Log full auth data to file (with sensitive data masked)
    data_masker = DefaultDataMasker()
    file_log.debug(f"Full auth response: {json.dumps(data_masker.mask_sensitive_data(auth_data), indent=2)}")
    
    if auth_data.get('token'):
        console_log.info("✓ Authentication successful")
        console_log.info(f"User ID: {auth_data.get('userId', 'N/A')}")
        console_log.info(f"Expires In: {auth_data.get('expiresIn', 'N/A')} seconds")
    else:
        console_log.warning("✗ Authentication failed")
        file_log.warning("Authentication failed - no token received")
    
    console_log.info("=" * len(section))

def display_connections(connections_data: Dict[str, Any]) -> None:
    """Display patient connections information."""
    print("\n=== Patient Connections ===")
    connections = connections_data.get('data', [])
    if not connections:
        print("No patient connections found")
        return
    
    for conn in connections:
        print(f"\nPatient ID: {conn.get('patientId', 'N/A')}")
        print(f"Name: {conn.get('firstName', '')} {conn.get('lastName', '')}")
        print("-" * 20)

def display_glucose_data(graph_data: Dict[str, Any], connection_id: str) -> None:
    """Display glucose readings from graph data."""
    print(f"\n=== Glucose Readings for Connection {connection_id} ===")
    
    # Log the full response structure for debugging
    data_masker = DefaultDataMasker()
    file_log.debug(f"Full graph data response:\n{json.dumps(data_masker.mask_sensitive_data(graph_data), indent=2)}")
    
    data = graph_data.get('data', [])
    if not data:
        print("No glucose data available")
        return
        
    print("\nRecent Readings:")
    for reading in data:
        print(
            f"Time: {reading.get('date', 'N/A')} - "
            f"Value: {reading.get('Value', 'N/A')} "
            f"{'HIGH' if reading.get('isHigh') else 'LOW' if reading.get('isLow') else ''} "
            f"Trend: {reading.get('trend', 'N/A')}"
        )
    print("=" * 30)

def main():
    """Main function to orchestrate the LibreLinkUp client operations."""
    session_start = time.time()
    file_log.info("Starting new LibreLinkUp Client session")
    
    try:
        console_log.info("\n=== LibreLinkUp CGM Client ===")
        
        # Load credentials
        console_log.info("Loading environment variables...")
        start_time = time.time()
        username, password, version, product = load_environment()
        duration = time.time() - start_time
        console_log.info(f"✓ Environment variables loaded ({duration:.2f}s)")
        
        # Initialize client with configuration
        console_log.info("\nInitializing client...")
        start_time = time.time()
        config = LibreLinkUpConfig(
            client_version=version,
            product=product
        )
        client = LibreLinkUpClient(
            username=username,
            password=password,
            config=config,
            data_masker=DefaultDataMasker()
        )
        duration = time.time() - start_time
        console_log.info(f"✓ Client initialized ({duration:.2f}s)")
        
        # Authenticate
        print("\nAuthenticating with LibreLinkUp API...")
        start_time = time.time()
        try:
            auth_data = client.authenticate()
            print(f"✓ Authentication successful ({time.time() - start_time:.2f}s)")
            display_auth_info(auth_data)
        except Exception as auth_error:
            print(f"✗ Authentication failed: {auth_error}")
            sys.exit(1)
        
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
                    connection_id = connection.get('patientId')
                    if connection_id:
                        print(f"\nFetching glucose data for connection {connection_id}...")
                        start_time = time.time()
                        try:
                            graph_data = client.get_connection_graph(connection_id)
                            print(f"✓ Glucose data retrieved ({time.time() - start_time:.2f}s)")
                            display_glucose_data(graph_data, connection_id)
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
