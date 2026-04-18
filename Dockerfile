# Use a lightweight Python base image
FROM python:3.9-slim

# Install system dependencies required for OpenCV and YOLO
# libgl1 is for OpenCV, libglib is for general image processing support
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy and install dependencies first (better for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Add core web and AI libraries explicitly to ensure they are present
RUN pip install --no-cache-dir ultralytics fastapi uvicorn python-multipart opencv-python-headless

# Copy the rest of the application files
COPY . .

# Expose the default FastAPI port (will be overridden by env variable on most hosts)
EXPOSE 8000

# Use python to run the server script
# web_server.py is updated to handle the $PORT environment variable
CMD ["python", "web_server.py"]
