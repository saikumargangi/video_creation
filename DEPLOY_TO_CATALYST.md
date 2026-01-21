# Deployment Guide: Zoho Catalyst (AppSail)

Since you cannot run Docker locally, you can deploy the components of this application to Zoho Catalyst (AppSail) or any other container platform.

## Architecture on Catalyst
You will need to deploy 4 separate services "apps" in AppSail (or 3 if you use a managed Redis):
1.  **Backend** (FastAPI)
2.  **Worker** (Celery)
3.  **Frontend** (Next.js)
4.  **Redis** (Message Broker)

## Prerequisites
1.  **Zoho CLI**: Install `zcli`.
2.  **Catalyst Project**: Create a project in the Zoho Catalyst console.
3.  **Git Remote**: Push this repository to GitHub/GitLab.

## 1. Redis (Message Broker)
Celery needs Redis to communicate between the Backend and Worker.
*Option A (Easiest)*: Use a managed Redis provider (e.g., Upstash, Redis Cloud) and get a `redis://` URL.
*Option B (Catalyst)*: Deploy a standard Redis docker image als an AppSail service.

## 2. Backend Service
1.  Navigate to `backend/`.
2.  Initialize an AppSail service:
    ```bash
    catalyst appsail:init
    # Select "Python", build path: .
    ```
3.  Update `app-config.json` (created by init) or set Environment Variables in the Console:
    - `CELERY_BROKER_URL`: Your Redis URL
    - `CELERY_RESULT_BACKEND`: Your Redis URL
    - `GEMINI_API_KEY`: Your API Key
    - `JOBS_DIR`: `/tmp` (Note: AppSail storage is ephemeral. For persistence, enable Catalyst File Store and use SDK, or use `/tmp` for demo).
4.  Deploy:
    ```bash
    catalyst appsail:deploy
    ```
5.  Note the **Backend URL**.

## 3. Worker Service
1.  Navigate to `worker/`.
2.  Initialize AppSail:
    ```bash
    catalyst appsail:init
    # Select "Python", build path: .
    ```
3.  **Crucial**: The `CMD` in Dockerfile must start the worker, NOT a web server. AppSail expects a web server usually, but for a worker, you might need to ensure it doesn't health-check fail.
    *Workaround*: Run a small dummy web server alongside build, or configure AppSail to ignore health checks if possible.
4.  Set Environment Variables (Same as Backend).
5.  Deploy.

## 4. Frontend Service
1.  Navigate to `frontend/`.
2.  Initialize AppSail (Node.js).
3.  Set Environment Variable:
    - `NEXT_PUBLIC_API_URL`: The **Backend URL** from step 2.
4.  Deploy.

## Shared Storage (Important)
Since Backend writes files that Worker reads, and they are in *different* containers in the cloud, they **cannot share a filesystem** like `/jobs` on Docker Compose.
**MVP Fix for Cloud**:
You must modify the code to use **Cloud Storage** (AWS S3, Google Cloud Storage, or Zoho Catalyst File Store) instead of local files (`/jobs`) for passing data between agents and serving the final video.

*For this MVP code provided*: It relies on a shared Volume (`/jobs`). Verification in Zoho Catalyst will fail unless you switch to a single-container deployment (all in one) or implement cloud storage.

### Recommendation for "Single Container" (Simplest Cloud Deploy)
To avoid rewriting storage logic:
1.  Create a **new Dockerfile** in root that installs Redis, Python, and Node.
2.  Run Backend, Worker, and Frontend *inside one container* using `supervisord`.
3.  Deploy that ONE container to AppSail.
4.  This mimics `docker-compose` behavior in a single box.
