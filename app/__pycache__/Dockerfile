# Use a base image with Python
FROM python:3.8-slim

# Set working directory inside the container
WORKDIR /app

# Copy your app code into the container
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Run your application
CMD ["python", "run.py"]
