# syntax=docker/dockerfile:1

# ---------- Stage 1: build the React (Vite) bundle ----------
FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- Stage 2: Django served by gunicorn + WhiteNoise ----------
FROM python:3.13-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app/backend

COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

COPY backend/ ./
# The built SPA must sit at /app/frontend/dist so settings.FRONTEND_DIST
# (BASE_DIR.parent / "frontend" / "dist") resolves correctly.
COPY --from=frontend /app/frontend/dist /app/frontend/dist

RUN chmod +x entrypoint.sh
# Collect the SPA assets so WhiteNoise can serve them under /static/.
# A throwaway key lets settings import during the build (no DB access here).
RUN DJANGO_SECRET_KEY=build-only-not-used python manage.py collectstatic --noinput

EXPOSE 8000
ENTRYPOINT ["/app/backend/entrypoint.sh"]
