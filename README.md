# LibreApp

A Python client application for interacting with the LibreView CGM API.

## Features

- Authentication with LibreView API
- User profile and account management
- Patient connections handling
- Glucose data retrieval
- Comprehensive logging system
- Sensitive data masking

## Setup

1. Create a `.env` file with your credentials:
```
EMAIL=your.email@example.com
PASSWORD=your_password
```

2. Install dependencies:
```bash
pip install requests python-dotenv
```

## Usage

Run the main application:
```bash
python main.py
```

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
