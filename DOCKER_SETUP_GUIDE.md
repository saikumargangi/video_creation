# How to Configure Docker Hub for GitHub Actions

Since you logged in with Google, you **must** use an Access Token for the password.

## 1. Generate Docker Hub Access Token
1.  Log in to [hub.docker.com](https://hub.docker.com).
2.  Click your **Profile Picture** (top right) > **Account Settings**.
3.  Go to **Security** > **Personal Access Tokens**.
4.  Click **Generate New Access Token**.
5.  **Description**: `GitHub Actions`.
6.  **Access permissions**: `Read, Write, Delete`.
7.  Click **Generate**.
8.  **COPY THIS TOKEN**. You will not see it again.

## 2. Configure GitHub Secrets
1.  Go to your GitHub Repository: `https://github.com/saikumargangi/video_creation`.
2.  Click **Settings** (top tab).
3.  On the left sidebar, click **Secrets and variables** > **Actions**.
4.  Click **New repository secret** (green button).

### Secret #1: Username
*   **Name**: `DOCKER_USERNAME`
*   **Secret**: `(Your Docker Hub Username)` (NOT your email. It's the name you see in the URL, e.g., `saikumargangi`).

### Secret #2: Password
*   **Name**: `DOCKER_PASSWORD`
*   **Secret**: `(The Long Token you just copied)`

## 3. Trigger the Build
Once saved, go to the **Actions** tab in GitHub.
*   If the workflow failed before, click it and select **Re-run jobs**.
*   Or, push a small change to `README.md` to trigger it again.
