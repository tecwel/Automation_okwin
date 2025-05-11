FROM mcr.microsoft.com/playwright/python:v1.43.0-jammy

WORKDIR /app

# Copy all files
COPY . .

# Install your Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Run your app
CMD ["python3", "main.py"]
