# Ubuntu Binary Analysis Environment
# Optimized for x86_64 binary analysis with Rosetta 2 support on Apple Silicon

FROM --platform=linux/amd64 ubuntu:22.04

LABEL maintainer="0xdhanesh <dhanesh.professional@gmail.com>"
LABEL description="Ubuntu 22.04 environment with binary analysis and reverse engineering tools"
LABEL version="1.0"

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install binary analysis tools and clean up in single layer
RUN apt-get update && apt-get install -y \
    binutils \
    coreutils \
    file \
    gdb \
    ltrace \
    strace \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /analysis

CMD ["/bin/bash"]
