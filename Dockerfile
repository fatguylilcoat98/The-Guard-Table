# PathBack — The Good Neighbor Guard
# Built by Christopher Hughes · Sacramento, CA
# Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
# Truth · Safety · We Got Your Back
#
# Multi-stage build: React frontend compiled in a node stage, then served
# by Flask/gunicorn from a slim Python image. SQLite lives on the /data
# volume so counters and access passes survive container restarts.

FROM node:20-slim AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY --from=frontend-build /build/build frontend/build

ENV PATHBACK_DB=/data/pathback.db \
    PYTHONUNBUFFERED=1
VOLUME /data
EXPOSE 8000

WORKDIR /app/backend
# 2 workers proves the SQLite counters are multi-worker safe; SSE streams
# need the long timeout and keep-alive.
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers", "2", \
     "--timeout", "120", "--keep-alive", "75", "app:app"]
