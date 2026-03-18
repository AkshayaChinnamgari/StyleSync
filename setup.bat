@echo off
REM StyleSync - Automated Setup Script for Windows

echo ========================================
echo StyleSync - Developer Setup
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] Python found: 
python --version

echo [OK] Node.js found:
node --version

REM Setup Backend
echo.
echo ========================================
echo Setting up Backend...
echo ========================================

cd backend

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt

echo [OK] Backend setup complete!

cd ..

REM Setup Frontend
echo.
echo ========================================
echo Setting up Frontend...
echo ========================================

cd frontend

if not exist node_modules (
    echo Installing Node.js dependencies...
    call npm install
) else (
    echo Node modules already installed
)

echo [OK] Frontend setup complete!

cd ..

REM Summary
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application:
echo.
echo Terminal 1 - Backend:
echo   cd backend
echo   venv\Scripts\activate.bat
echo   python main.py
echo.
echo Terminal 2 - Frontend:
echo   cd frontend
echo   npm start
echo.
echo Then open: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
pause
