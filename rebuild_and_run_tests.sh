#!/bin/bash
set -e

# Stop and remove any existing containers
docker-compose -f docker-compose.test.yml down

# Rebuild the image
docker-compose -f docker-compose.test.yml build

# Run the tests
docker-compose -f docker-compose.test.yml up

# Print the logs for debugging
echo "Test container logs:"
docker-compose -f docker-compose.test.yml logs 