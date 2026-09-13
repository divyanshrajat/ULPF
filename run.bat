@echo off
echo Starting setup and run...

:: 1. Check for Docker Compose
IF EXIST "docker-compose.yml" (
    echo Found docker-compose.yml. Starting with Docker...
    docker-compose up --build
    exit /b
)

echo Starting natively...

:: 2. Start Backend in a new terminal window
IF EXIST "backend\" (
    echo Setting up backend...
    :: Create venv, activate it, install requirements, and run uvicorn
    start "Backend Server" cmd /k "cd backend && if not exist venv python -m venv venv && call venv\Scripts\activate && pip install -r requirements.txt && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
) ELSE (
    echo Backend directory not found!
)

:: 3. Start Frontend in a new terminal window
IF EXIST "frontend\" (
    echo Setting up frontend...
    start "Frontend Server" cmd /k "cd frontend && npm install && npm run dev"
) ELSE (
    echo Frontend directory not found!
)

echo App is running in separate windows! Close those windows to stop the servers.
pause
