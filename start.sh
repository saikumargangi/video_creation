#!/bin/bash
set -e

echo "🚀 Starting Story-to-Cartoon Monolith..."

# 1. Start Redis in background
echo "📦 Starting Redis..."
redis-server --daemonize yes

# 2. Generate Assets (if missing)
echo "🎨 Generating assets..."
# 2. Generate Assets (if missing)
echo "🎨 Generating assets..."
python3 generate_assets.py || echo "⚠️ Asset generation failed, continuing anyway..."

# 3. Start Backend (FastAPI) in background
echo "🐍 Starting Backend on port 8000..."
cd backend
# Run with uvicorn in background, logging to file
# Run with uvicorn in background, but log to stdout for debugging
# Run with uvicorn in background, with unbuffered output
PYTHONUNBUFFERED=1 uvicorn main:app --host 127.0.0.1 --port 8000 >&2 &
cd ..

# 4. Start Celery Worker in background
echo "👷 Starting Worker..."
cd worker
# Run celery in background
# Run celery in background, logging to stderr (unbuffered)
PYTHONUNBUFFERED=1 celery -A tasks worker --loglevel=info --concurrency=2 >&2 &
cd ..

# 5. Start Frontend (Next.js) in foreground (this keeps container alive)
echo "⚛️ Starting Frontend on port 3000..."
cd frontend
# Use npx next start to allow passing arguments explicitly
npx next start -p 3000 -H 0.0.0.0
