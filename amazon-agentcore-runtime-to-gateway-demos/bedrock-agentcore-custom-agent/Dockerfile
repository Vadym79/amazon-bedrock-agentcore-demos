# Use uv's ARM64 Python base image
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY requirements.txt requirements.txt
# Install from requirements file
RUN pip install -r requirements.txt


# Copy agent file
COPY agentcore_runtime_custom_agent_demo.py ./
COPY agent_core_utils.py ./


# Expose port
EXPOSE 8080

# Run application
CMD ["opentelemetry-instrument", "uvicorn", "agentcore_runtime_custom_agent_demo:app", "--host", "0.0.0.0", "--port", "8080"]