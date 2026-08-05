@echo off
chcp 65001 >nul 2>&1
title ZhiPinYunTu - Launcher
color 0A

echo ========================================
echo        ZhiPinYunTu Project Launcher
echo   LLM-based Intelligent Recruitment
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Checking frontend dependencies...
cd /d "%~dp0frontend"
if not exist "node_modules\jspdf" (
  echo       jspdf not found, installing dependencies...
  call npm install --legacy-peer-deps
  if errorlevel 1 (
    echo       [ERROR] npm install failed! Please run manually: npm install --legacy-peer-deps
    pause
    exit /b 1
  )
  echo       Dependencies installed.
) else (
  if not exist "node_modules\exceljs" (
    echo       exceljs not found, installing dependencies...
    call npm install --legacy-peer-deps
    if errorlevel 1 (
      echo       [ERROR] npm install failed! Please run manually: npm install --legacy-peer-deps
      pause
      exit /b 1
    )
    echo       Dependencies installed.
  ) else (
    echo       Dependencies OK.
  )
)

echo.
echo [2/3] Starting Backend (FastAPI :8001)...
start "ZhiPinYunTu-Backend" cmd /k "cd /d %~dp0backend && set PYTHONPATH=. && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"

timeout /t 3 /nobreak >nul

echo [3/3] Starting Frontend (Vite :5174)...
start "ZhiPinYunTu-Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo  Project is starting...
echo  Backend API:  http://127.0.0.1:8001
echo  API Docs:     http://127.0.0.1:8001/docs
echo  Frontend:     http://localhost:5174
echo ========================================
echo.
echo  Close the corresponding window to stop.
echo  Press any key to close this launcher...
pause >nul
