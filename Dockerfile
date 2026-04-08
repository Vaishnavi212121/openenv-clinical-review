FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# STEP 1: Copy ALL files first so pyproject.toml exists in /app
COPY . .

# STEP 2: Now install (pip will find the files now)
RUN pip install --no-cache-dir .

# Setup user and port
RUN useradd -m -u 1000 openenv && chown -R openenv:openenv /app
USER 1000
EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]