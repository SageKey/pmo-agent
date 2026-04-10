# Backend container for Railway deployment.
# Serves the FastAPI app on $PORT (Railway injects) and imports the
# flat Python engines from the repo root via the app.engines shim.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# System deps for ortools / pandas wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Install backend dependencies first (better layer caching)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install -r /app/backend/requirements.txt

# 2. Copy the engines (flat root-level Python files) — the FastAPI app
#    imports these via the sys.path shim in backend/app/engines.py.
COPY models.py sqlite_connector.py capacity_engine.py \
     schedule_optimizer.py pmo_agent.py snapshot_store.py jira_sync.py \
     config.py \
     seed_data.sql \
     /app/

# 3. Copy the backend package
COPY backend /app/backend

# Railway mounts a persistent volume at /data — point DB_PATH there so
# data survives redeploys. The startup hook in app.main will seed it
# from /app/seed_data.sql on first boot.
ENV DB_PATH=/data/pmo_data.db \
    SNAPSHOT_DB_PATH=/data/pmo_snapshots.db

WORKDIR /app/backend

# Railway injects $PORT — default to 8000 for local `docker run` testing.
ENV PORT=8000
EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
