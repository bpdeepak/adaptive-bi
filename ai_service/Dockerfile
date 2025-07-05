# ai_service/Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# Add redis-tools if you want redis-cli inside the container for debugging
# Required by some Python packages for image/chart generation (e.g., kaleido for plotly)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*


# Copy the requirements file into the container
# Assuming you have combined requirements.txt and requirements_phase4.txt into a single requirements.txt
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create the directory for saved models if it doesn't exist (important for persistence)
# This should match MODEL_SAVE_PATH in .env / ModelConfig
RUN mkdir -p /app/models/saved_models

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]