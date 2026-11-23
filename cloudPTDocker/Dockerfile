# Build from the repository root.
FROM ubuntu:24.04
LABEL maintainer="0xdhanesh <dhanesh.professional@gmail.com>" \
      org.opencontainers.image.title="cloudPTDocker" \
      org.opencontainers.image.description="Cloud configuration assessment"
ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SECURITY_ENV=cloudPTDocker
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    file \
    git \
    groff \
    jq \
    less \
    openssl \
    python3 \
    python3-pip \
    python3-venv \
    tini \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*
COPY shared/requirements.txt /opt/security/mcp-requirements.txt
COPY cloudPTDocker/requirements.txt /opt/security/requirements.txt
RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir -r /opt/security/mcp-requirements.txt -r /opt/security/requirements.txt
ARG TARGETARCH
COPY cloudPTDocker/versions.json cloudPTDocker/gcloud-release.json /opt/security/
COPY cloudPTDocker/install_clis.py cloudPTDocker/install_gcloud.py /opt/security/
RUN /usr/bin/python3 /opt/security/install_gcloud.py "$TARGETARCH"
# Some prowler dependencies (e.g. zstd) have no wheels on every architecture, so a
# compiler is present only while the CLIs are installed.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential python3-dev \
    && /usr/bin/python3 /opt/security/install_clis.py \
    && apt-get purge -y --auto-remove build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*
COPY shared/install_artifacts.py /opt/security/install_artifacts.py
COPY cloudPTDocker/artifacts.json /opt/security/artifacts.json
RUN /usr/bin/python3 /opt/security/install_artifacts.py /opt/security/artifacts.json "$TARGETARCH" \
    && ln -s /opt/trivy/trivy /usr/local/bin/trivy \
    && trivy --version
ENV CLOUDSDK_PYTHON=/usr/bin/python3 \
    CLOUDSDK_CORE_DISABLE_USAGE_REPORTING=true \
    CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK=true \
    AZURE_CORE_COLLECT_TELEMETRY=no \
    AWS_PAGER=""
RUN useradd --badname --uid 10001 --create-home --shell /bin/bash 0xdhanesh \
    && mkdir -p /workspace \
    && chown 10001:10001 /workspace
COPY shared/mcp_server.py /opt/security/mcp_server.py
COPY cloudPTDocker/tools.json /opt/security/tools.json
USER 0xdhanesh
WORKDIR /workspace
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/bash"]
