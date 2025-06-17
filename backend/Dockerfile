# Use latest Python 3.12 image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    cmake \
    pkg-config \
    libx11-dev \
    libatlas-base-dev \
    libgtk-3-dev \
    libboost-python-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*
# Set work directory
WORKDIR /code

# Install Python dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /code/

# Collect static files (optional)
RUN python backend/manage.py collectstatic --noinput || true

# Run Uvicorn ASGI server
CMD ["uvicorn", "timeEntry.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
