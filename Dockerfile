# Dockerfile for CasualHero BI Platform (Dash)
# Base: Python 3.11 slim
# Target: Fly.io deployment with 8GB RAM

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 casualhero && chown -R casualhero:casualhero /app
USER casualhero

# Expose port (Fly.io internal port)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run with Gunicorn (single worker for MVP - data loads once at startup)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "300", "--graceful-timeout", "300", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "src.ui.dash_app:server"]
