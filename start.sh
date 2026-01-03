#!/bin/bash
# Auto-start script for Transaction Monitoring Dashboard

echo "Starting Transaction Monitoring System..."
echo ""

# Start FastAPI backend in background
echo "Starting FastAPI backend on port 8000..."
./venv/Scripts/python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready (with health check)
echo "Waiting for FastAPI backend to be ready..."
MAX_RETRIES=30
RETRIES=0

while [ $RETRIES -lt $MAX_RETRIES ]; do
    sleep 1
    RETRIES=$((RETRIES + 1))

    # Try health endpoint first, then root endpoint
    if curl -s -o /dev/null -w "" http://localhost:8000/health 2>/dev/null || \
       curl -s -o /dev/null -w "" http://localhost:8000/ 2>/dev/null; then
        echo "FastAPI backend is ready!"
        break
    fi

    echo "   Waiting... attempt $RETRIES/$MAX_RETRIES"
done

if [ $RETRIES -eq $MAX_RETRIES ]; then
    echo "WARNING: Backend may not be fully ready, proceeding anyway..."
fi

echo ""

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
echo "Transaction Monitoring System is running!"
echo "   - FastAPI Backend: http://localhost:8000"
echo "   - Streamlit Dashboard: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $STREAMLIT_PID; exit" INT
wait
