FROM python:3.10-slim

# System dependencies for Playwright
RUN apt-get update && apt-get install -y wget gnupg curl libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxss1 libasound2 libxrandr2 libgtk-3-0 libgbm-dev

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its dependencies
RUN pip install playwright && playwright install --with-deps

# Run the app
CMD ["python", "main.py"]
