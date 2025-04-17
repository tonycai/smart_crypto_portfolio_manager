FROM python:3.9-slim

WORKDIR /app

# Copy the requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent code and common modules
COPY agents/orchestration /app/agents/orchestration
COPY a2a /app/a2a
COPY common /app/common
COPY config /app/config

# Set environment variables
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8005

# Expose the port
EXPOSE 8005

# Run the agent
CMD ["python", "agents/orchestration/agent.py"] 