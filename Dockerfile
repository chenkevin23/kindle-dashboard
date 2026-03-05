FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

ENV DEBIAN_FRONTEND=noninteractive
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PYTHONUNBUFFERED=1
ENV MALLOC_ARENA_MAX=2

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Entry point for Railway cron
CMD ["python", "-m", "src.main"]
