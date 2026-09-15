#!/bin/bash
if [ -z "$ULPF_MODE" ]; then
    export ULPF_MODE="dev"
fi
echo "Starting setup and run..."

# 1. Start Infrastructure via Docker Compose
if [ -f "docker-compose.yml" ]; then
    echo "Starting infrastructure (Postgres, Redis, Kafka, OpenSearch) via Docker..."
    docker-compose up -d postgres redis zookeeper kafka opensearch
fi

echo "Starting app natively..."

# 2. Start Backend
if [ -d "backend" ]; then
    echo "Setting up backend..."
    cd backend || exit
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Start the backend server (using uvicorn based on actual project)
    alembic upgrade head
    uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload & 
    BACKEND_PID=$!
    cd ..
else
    echo "Backend directory not found!"
fi

# 3. Start Frontend
if [ -d "frontend" ]; then
    echo "Setting up frontend..."
    cd frontend || exit
    npm install
    npm run dev &
    FRONTEND_PID=$!
    cd ..
else
    echo "Frontend directory not found!"
fi

# 4. Cleanup on exit (kills both processes when you press Ctrl+C)
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM EXIT

echo "Both servers are running! Press Ctrl+C to stop."
wait
