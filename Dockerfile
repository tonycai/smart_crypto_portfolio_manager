FROM python:3.9-slim

WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code
COPY src/ /app/src/
COPY config/ /app/config/

# Expose the port that FastAPI runs on
EXPOSE 8000

# Command to run the server
CMD ["python", "src/api/mcp_server.py"] 