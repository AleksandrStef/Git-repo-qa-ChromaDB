FROM python:3.10-slim

WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data/chroma

# Expose port
EXPOSE 8000

# Start the application
CMD ["python", "-m", "app.main"]
