# Containerized Static Analysis Sandbox for AuditAgent
FROM python:3.11-slim

LABEL maintainer="AuditAgent Team <team@auditagent.local>"
LABEL description="Hardened execution sandbox for Slither, Aderyn, and Solidity compilers"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SOLC_VERSION=0.8.20

# Install minimal OS dependencies and git
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python analysis tools
RUN pip install --no-cache-dir \
    slither-analyzer==0.10.2 \
    solc-select \
    pydantic

# Pre-install Solidity compiler
RUN solc-select install ${SOLC_VERSION} && solc-select use ${SOLC_VERSION}

# Create unprivileged sandbox user
RUN useradd -m -u 1001 sandboxuser
WORKDIR /home/sandboxuser/app

COPY . /home/sandboxuser/app
RUN chown -R sandboxuser:sandboxuser /home/sandboxuser/app

USER sandboxuser

# Sandbox execution constraints:
# Execute container with: --network none --read-only --cpus 2.0 --memory 2048m
ENTRYPOINT ["python", "-m", "analysis.runner"]
