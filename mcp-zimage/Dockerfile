FROM nvidia/cuda:12.8.0-devel-ubuntu22.04

WORKDIR /app

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.12 and basics
# Ubuntu 22.04 comes with Python 3.10. We need 3.12.
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pip for 3.12
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# Make python3 command point to python3.12
RUN ln -sf /usr/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.12 /usr/bin/python

# Install poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY README.md ./

# Configure poetry
RUN poetry config virtualenvs.create false

# Install dependencies
# Using --no-cache-dir to keep image small
RUN poetry install --no-interaction --no-ansi --no-root --no-cache

# Copy source code
COPY src/ ./src/

# Set environment variable for transport
ENV MCP_TRANSPORT=sse
ENV INTERNAL_PORT=8000

# Expose port
EXPOSE 8000

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "server"]