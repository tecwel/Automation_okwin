FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && \
    apt-get install -y wget gnupg curl ca-certificates fonts-liberation \
    libnss3 libxss1 libasound2 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium
RUN python -m playwright install --with-deps chromium

# Copy source code
COPY . /app/

CMD ["python", "main.py"]
