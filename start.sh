#!/bin/bash
# Auto-start script for Transaction Monitoring Dashboard

echo "Starting Transaction Monitoring System..."
echo ""

# Start FastAPI backend in background
echo "Starting FastAPI backend on port 8000..."
./venv/Scripts/python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start Streamlit dashboard in background
echo "Starting Streamlit dashboard on port 8501..."
./venv/Scripts/python.exe -m streamlit run streamlit_app/app.py &
STREAMLIT_PID=$!

# Wait for Streamlit to start
sleep 3

# Open browser
echo "Opening browser..."
start http://localhost:8501

echo ""
echo "✅ Transaction Monitoring System is running!"
echo "   - FastAPI Backend: http://localhost:8000"
echo "   - Streamlit Dashboard: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $STREAMLIT_PID; exit" INT
wait
