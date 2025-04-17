FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agents/reporting_analytics /app/agents/reporting_analytics
COPY a2a /app/a2a

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8004

# Expose the port
EXPOSE ${PORT}

# Run the agent
CMD ["python", "agents/reporting_analytics/agent.py"]
