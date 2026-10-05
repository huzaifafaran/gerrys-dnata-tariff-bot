FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies, curl, and Node.js 20.x
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js bridge dependencies
COPY bridge/package*.json ./bridge/
RUN cd bridge && npm install --omit=dev

# Copy application source code
COPY . .

# Ensure start script has executable permissions
RUN chmod +x ./start.sh

# Render dynamically sets $PORT (typically 10000)
EXPOSE 8000 10000

# Launch all 3 services via start.sh
CMD ["./start.sh"]
