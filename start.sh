#!/bin/bash
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

# Load environment variables
if [ -f .env ]; then
  export $(cat .env | xargs)
fi

# Ensure jobs.json exists for Docker mounting issues (it becomes a dir if missing)
if [ ! -f jobs.json ]; then
  echo "[]" > jobs.json
fi

echo "Starting Job Portal Services..."

# Start Agent
echo "Starting Python Agent..."
cd agent
source venv/bin/activate
uvicorn bot:app --host 0.0.0.0 --port 7860 --reload &
AGENT_PID=$!
cd ..

# Start Frontend
echo "Starting Next.js Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

wait $AGENT_PID $FRONTEND_PID
