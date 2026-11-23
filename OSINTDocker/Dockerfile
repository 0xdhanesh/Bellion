# Build from the repository root: docker build -f OSINTDocker/Dockerfile -t osintdocker:latest .
FROM node:24.22.1-bookworm-slim AS node
FROM ubuntu:24.04
LABEL maintainer="0xdhanesh <dhanesh.professional@gmail.com>" \
      org.opencontainers.image.title="OSINTDocker" \
      org.opencontainers.image.description="OSINT and artifact/website reconnaissance"
ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SECURITY_ENV=OSINTDocker
RUN apt-get update && apt-get install -y --no-install-recommends \
    apktool \
    bash \
    binutils \
    binwalk \
    ca-certificates \
    curl \
    default-jre-headless \
    dnsutils \
    file \
    git \
    jq \
    libimage-exiftool-perl \
    nmap \
    openssl \
    python3 \
    python3-pip \
    python3-venv \
    ripgrep \
    tini \
    unzip \
    wget \
    whois \
    && rm -rf /var/lib/apt/lists/*
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
# REA uses procps for ownership checks before launching analysis workers.
RUN apt-get update && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/*
ARG REA_VERSION=6.10.1
RUN npm install --global "rea-agents@${REA_VERSION}" && npm cache clean --force
ARG TARGETARCH
COPY shared/install_artifacts.py /opt/security/install_artifacts.py
COPY shared/rea/jadx-mcp.json /opt/security/rea-jadx-mcp.json
RUN python3 /opt/security/install_artifacts.py /opt/security/rea-jadx-mcp.json "$TARGETARCH"
# REA engine locations live in the image, so neither the shell nor MCP needs host paths.
ENV REA_JADX_MCP_JAR=/opt/rea-engines/jadx/jadx-headless-mcp-0.7.1-all.jar
COPY shared/install_release.py /opt/security/install_release.py
COPY OSINTDocker/releases.json /opt/security/releases.json
RUN python3 /opt/security/install_release.py /opt/security/releases.json "$TARGETARCH"
COPY shared/requirements.txt /opt/security/mcp-requirements.txt
COPY OSINTDocker/requirements.txt /opt/security/requirements.txt
RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir -r /opt/security/mcp-requirements.txt -r /opt/security/requirements.txt
RUN useradd --badname --uid 10001 --create-home --shell /bin/bash 0xdhanesh \
    && mkdir -p /workspace \
    && chown 10001:10001 /workspace
COPY shared/mcp_server.py /opt/security/mcp_server.py
COPY OSINTDocker/tools.json /opt/security/tools.json
USER 0xdhanesh
WORKDIR /workspace
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/bash"]
