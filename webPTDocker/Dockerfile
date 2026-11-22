# Build from the repository root: docker build -f webPTDocker/Dockerfile -t webptdocker:latest .
FROM ubuntu:24.04
LABEL maintainer="0xdhanesh <dhanesh.professional@gmail.com>" \
      org.opencontainers.image.title="webPTDocker" \
      org.opencontainers.image.description="Web application pentesting"
ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SECURITY_ENV=webPTDocker
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    dnsutils \
    ffuf \
    file \
    git \
    gobuster \
    jq \
    libpcap0.8t64 \
    nmap \
    openssl \
    python3 \
    python3-pip \
    python3-venv \
    sqlmap \
    tini \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*
ARG TARGETARCH
COPY shared/install_release.py /opt/security/install_release.py
COPY webPTDocker/releases.json /opt/security/releases.json
RUN python3 /opt/security/install_release.py /opt/security/releases.json "$TARGETARCH"
# Bundle a known template snapshot for use without a runtime download.
ARG NUCLEI_TEMPLATES_VERSION=v10.5.2
RUN git clone --depth 1 --branch "$NUCLEI_TEMPLATES_VERSION" \
    https://github.com/projectdiscovery/nuclei-templates.git /opt/nuclei-templates \
    && rm -rf /opt/nuclei-templates/.git
COPY shared/requirements.txt /opt/security/mcp-requirements.txt
COPY webPTDocker/requirements.txt /opt/security/requirements.txt
RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir -r /opt/security/mcp-requirements.txt -r /opt/security/requirements.txt
RUN useradd --badname --uid 10001 --create-home --shell /bin/bash 0xdhanesh \
    && mkdir -p /workspace \
    && chown 10001:10001 /workspace
COPY shared/mcp_server.py /opt/security/mcp_server.py
COPY webPTDocker/tools.json /opt/security/tools.json
USER 0xdhanesh
WORKDIR /workspace
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/bash"]
