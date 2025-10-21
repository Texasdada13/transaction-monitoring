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
## Development Workflow

This project follows a simplified Git Flow workflow:

1. master - Production-ready code
2. develop - Main development branch
3. eature/* - Individual feature branches

### Contributing

1. Create a feature branch from develop: git checkout -b feature/your-feature-name
2. Make your changes and commit them
3. Push your feature branch to GitHub: git push -u origin feature/your-feature-name
4. Create a pull request to merge into the develop branch
5. After review, the feature will be merged into develop
6. Periodically, develop will be merged into master for releases
