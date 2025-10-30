# Python slim base image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (none required when using psycopg2-binary)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (better caching)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app

# Expose the application port
EXPOSE 8000

# Default environment (override in runtime with --env or --env-file)
# ENV DJANGO_SETTINGS_MODULE=config.settings

# Run database migrations on container start (optional). Comment out if you prefer external orchestration.
# CMD python manage.py migrate && gunicorn core.wsgi:application --bind 0.0.0.0:8000

# Start the app with Gunicorn
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
