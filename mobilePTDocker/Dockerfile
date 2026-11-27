# Build from the repository root: docker build -f mobilePTDocker/Dockerfile -t mobileptdocker:latest .
FROM node:24.22.1-bookworm-slim AS node

# Ghidra is REA's native decompiler for the .so libraries inside APKs. Releases ship
# Linux decompiler natives for x86_64 only, so arm64 builds compile them here.
FROM ubuntu:24.04 AS ghidra
ARG TARGETARCH
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl g++ gcc make openjdk-25-jdk-headless python3 \
    && rm -rf /var/lib/apt/lists/*
COPY shared/install_artifacts.py shared/rea/ghidra.json /tmp/
RUN python3 /tmp/install_artifacts.py /tmp/ghidra.json "$TARGETARCH"
RUN if [ "$TARGETARCH" = arm64 ]; then \
        cd /opt/ghidra/support/gradle && ./gradlew --no-daemon buildNatives \
        && for built in $(find /opt/ghidra -type d -path '*/build/os/linux_arm_64'); do \
               module="${built%/build/os/linux_arm_64}"; \
               mkdir -p "$module/os/linux_arm_64" && cp -a "$built"/. "$module/os/linux_arm_64/"; \
           done \
        && rm -rf /root/.gradle /opt/ghidra/support/gradle/.gradle \
        && find /opt/ghidra -type d -name build -prune -exec rm -rf {} +; \
    fi \
    && os="linux_$([ "$TARGETARCH" = arm64 ] && echo arm_64 || echo x86_64)" \
    && test -x "/opt/ghidra/Ghidra/Features/Decompiler/os/$os/decompile" \
    && test -x "/opt/ghidra/Ghidra/Features/Decompiler/os/$os/sleigh" \
    && test -x "/opt/ghidra/GPL/DemanglerGnu/os/$os/demangler_gnu_v2_41"

FROM ubuntu:24.04
LABEL maintainer="0xdhanesh <dhanesh.professional@gmail.com>" \
      org.opencontainers.image.title="mobilePTDocker" \
      org.opencontainers.image.description="Android and iOS application pentesting"
ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:/opt/jadx/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SECURITY_ENV=mobilePTDocker
RUN apt-get update && apt-get install -y --no-install-recommends \
    adb \
    apksigner \
    apktool \
    bash \
    binutils \
    ca-certificates \
    curl \
    file \
    git \
    ideviceinstaller \
    jq \
    libimobiledevice-utils \
    libplist-utils \
    openjdk-25-jdk-headless \
    procps \
    python3 \
    python3-pip \
    python3-venv \
    tini \
    unzip \
    usbmuxd \
    wget \
    xz-utils \
    zipalign \
    && rm -rf /var/lib/apt/lists/*
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
ARG REA_VERSION=6.10.1
RUN npm install --global "rea-agents@${REA_VERSION}" && npm cache clean --force
ARG TARGETARCH
COPY shared/install_artifacts.py /opt/security/install_artifacts.py
COPY shared/rea/jadx-mcp.json /opt/security/rea-jadx-mcp.json
COPY mobilePTDocker/artifacts.json /opt/security/artifacts.json
RUN python3 /opt/security/install_artifacts.py /opt/security/rea-jadx-mcp.json "$TARGETARCH" \
    && python3 /opt/security/install_artifacts.py /opt/security/artifacts.json "$TARGETARCH"
COPY --from=ghidra /opt/ghidra /opt/ghidra
RUN ln -s /opt/ghidra/support/analyzeHeadless /usr/local/bin/analyzeHeadless
# REA engine locations live in the image, so neither the shell nor MCP needs host paths.
ENV JAVA_HOME=/usr/lib/jvm/java-25-openjdk-${TARGETARCH} \
    GHIDRA_INSTALL_DIR=/opt/ghidra \
    REA_JADX_MCP_JAR=/opt/rea-engines/jadx/jadx-headless-mcp-0.7.1-all.jar \
    FRIDA_SERVER_DIR=/opt/frida/android
COPY shared/requirements.txt /opt/security/mcp-requirements.txt
COPY mobilePTDocker/requirements.txt /opt/security/requirements.txt
RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir -r /opt/security/mcp-requirements.txt -r /opt/security/requirements.txt
RUN useradd --badname --uid 10001 --create-home --shell /bin/bash 0xdhanesh \
    && mkdir -p /workspace \
    && chown 10001:10001 /workspace
COPY shared/mcp_server.py /opt/security/mcp_server.py
COPY mobilePTDocker/tools.json /opt/security/tools.json
# Static iOS RASP scanner — available as ipa-rasp inside the container
COPY mobilePTDocker/scripts/ipa_rasp_scanner.sh /usr/local/bin/ipa-rasp
RUN chmod +x /usr/local/bin/ipa-rasp
USER 0xdhanesh
WORKDIR /workspace
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/bash"]
