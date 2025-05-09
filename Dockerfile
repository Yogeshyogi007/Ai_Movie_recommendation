FROM python:3.8-slim

WORKDIR /app

# Install system dependencies for building scientific packages
RUN apt-get update && apt-get install -y \
    python3-dev \
    build-essential \
    gfortran \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Upgrade pip and build tools
RUN pip install --upgrade pip setuptools wheel

# Install Python requirements
RUN pip install --only-binary :all: -r requirements.txt

# Command to run your app
CMD ["python", "run.py"]
