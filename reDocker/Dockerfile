# Build from the repository root: docker build -f reDocker/Dockerfile -t redocker:latest .
FROM node:24.22.1-bookworm-slim AS node

# Ghidra is REA's native decompiler. Releases ship Linux decompiler natives for
# x86_64 only, so arm64 builds compile them here.
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

# Rizin publishes a static build for x86_64 only; build the same release from
# verified source for every architecture so both images match.
FROM ubuntu:24.04 AS rizin
ARG TARGETARCH
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl g++ gcc meson ninja-build pkg-config python3 \
    && rm -rf /var/lib/apt/lists/*
COPY shared/install_artifacts.py reDocker/rizin.json /tmp/
RUN python3 /tmp/install_artifacts.py /tmp/rizin.json "$TARGETARCH"
WORKDIR /src/rizin
RUN meson setup build --prefix=/opt/rizin --buildtype=release -Dportable=true \
    && ninja -C build install \
    && /opt/rizin/bin/rizin -v

FROM ubuntu:24.04
LABEL maintainer="0xdhanesh <dhanesh.professional@gmail.com>" \
      org.opencontainers.image.title="reDocker" \
      org.opencontainers.image.description="ELF and native binary reverse engineering"
ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:/opt/rizin/bin:/opt/wabt/bin:$PATH" \
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
    openjdk-25-jdk-headless \
    patchelf \
    procps \
    python3 \
    python3-pip \
    python3-venv \
    strace \
    tini \
    unzip \
    wget \
    yara \
    && rm -rf /var/lib/apt/lists/*
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
ARG REA_VERSION=6.10.1
RUN npm install --global "rea-agents@${REA_VERSION}" && npm cache clean --force
ARG TARGETARCH
COPY shared/install_artifacts.py /opt/security/install_artifacts.py
COPY reDocker/artifacts.json /opt/security/artifacts.json
RUN python3 /opt/security/install_artifacts.py /opt/security/artifacts.json "$TARGETARCH"
COPY --from=ghidra /opt/ghidra /opt/ghidra
COPY --from=rizin /opt/rizin /opt/rizin
RUN ln -s /opt/ghidra/support/analyzeHeadless /usr/local/bin/analyzeHeadless
COPY shared/requirements.txt /opt/security/mcp-requirements.txt
COPY reDocker/requirements.txt /opt/security/requirements.txt
RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir -r /opt/security/mcp-requirements.txt -r /opt/security/requirements.txt
# REA engine locations live in the image, so neither the shell nor MCP needs host paths.
ENV JAVA_HOME=/usr/lib/jvm/java-25-openjdk-${TARGETARCH} \
    GHIDRA_INSTALL_DIR=/opt/ghidra \
    REA_RIZIN_COMMAND=/opt/rizin/bin/rizin \
    REA_GDB_COMMAND=/usr/bin/gdb \
    REA_OBJDUMP_COMMAND=/usr/bin/objdump \
    REA_WABT_BIN_DIRECTORY=/opt/wabt/bin \
    REA_PWNTOOLS_PYTHON=/opt/venv/bin/python3
RUN useradd --badname --uid 10001 --create-home --shell /bin/bash 0xdhanesh \
    && mkdir -p /workspace \
    && chown 10001:10001 /workspace
COPY shared/mcp_server.py /opt/security/mcp_server.py
COPY reDocker/tools.json /opt/security/tools.json
USER 0xdhanesh
WORKDIR /workspace
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/bash"]
