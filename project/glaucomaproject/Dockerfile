# Use Python 3.10 slim to reduce image size
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (useful for image processing libs like Pillow)
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose Django port
EXPOSE 8000

# Start Django development server
# Note: For production use gunicorn, e.g., gunicorn glaucomaproject.wsgi:application -b 0.0.0.0:8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
