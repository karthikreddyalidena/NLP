# Use the official Python 3.10 slim image for a smaller footprint
FROM python:3.10-slim

# Set environment variables for Python and PyTorch optimization
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/.cache
ENV OMP_NUM_THREADS=1

# Install system dependencies (build-essential needed for some C-extensions)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
# We do this before copying the rest of the code to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK data to avoid downloading on every startup
RUN python -m nltk.downloader vader_lexicon

# Copy the entire project into the container
COPY . .

# Create a non-root user for security
RUN useradd -m appuser && \
    mkdir -p /app/.cache && \
    chown -R appuser:appuser /app
USER appuser

# Expose the port (Hugging Face Spaces requires port 7860)
EXPOSE 7860

# Start the application using Gunicorn with Eventlet workers for Socket.IO support
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "--timeout", "120", "--bind", "0.0.0.0:7860", "wsgi:application"]
