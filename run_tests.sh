#!/bin/bash

# Start the Docker container
echo "Starting Docker container..."
docker-compose up -d

# Wait for the API to start
echo "Waiting for API to start..."
sleep 10

# Run the tests
echo "Running tests..."
python test_qa.py

# Optional: Stop the Docker container
# echo "Stopping Docker container..."
# docker-compose down
