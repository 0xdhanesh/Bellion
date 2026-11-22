# Build from the repository root: docker build -f reDocker/Dockerfile -t redocker:latest .
FROM ubuntu:24.04
LABEL maintainer="0xdhanesh <dhanesh.professional@gmail.com>" \
      org.opencontainers.image.title="reDocker" \
      org.opencontainers.image.description="ELF and native binary reverse engineering"
ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SECURITY_ENV=reDocker
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    binutils \
    build-essential \
    ca-certificates \
    curl \
    elfutils \
    file \
    gdb \
    git \
    jq \
    ltrace \
    nasm \
    patchelf \
    python3 \
    python3-pip \
    python3-venv \
    strace \
    tini \
    unzip \
    wget \
    yara \
    && rm -rf /var/lib/apt/lists/*
COPY shared/requirements.txt /opt/security/mcp-requirements.txt
COPY reDocker/requirements.txt /opt/security/requirements.txt
RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir -r /opt/security/mcp-requirements.txt -r /opt/security/requirements.txt
RUN useradd --badname --uid 10001 --create-home --shell /bin/bash 0xdhanesh \
    && mkdir -p /workspace \
    && chown 10001:10001 /workspace
COPY shared/mcp_server.py /opt/security/mcp_server.py
COPY reDocker/tools.json /opt/security/tools.json
USER 0xdhanesh
WORKDIR /workspace
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/bash"]
