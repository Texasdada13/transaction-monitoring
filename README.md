# Transaction Monitoring System

A real-time transaction monitoring and fraud detection system for financial institutions.

## Features

- Automated transaction processing with dynamic risk assessment
- Rule-based and ML-powered risk scoring
- Cost-benefit optimized workflow
- Clear explainability for compliance
- Administrative dashboard for monitoring and configuration

## Future Enhancements

- Machine learning model integration for advanced fraud detection
- API documentation with Swagger
- Performance optimization for high-volume transactions

## Setup

### Prerequisites

- Python 3.9+
- Pip

### Installation

1. Clone the repository
2. Create a virtual environment:
`
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
`
3. Install dependencies:
`
   pip install -r requirements.txt
`

### Configuration

Edit the .env file to configure:
- Database settings
- API port
- Dashboard port
- Default threshold values

## Running the System

Start both the API and dashboard with:
`
python run.py
`

This will start:
- FastAPI server on port 8000 (default)
- Streamlit dashboard on port 8501 (default)
