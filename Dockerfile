# Multi-stage build for SRL4C

# Stage 1: Build frontend
FROM node:20-slim AS frontend
WORKDIR /app/ui
COPY ui/package*.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.10-slim

WORKDIR /app

# Install uv for fast package management
RUN pip install uv

# Copy and install Python dependencies
COPY pyproject.toml ./
COPY src/ src/
RUN uv pip install --system .

# Copy built frontend
COPY --from=frontend /app/ui/dist ./static

# Copy data and templates
COPY data/ data/
COPY templates/ templates/

# Create directory for user config (will be mounted as volume)
RUN mkdir -p /data

# Environment
ENV SRL4C_HOME=/data
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

CMD ["uvicorn", "srl4c.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
