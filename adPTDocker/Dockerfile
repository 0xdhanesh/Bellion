# Build from the repository root.
# kerbrute publishes no arm64 binary; build the pinned tag from source for every
# architecture (Go verifies the module graph against go.sum and the checksum database).
FROM ubuntu:24.04 AS kerbrute
ARG KERBRUTE_VERSION=v1.0.3
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git golang-go \
    && rm -rf /var/lib/apt/lists/*
RUN GOBIN=/out CGO_ENABLED=0 go install -trimpath "github.com/ropnop/kerbrute@${KERBRUTE_VERSION}" \
    && /out/kerbrute version

FROM ubuntu:24.04
LABEL maintainer="0xdhanesh <dhanesh.professional@gmail.com>" \
      org.opencontainers.image.title="adPTDocker" \
      org.opencontainers.image.description="Windows and Active Directory assessment"
ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SECURITY_ENV=adPTDocker
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    dnsutils \
    file \
    git \
    jq \
    krb5-user \
    ldap-utils \
    libsasl2-modules-gssapi-mit \
    openssl \
    python3 \
    python3-pip \
    python3-venv \
    smbclient \
    tini \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*
# evil-winrm is a Ruby gem; native gems (gssapi, readline-ext) compile against the
# -dev packages below, which are removed once installed. Runtime libraries stay.
ARG EVIL_WINRM_VERSION=4.1
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libffi-dev libkrb5-dev libreadline-dev ruby ruby-dev \
    && gem install --no-document evil-winrm -v "$EVIL_WINRM_VERSION" \
    && apt-get purge -y --auto-remove build-essential libffi-dev libkrb5-dev libreadline-dev ruby-dev \
    && apt-get install -y --no-install-recommends libreadline8t64 libffi8 \
    && rm -rf /var/lib/apt/lists/* /var/lib/gems/*/cache \
    && evil-winrm --help >/dev/null
COPY --from=kerbrute /out/kerbrute /usr/local/bin/kerbrute
COPY shared/requirements.txt /opt/security/mcp-requirements.txt
COPY adPTDocker/requirements.txt /opt/security/requirements.txt
RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir -r /opt/security/mcp-requirements.txt -r /opt/security/requirements.txt
RUN useradd --badname --uid 10001 --create-home --shell /bin/bash 0xdhanesh \
    && mkdir -p /workspace \
    && chown 10001:10001 /workspace
COPY shared/mcp_server.py /opt/security/mcp_server.py
COPY adPTDocker/tools.json /opt/security/tools.json
USER 0xdhanesh
WORKDIR /workspace
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/bash"]
