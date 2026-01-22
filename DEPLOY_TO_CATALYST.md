# Deployment Guide: Zoho Catalyst (AppSail)

## Overview
This project is configured as a **Monolithic Docker Container** for easy deployment on Zoho Catalyst AppSail. It bundles the Backend, Frontend, Celery Worker, and Redis into a single container.

**Why this approach?**
The current code uses a *shared filesystem* (local `/app/jobs` folder) to pass data between the API and the Worker. Deploying them as separate microservices would break this link. The monolithic approach preserves it.

## Deployment Steps

### 1. Prerequisites
*   Zoho CLI installed (`npm install -g zcli`) or use the [Catalyst Console](https://catalyst.zoho.com/).
*   A Project created in Zoho Catalyst.

### 2. Deploy via AppSail Console (Git Integration)
Since you have connected this project to GitHub, you do **not** need to zip files manually.

1.  **Trigger Build**:
    *   Go to your AppSail service in the Zoho Catalyst Console.
    *   Click **Deploy** / **Build**.
    *   Select your **Branch** (e.g., `main`).

2.  **Build Configuration (Crucial)**:
    *   **Build Context**: `/` (Root directory).
    *   **Dockerfile Path**: `Dockerfile.deploy` (⚠️ **IMPORTANT**: You must manually change this from `Dockerfile` to `Dockerfile.deploy`).
    *   **Port**: `3000`.

3.  **Configurations (Environmental Variables)**:
    Ensure these are set in the "Configuration" tab:
    *   `GEMINI_API_KEY`: `[Your Google Gemini API Key]` (Required)
    *   `PORT`: `3000`
    *   `HOST`: `0.0.0.0`
    *   `PYTHONUNBUFFERED`: `1`

4.  **Resources (Compute)**:
    *   **Memory**: Select at least **1GB or 2GB**. 
    *   **CPU**: 1 vCPU minimum.

### Alternative: Manual Upload
If Git fails for any reason, you can use the source code upload method (Zip), but Git is preferred for continuous deployment.

### 3. Deploy via CLI
If you prefer the command line:

```bash
# Login
zcli login

# Initialize (if not already)
catalyst appsail:init
# Select your project
# Service Name: video-creator
# Stack: Docker (Use Dockerfile)

# Deploy
catalyst appsail:deploy
```
*Note: Ensure `app-config.json` points to `Dockerfile.deploy`.*

## Important Considerations
*   **Ephemeral Storage**: In AppSail, the filesystem is temporary. If the app restarts, **all generated videos and job history in `/jobs` will be lost**. For a production app, you must integrate Cloud Storage (Catalyst FileStore, S3, etc.).
*   **Startup Time**: The container starts 4 services. It might take 10-20 seconds to become "Ready".
*   **Logs**: Check "Logs" in the Catalyst Console if deployment fails. We have enabled full logging to `stderr`.

## Testing
Once deployed:
1.  Open the AppSail URL (e.g., `https://video-creator.zohoapp.com`).
2.  Paste a short story.
3.  Watch the logs to see the "Job Submitted" and worker picking it up.
