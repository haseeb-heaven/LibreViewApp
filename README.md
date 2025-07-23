# LibreApp - Medical Technology API Library

A professional-grade Python library for interfacing with LibreView Continuous Glucose Monitoring (CGM) systems. This library is designed for medical technology integration, following industry standards for reliability, security, and data handling.

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Versions](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10-blue)]()
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)]()

## Medical Technology Integration

This library is specifically designed for medical technology integration, featuring:

- **SOLID Principles**: Clean, modular, and maintainable code architecture
- **Security First**: Built-in sensitive data masking and secure communication
- **Audit Logging**: Comprehensive logging for medical compliance
- **Error Handling**: Robust error handling for medical-grade reliability
- **Type Safety**: Full type hints and runtime type checking
- **API Versioning**: Support for multiple API versions
- **Regional Compliance**: Built-in regional server support

## Repository Structure

This repository maintains two main branches:
- `develop` - Development branch for active development and new features
- `main` - Stable release branch for production deployments

All development work should be done in feature branches branched from `develop` and merged back via pull requests.

## API Features & Endpoints

### Authentication
```python
from client import LibreCGMClient, ApiConfig

# Create configuration (optional, has defaults)
config = ApiConfig(
    version="4.7",
    product="ios",
    region="us",
    base_url="https://libreview-proxy.onrender.com"
)

# Initialize client with configuration
client = LibreCGMClient(
    email="user@example.com",
    password="****",
    config=config  # Optional, will use defaults if not provided
)

# Authenticate
auth_data = client.authenticate()
```
- Endpoint: `/llu/auth/login`
- Method: POST
- Features:
  - Automatic regional server detection
  - Terms of service handling
  - Secure token management
  - Rate limiting protection

### User Management
```python
# Get user profile
user_data = client.get_current_user()

# Get account details
account_data = client.get_account()
```
- Endpoints:
  - `/user` (GET) - User profile
  - `/account` (GET) - Account details
- Features:
  - Sensitive data masking
  - Detailed user information
  - Account status tracking

### Patient Connections
```python
# List all connections
connections = client.list_connections()

# Get patient graph data
graph_data = client.get_patient_graph(patient_id="...")
```
- Endpoints:
  - `/llu/connections` (GET) - List connections
  - `/llu/connections/{id}/graph` (GET) - Patient glucose data
  - `/llu/connections/{id}/logbook` (GET) - Patient logbook
- Features:
  - Real-time glucose data
  - Historical data access
  - Trend analysis

### Glucose Data Analysis
```python
# Get patient glucose data
glucose_data = client.get_patient_graph(patient_id)

# Get logbook entries
logbook = client.get_patient_logbook(patient_id)
```
- Data Points:
  - Current glucose level
  - Historical trends
  - Time-series analysis
  - Alerts and warnings

### Notification Management
```python
settings = client.get_notification_settings(connection_id)
```
- Endpoint: `/llu/notifications/settings/{id}`
- Features:
  - Alert configuration
  - Threshold management
  - Notification preferences

### Regional Configuration
```python
config = client.get_country_config(country_code)
```
- Endpoint: `/llu/config/country`
- Features:
  - Regional settings
  - Compliance rules
  - Unit preferences

## Technical Features

### SOLID Design
- **Single Responsibility**: Each class handles one aspect
- **Open/Closed**: Extensible through protocols
- **Liskov Substitution**: Proper inheritance hierarchy
- **Interface Segregation**: Clean protocol definitions
- **Dependency Inversion**: Dependency injection ready

### Security Features
- Automatic token management
- Sensitive data masking
- Secure communication
- Rate limiting protection
- Audit logging

### Data Handling
- Type-safe operations
- Input validation
- Error handling
- Response parsing
- Data transformation

## Setup

1. Clone the repository:
```bash
git clone https://github.com/haseeb-heaven/LibreViewApp.git
cd LibreViewApp
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Copy the example environment file and configure it:
```bash
cp .env.example .env
```

Then edit the `.env` file with your credentials:
```bash
# Required credentials
LIBRE_EMAIL=your.email@example.com      # Your LibreView account email
LIBRE_PASSWORD=your_password            # Your LibreView account password

# Optional API configuration (defaults shown)
LIBRE_VERSION=4.7                       # API version to use (default: 4.7)
LIBRE_PRODUCT=ios                       # Product type (ios or android, default: ios)
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

This will install all required packages:
- requests: For HTTP client functionality
- python-dotenv: For environment variable management
- typing-extensions: For enhanced type hints
- black: For code formatting
- pytest: For unit testing
- mypy: For static type checking

## Usage

1. Run the main application:
```bash
python main.py
```

2. The application will:
   - Authenticate with LibreView API
   - Retrieve user profile and account information
   - List all patient connections
   - Fetch and display glucose readings for each patient

3. Logs can be found in:
   - Console: Shows user-friendly progress and status
   - `logs/libreview_YYYYMMDD.log`: Contains detailed debug information

## API Documentation

This application uses the unofficial LibreView API as documented at [libreview-unofficial.stoplight.io](https://libreview-unofficial.stoplight.io/). The API provides:

- Regional server support
- Authentication and token management
- User profile and account management
- Patient connection handling
- Glucose data retrieval
- Real-time CGM data access

Note: This is a community-driven, unofficial implementation and is not affiliated with Abbott Diabetes Care, Inc.

## Contributing

1. Fork the repository
2. Create your feature branch from `develop`: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request to the `develop` branch

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Changelog

### Version 1.0.1 (2025-07-23)

API and Code Quality Update:
- Refactored codebase to follow SOLID principles
- Added dependency injection with ApiConfig class
- Implemented Protocol-based interfaces for better modularity
- Enhanced error handling with detailed error messages
- Updated OpenAPI specification with improved examples
- Added comprehensive type hints and documentation
- Improved logging system with better data masking
- Added requirements.txt with development dependencies
- Created .env.example for better configuration management

### Version 1.0.0 (2025-07-23)

Initial release with following features:
- Implemented robust LibreView API client
- Added comprehensive logging with dual loggers (console and file)
- Implemented sensitive data masking
- Added user profile and account management
- Added patient connections handling
- Added glucose data retrieval
- Added error handling and session management
