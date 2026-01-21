# Story-to-Cartoon MVP

A web platform that converts user stories into 5-minute animated cartoon videos using AI agents and a deterministic rendering pipeline.

## Features
- **AI Agents**: Converts stories to scripts, bibles, and scene layouts using Gemini API.
- **Deterministic Renderer**: Generates 1080p MP4 videos using MoviePy and FFmpeg.
- **Parallel Processing**: Uses Celery workers for concurrent scene rendering.
- **Premium Frontend**: Next.js interface with real-time progress tracking.

## Prerequisites
- Docker and Docker Compose
- Google Gemini API Key

## Setup & Run

1.  **Environment Variables**
    Copy `.env.example` to `.env` and add your Gemini API Key:
    ```bash
    cp .env.example .env
    # Edit .env and set GEMINI_API_KEY
    ```

2.  **Generate Dummy Assets**
    (Optional if running purely with Docker, as you can run this inside the container)
    If you want to run asset generation manually:
    ```bash
    python3 generate_assets.py
    ```
    *Note: This requires `Pillow` to be installed locally.*

3.  **Run with Docker Compose**
    ```bash
    docker-compose up --build
    ```
    This will start:
    - Frontend: http://localhost:3000
    - Backend: http://localhost:8000
    - Redis: port 6379
    - Worker: Background processing

    *Note: If you are on a Mac with a broken Docker installation, please reinstall Docker Desktop.*

4.  **Generate Assets in Docker**
    If you didn't run step 2 locally, run this once the containers are up:
    ```bash
    docker-compose exec worker python3 generate_assets.py
    ```

## Usage
1.  Open http://localhost:3000.
2.  Enter a short story (e.g., "A robot finds a flower...").
3.  Click "Generate Cartoon".
4.  Wait for the progress bar to complete.
5.  Download and watch your video!

## Testing
Run the integration test (requires the stack to be running):
```bash
python3 test_integration.py
```

## Architecture
- **Backend**: FastAPI
- **Frontend**: Next.js (React)
- **Worker**: Celery + Redis
- **Rendering**: MoviePy + FFmpeg
