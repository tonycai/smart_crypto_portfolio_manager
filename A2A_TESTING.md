# A2A Protocol Testing

This document provides instructions for running the tests for the Agent-to-Agent (A2A) protocol implementation.

## Prerequisites

- Docker and Docker Compose installed on your system
- Git repository cloned to your local machine

## Running the Tests

### Using the Test Script

The easiest way to run the tests is to use the provided shell script:

```bash
# Make the script executable
chmod +x run_a2a_tests.sh

# Run the tests
./run_a2a_tests.sh
```

This will:
1. Build a Docker image with all required dependencies
2. Run the A2A tests inside a container
3. Clean up after completion

### Manual Execution

If you prefer to run the tests manually:

```bash
# Build the test container
docker-compose -f docker-compose.test.yml build

# Run all A2A tests
docker-compose -f docker-compose.test.yml run --rm a2a-tests

# Run specific tests (example)
docker-compose -f docker-compose.test.yml run --rm a2a-tests python -m pytest tests/test_a2a_server.py -v

# Clean up
docker-compose -f docker-compose.test.yml down
```

## Test Files

The A2A tests are located in the following files:

- `tests/test_a2a_server.py` - Tests for the A2A server implementation
- `tests/test_a2a_protocol_client_server.py` - Tests for the integration between A2A client and server

## Structure

The test environment is configured with:

- Python 3.9
- All required dependencies from `requirements.txt` and `requirements-a2a.txt`
- pytest and pytest-asyncio for handling async tests
- Proper PYTHONPATH configuration to find all modules

## Troubleshooting

If you encounter any issues:

1. Ensure Docker and Docker Compose are properly installed
2. Check that the proper files are mounted in the Docker Compose configuration
3. Verify that all required dependencies are listed in the requirements files

For module import errors, check that the `PYTHONPATH` environment variable is set correctly in the Docker Compose file. 