# LibreApp

A Python client application for interacting with the LibreView CGM API. This application uses the unofficial LibreView API documentation available at [LibreView Unofficial API](https://libreview-unofficial.stoplight.io/).

## Features

- Authentication with LibreView API with regional support
- User profile and account management
- Patient connections handling
- Glucose data retrieval and visualization
- Comprehensive dual logging system:
  - Console: Clean, user-friendly output (INFO level and above)
  - File: Detailed debug logs including API interactions
- Sensitive data masking for security
- Regional server support
- Automatic token management
- Error handling and retry logic

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd LibreApp
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Create a `.env` file with your credentials:
```bash
EMAIL=your.email@example.com
PASSWORD=your_password
```

4. Install dependencies:
```bash
pip install requests python-dotenv
```

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

## Changelog

### Version 1.0.0 (2025-07-23)

Initial release with following features:
- Implemented robust LibreView API client
- Added comprehensive logging with dual loggers (console and file)
- Implemented sensitive data masking
- Added user profile and account management
- Added patient connections handling
- Added glucose data retrieval
- Added error handling and session management
