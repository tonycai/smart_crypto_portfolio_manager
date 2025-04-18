#!/bin/bash

echo "Building and running A2A protocol tests in Docker..."

# Build the test container
docker-compose -f docker-compose.test.yml build

# Run the tests
docker-compose -f docker-compose.test.yml run --rm a2a-tests

# Clean up
docker-compose -f docker-compose.test.yml down 