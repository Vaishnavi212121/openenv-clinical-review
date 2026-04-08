FROM python:3.11-slim

# Metadata
LABEL maintainer="OpenEnv Clinical Review"
LABEL version="1.0.0"
LABEL description="Clinical Trial Protocol Review — OpenEnv Environment"

# System deps
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Install Python dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user (HF Spaces runs as user 1000)
RUN useradd -m -u 1000 openenv && chown -R openenv:openenv /app
USER 1000

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
