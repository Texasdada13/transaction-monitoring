@echo off
REM Auto-start script for Transaction Monitoring Dashboard (Windows)

echo Starting Transaction Monitoring System...
echo.

REM Start FastAPI backend in new window
echo Starting FastAPI backend on port 8000...
start "FastAPI Backend" cmd /k "venv\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start Streamlit dashboard in new window
echo Starting Streamlit dashboard on port 8501...
start "Streamlit Dashboard" cmd /k "venv\Scripts\python.exe -m streamlit run streamlit_app\app.py"

REM Wait for Streamlit to start
timeout /t 3 /nobreak >nul

REM Open browser
echo Opening browser...
start http://localhost:8501

echo.
echo Transaction Monitoring System is running!
echo   - FastAPI Backend: http://localhost:8000
echo   - Streamlit Dashboard: http://localhost:8501
echo.
echo Close the terminal windows to stop the services.
