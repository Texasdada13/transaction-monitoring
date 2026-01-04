@echo off
REM Auto-start script for Transaction Monitoring Dashboard (Windows)

echo Starting Transaction Monitoring System...
echo.

REM Set API URL for Streamlit
set API_BASE_URL=http://127.0.0.1:8347

REM Start FastAPI backend in new window
echo Starting FastAPI backend on port 8347...
start "FastAPI Backend" cmd /k "venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8347"

REM Wait for backend to be ready (with health check)
echo Waiting for FastAPI backend to be ready...
set RETRIES=0
set MAX_RETRIES=30

:CHECK_BACKEND
timeout /t 1 /nobreak >nul
set /a RETRIES+=1

REM Try to connect to the health endpoint
curl -s -o nul -w "" http://127.0.0.1:8347/health >nul 2>&1
if %errorlevel% equ 0 (
    echo FastAPI backend is ready!
    goto BACKEND_READY
)

REM Also try the root endpoint as fallback
curl -s -o nul -w "" http://127.0.0.1:8347/ >nul 2>&1
if %errorlevel% equ 0 (
    echo FastAPI backend is ready!
    goto BACKEND_READY
)

if %RETRIES% lss %MAX_RETRIES% (
    echo    Waiting... attempt %RETRIES%/%MAX_RETRIES%
    goto CHECK_BACKEND
)

echo WARNING: Backend may not be fully ready, proceeding anyway...

:BACKEND_READY
echo.

REM Start Streamlit dashboard in new window
echo Starting Streamlit dashboard on port 8348...
start "Streamlit Dashboard" cmd /k "set API_BASE_URL=http://127.0.0.1:8347 && venv\Scripts\python.exe -m streamlit run streamlit_app\app.py --server.port 8348"

REM Wait for Streamlit to start
timeout /t 3 /nobreak >nul

REM Open browser
echo Opening browser...
start http://127.0.0.1:8348

echo.
echo Transaction Monitoring System is running!
echo   - FastAPI Backend: http://127.0.0.1:8347
echo   - Streamlit Dashboard: http://127.0.0.1:8348
echo.
echo Close the terminal windows to stop the services.
