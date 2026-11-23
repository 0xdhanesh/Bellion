# Build from the repository root.
FROM ubuntu:24.04
LABEL maintainer="0xdhanesh <dhanesh.professional@gmail.com>" \
      org.opencontainers.image.title="networkPTDocker" \
      org.opencontainers.image.description="Network enumeration and packet analysis"
ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SECURITY_ENV=networkPTDocker
RUN apt-get update && apt-get install -y --no-install-recommends \
    arp-scan \
    bash \
    ca-certificates \
    curl \
    dnsutils \
    file \
    git \
    iproute2 \
    iputils-ping \
    jq \
    ldap-utils \
    masscan \
    netcat-openbsd \
    nmap \
    openssl \
    proxychains4 \
    python3 \
    python3-netifaces \
    python3-pip \
    python3-venv \
    smbclient \
    socat \
    tcpdump \
    tini \
    traceroute \
    tshark \
    unzip \
    wget \
    whois \
    && rm -rf /var/lib/apt/lists/*
ARG TARGETARCH
COPY shared/install_artifacts.py /opt/security/install_artifacts.py
COPY networkPTDocker/artifacts.json /opt/security/artifacts.json
RUN python3 /opt/security/install_artifacts.py /opt/security/artifacts.json "$TARGETARCH" \
    && ln -s /opt/ligolo-ng/proxy /usr/local/bin/ligolo-proxy \
    && ln -s /opt/ligolo-ng/agent /usr/local/bin/ligolo-agent \
    && /usr/local/bin/chisel --version
COPY shared/requirements.txt /opt/security/mcp-requirements.txt
COPY networkPTDocker/requirements.txt /opt/security/requirements.txt
RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir -r /opt/security/mcp-requirements.txt -r /opt/security/requirements.txt
# Responder needs netifaces (system package) and aioquic; keep it in its own venv.
# It writes logs, its database and certificates beside itself, so the install tree is
# owned by the runtime user (live poisoning still needs root and network capabilities).
RUN python3 -m venv --system-site-packages /opt/responder-venv \
    && /opt/responder-venv/bin/pip install --no-cache-dir aioquic==1.9.1 \
    && printf '#!/bin/sh\nexec /opt/responder-venv/bin/python3 /opt/responder/Responder.py "$@"\n' > /usr/local/bin/responder \
    && chmod 0755 /usr/local/bin/responder
RUN useradd --badname --uid 10001 --create-home --shell /bin/bash 0xdhanesh \
    && mkdir -p /workspace \
    && chown 10001:10001 /workspace \
    && chown -R 10001:10001 /opt/responder
COPY shared/mcp_server.py /opt/security/mcp_server.py
COPY networkPTDocker/tools.json /opt/security/tools.json
USER 0xdhanesh
WORKDIR /workspace
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/bash"]
