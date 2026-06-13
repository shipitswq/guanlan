@echo off
echo ========================================
echo  观澜——学习·分析·模拟交易
echo  GuanLan——reading the waves.
echo ========================================
echo.
echo Step 1: Starting Backend (port 8000)...
start "GuanLan-Backend" cmd /c "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo Waiting for backend...
timeout /t 5 /nobreak >nul

echo Step 2: Starting Frontend (port 3000)...
start "GuanLan-Frontend" cmd /c "cd /d %~dp0frontend && npx next dev --port 3000"

echo.
echo ========================================
echo  观澜 / GuanLan
echo  Backend API:  http://localhost:8000
echo  API Docs:     http://localhost:8000/docs
echo  Frontend UI:  http://localhost:3000
echo ========================================
echo.
echo Frontend will take ~30s for first compile.
pause
