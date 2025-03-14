# Use an official Python image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libsm6 libxext6 libxrender-dev \
    libglib2.0-0 ffmpeg

# Copy project files
COPY . /app

# Install required Python packages
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir opencv-contrib-python flask firebase-admin

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Start the app
CMD ["python", "main.py"]
