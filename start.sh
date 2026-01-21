#!/bin/bash
set -e

echo "🚀 Starting Story-to-Cartoon Monolith..."

# 1. Start Redis in background
echo "📦 Starting Redis..."
redis-server --daemonize yes

# 2. Generate Assets (if missing)
echo "🎨 Generating assets..."
python3 generate_assets.py

# 3. Start Backend (FastAPI) in background
echo "🐍 Starting Backend on port 8000..."
cd backend
# Run with uvicorn in background, logging to file
uvicorn main:app --host 127.0.0.1 --port 8000 > ../backend.log 2>&1 &
cd ..

# 4. Start Celery Worker in background
echo "👷 Starting Worker..."
cd worker
# Run celery in background
celery -A tasks worker --loglevel=info --concurrency=2 > ../worker.log 2>&1 &
cd ..

# 5. Start Frontend (Next.js) in foreground (this keeps container alive)
echo "⚛️ Starting Frontend on port 3000..."
cd frontend
npm start
