###########################
# Stage 1: Build Frontend  #
###########################
FROM node:18-slim AS frontend-build

WORKDIR /app/frontend

# Install only production dependencies first for better layer caching
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

# Copy rest of frontend sources
COPY frontend/ .
RUN npm run build

###########################
# Stage 2: Runtime Image   #
###########################
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
		PYTHONUNBUFFERED=1

WORKDIR /app

# System deps that are commonly needed for libs like lxml / pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
		build-essential \
		curl \
	&& rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ backend/

# Copy built frontend (static assets)
COPY --from=frontend-build /app/frontend/build frontend/build

# Create a non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONPATH=/app/backend

# Start script: launches backend then serves static build via simple Python server
RUN echo '#!/bin/bash\nset -e\n\n# Start FastAPI backend\npython -m uvicorn app:app --host 0.0.0.0 --port 8000 &\nBACKEND_PID=$!\n\n# Serve static frontend (already built)\ncd /app/frontend/build\npython -m http.server 3000 &\nFRONT_PID=$!\n\n# Basic wait logic\ntrap "kill $BACKEND_PID $FRONT_PID" EXIT\nwait -n' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 8000 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
	CMD curl -fsS http://localhost:8000/docs >/dev/null || exit 1

CMD ["/app/start.sh"]