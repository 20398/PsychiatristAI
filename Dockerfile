# Use a slim Python base image
FROM python:3.12-slim

# Set workdir and Python options
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy dependency declarations first for efficient layer caching
COPY requirements.txt ./

# Install runtime dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . /app

# Expose the application port
EXPOSE 8000

# Default startup command
CMD ["python", "app/main.py"]
