@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title ZhiPinYunTu - Dev Launcher
color 0A

echo ========================================
echo        ZhiPinYunTu Project Launcher
echo   LLM-based Intelligent Recruitment
echo ========================================
echo.

cd /d "%~dp0"

:: ===== Step 1: Check Python =====
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo       [ERROR] Python not found! Please install Python 3.10+
    goto :end_error
)
echo       Python OK.

:: ===== Step 2: Check backend dependencies =====
echo [2/4] Checking backend dependencies...
cd /d "%~dp0backend"

python -c "import fastapi, uvicorn, sqlalchemy, openai, loguru" >nul 2>&1
if errorlevel 1 (
    echo       Installing Python packages from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo       [ERROR] pip install failed!
        goto :end_error
    )
    echo       Python packages installed.
) else (
    echo       Python packages OK.
)

if not exist ".env.dev" (
    if exist ".env.example" (
        echo       .env.dev not found, copying from .env.example...
        copy ".env.example" ".env.dev" >nul
    ) else (
        echo       [WARNING] .env.dev not found!
    )
)

if not exist "uploads" (
    mkdir uploads
    echo       Created uploads directory.
)

:: ===== Step 3: Check frontend dependencies =====
echo [3/4] Checking frontend dependencies...
cd /d "%~dp0frontend"

set need_npm=0
if not exist "node_modules" (
    set need_npm=1
) else (
    if not exist "node_modules\jspdf" set need_npm=1
    if not exist "node_modules\exceljs" set need_npm=1
    if not exist "node_modules\html2canvas" set need_npm=1
    if not exist "node_modules\echarts" set need_npm=1
)

if "!need_npm!"=="1" (
    echo       Installing npm packages...
    call npm install --legacy-peer-deps
    if errorlevel 1 (
        echo       [ERROR] npm install failed!
        goto :end_error
    )
    echo       npm packages installed.
) else (
    echo       npm packages OK.
)

:: ===== Step 4: Start services =====
echo.
echo [4/4] Starting services...
echo.

:: Kill any existing process on port 8001
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8001" ^| findstr "LISTENING"') do (
    echo       Killing existing process on port 8001 PID: %%a
    taskkill /f /pid %%a >nul 2>&1
)

:: Start backend in background (same window)
echo [Backend] Starting FastAPI on http://127.0.0.1:8001 ...
cd /d "%~dp0backend"
set PYTHONPATH=.
start /b python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

:: Wait for backend to be ready
echo [Backend] Waiting for service to be ready...
set wait_count=0

:wait_backend
timeout /t 2 /nobreak >nul
set /a wait_count+=1
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/api/v1/health', timeout=2)" >nul 2>&1
if not errorlevel 1 goto backend_ready
if !wait_count! lss 10 (
    echo [Backend] Still starting... (!wait_count!/10)
    goto wait_backend
)
echo [Backend] [WARNING] Backend not responding after 20s.
echo [Backend] It may still be initializing. Check http://127.0.0.1:8001/docs
goto start_frontend

:backend_ready
echo [Backend] Service is ready!

:start_frontend
echo.
echo [Frontend] Starting Vite on http://localhost:5174 ...
cd /d "%~dp0frontend"
echo.
echo ========================================
echo  Backend API:  http://127.0.0.1:8001
echo  API Docs:     http://127.0.0.1:8001/docs
echo  Frontend:     http://localhost:5174
echo ========================================
echo.
echo  Press Ctrl+C to stop all services.
echo  Answer 'Y' to terminate batch job.
echo.

call npm run dev

:: ===== Cleanup =====
echo.
echo [Cleanup] Stopping backend...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8001" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [Cleanup] All services stopped.
goto :end_ok

:end_error
echo.
echo [ERROR] Startup failed. Please check the messages above.
echo.

:end_ok
pause
