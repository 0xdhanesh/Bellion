# Security Docker Environments

Five CLI environments for security research, maintained by **0xdhanesh**
<dhanesh.professional@gmail.com>. Each includes a non-root shell and a local
stdio MCP bridge for running its tools from a trusted agent client.

| Environment | Scope | Main tools |
| --- | --- | --- |
| [webPTDocker](webPTDocker/) | Web application pentesting | ffuf, gobuster, sqlmap, nmap, mitmproxy |
| [mobilePTDocker](mobilePTDocker/) | Android and iOS applications | ADB, apktool, Androguard, Frida, libimobiledevice |
| [reDocker](reDocker/) | ELF and native binaries | GDB, binutils, strace, YARA, pwntools, Capstone, LIEF |
| [cryptDocker](cryptDocker/) | Cryptographic implementations | OpenSSL, SymPy, GMP, PyCryptodome, Z3, John, hashcat |
| [OSINTDocker](OSINTDocker/) | Artifacts and passive/active recon | REA, WHOIS, DNS tools, ExifTool, binwalk, nmap, apktool |

## Quick start

Install Docker Engine or Docker Desktop, start its daemon, and clone this repo.
Build with the **repository root as context** because the images use `shared/`:

```bash
mkdir -p webPTDocker/workspace
docker build -f webPTDocker/Dockerfile -t webptdocker:latest .
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/webPTDocker/workspace,dst=/workspace" \
  webptdocker:latest
```

Or use `docker compose -f webPTDocker/compose.yaml run --build --rm tools`.
Each environment README covers its toolset, examples, device connections,
architecture requirements, and limitations. All image tags are lowercase.

## MCP access

Each directory includes `mcp.json`. Merge the desired server entry into your
stdio MCP client's configuration and replace the example absolute workspace
path. Build the image first. The client starts `docker run --rm -i` automatically;
there is no HTTP endpoint or published MCP port.

The bridge exposes `list_tools` and `run_tool(command, args, cwd, timeout)` using
the [official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).
OSINTDocker also includes an independent native [REA](https://github.com/morluto/rea)
MCP server, launched with `rea mcp`, with its own tools. REA's optional analysis
engines are separate prerequisites; see [OSINTDocker](OSINTDocker/README.md).

MCP access grants code execution inside the container. Mount only needed files,
use trusted clients, and add `--network=none` for offline artifact work. Reports
persist in `/workspace`; other container changes disappear at exit. Tools
cannot exceed the runtime's host, architecture, device, or driver capabilities.

## Platforms and limitations

Images use Ubuntu 24.04 and build for the host architecture. Foreign binaries
may be inspected statically, but native execution/debugging requires compatible
architecture and kernel features. On Apple Silicon, an explicit
`--platform linux/amd64` build/run uses Docker's configured emulation; ptrace,
GPU access, and device passthrough are not guaranteed. Linux containers cannot
run Apple's iOS Simulator or Xcode. No privileged mode, sudo, or host Docker
socket is needed for the default configurations.

All containers use `0xdhanesh` (UID 10001). Native Linux bind mounts may need
ownership adjustment or an explicit user override; see each README. Dependency
ranges and Ubuntu repositories resolve at build time; only REA and its Node
runtime are pinned. These images are starting environments rather than
reproducible forensic appliances.

## Validation

```bash
./scripts/verify.sh                 # Build and verify all environments
./scripts/verify.sh webPTDocker     # Verify one environment
```

Checks validate Compose configuration, image builds, the runtime identity, all
manifest executables, real MCP initialization and tool calls, exit codes,
timeouts, output truncation, argument handling, and invalid requests. OSINT also
checks the independent REA MCP server. They run offline after the build and do
not probe external targets. CI runs the same checks on Linux amd64; other
architectures and physical-device sessions need separate verification.

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under [MIT](LICENSE); bundled
tools retain their own licenses.

## Shell helpers for this project

These Bash/Zsh functions adapt the pasted Docker shortcuts to this repository's
five images. Add them to `~/.zshrc` or `~/.bashrc`, then reload that file with
`source ~/.zshrc` or `source ~/.bashrc`. Build the images once from the repository
root before using the helpers from any directory:

```bash
for environment in webPTDocker mobilePTDocker reDocker cryptDocker OSINTDocker; do
  image=$(printf '%s' "$environment" | tr '[:upper:]' '[:lower:]')
  docker build -f "$environment/Dockerfile" -t "$image:latest" .
done
```

The `here` helpers mount your current directory read/write at `/workspace` and
use it as the working directory. They quote paths containing spaces and retain
the image's `0xdhanesh` account. See the permissions guidance above for native
Linux bind mounts. Files saved under `/workspace` remain on your host.

```bash
# Shared defaults for this project's containers.
_securitydocker() {
    docker run --rm --cap-drop=ALL --security-opt=no-new-privileges \
        --ulimit fsize=16777216:16777216 "$@"
}

_securitydockerhere() {
    _securitydocker --mount "type=bind,src=${PWD},dst=/workspace" \
        --workdir /workspace "$@"
}

# Generic shells: Docker options go before the image; shell arguments after it.
dockershell() {
    _securitydocker -it --entrypoint=/bin/bash "$@"
}

dockershellsh() {
    _securitydocker -it --entrypoint=/bin/sh "$@"
}

dockershellhere() {
    _securitydockerhere -it --entrypoint=/bin/bash "$@"
}

dockershellshhere() {
    _securitydockerhere -it --entrypoint=/bin/sh "$@"
}

# Open a shell in one of the five environments, with the current folder mounted.
webpthere() {
    dockershellhere webptdocker:latest "$@"
}

mobilepthere() {
    dockershellhere mobileptdocker:latest "$@"
}

rehere() {
    dockershellhere redocker:latest "$@"
}

crypthere() {
    dockershellhere cryptdocker:latest "$@"
}

osinthere() {
    dockershellhere osintdocker:latest "$@"
}

# Direct tool shortcuts, using tools actually installed in these images.
sqlmaphere() {
    _securitydockerhere -it webptdocker:latest sqlmap "$@"
}

apktoolhere() {
    _securitydockerhere -it mobileptdocker:latest apktool "$@"
}

gdbhere() {
    _securitydockerhere -it --cap-add=SYS_PTRACE \
        --security-opt=seccomp=unconfined redocker:latest gdb "$@"
}

opensslhere() {
    _securitydockerhere -it cryptdocker:latest openssl "$@"
}

reahere() {
    _securitydockerhere -it osintdocker:latest rea "$@"
}

exiftoolhere() {
    _securitydockerhere -it osintdocker:latest exiftool "$@"
}

# Serve the current directory over HTTP, reachable from the host on port 8000.
httphere() {
    _securitydockerhere -it -p 127.0.0.1:8000:8000 webptdocker:latest \
        python3 -m http.server 8000 --bind 0.0.0.0 "$@"
}

# MCP uses stdin/stdout without a TTY. Pass an image, then optional Docker flags.
dockermcphere() {
    if [ "$#" -eq 0 ]; then
        printf '%s\n' 'Usage: dockermcphere IMAGE [DOCKER_OPTIONS...]' >&2
        return 2
    fi
    local image="$1"
    shift
    _securitydockerhere -i "$@" "$image" python3 /opt/security/mcp_server.py
}

# Independent REA MCP server, also without a TTY.
reamcphere() {
    _securitydockerhere -i "$@" osintdocker:latest rea mcp
}
```

Examples, run from the directory holding your artifacts:

```bash
webpthere                              # Interactive web testing shell
mobilepthere                           # Interactive Android/iOS tooling shell
rehere                                 # Interactive native binary analysis shell
crypthere                              # Interactive crypto analysis shell
osinthere                              # Interactive OSINT/recon shell

dockershell webptdocker:latest          # Shell without a host mount
dockershellshhere mobileptdocker:latest # /bin/sh with the current folder mounted
dockershellhere --network=none redocker:latest

sqlmaphere --help
apktoolhere d /workspace/app.apk -o /workspace/decoded
gdbhere /workspace/sample
opensslhere dgst -sha256 /workspace/sample
reahere analyze-javascript-application /workspace/extracted-app --json
exiftoolhere /workspace/document.pdf
httphere                               # Visit http://127.0.0.1:8000; Ctrl-C to stop
```

`gdbhere` enables ptrace and relaxes seccomp for debugging; it still requires
compatible host architecture/kernel support. Use `dockershellhere --network=none
redocker:latest` for offline static work. `httphere` serves the entire current
directory without authentication, so choose the directory deliberately. This
Python HTTP server provides basic file serving; it does not supply HTTPS,
WebDAV, SMB, or request-body uploads. The Windows-context, Impacket, Metasploit,
and specialized serving shortcuts from the original snippet depend on images
outside this project and are replaced here by the available shells and tools.

`dockermcphere webptdocker:latest --network=none` and `reamcphere` are stdio MCP
launchers, not interactive shells. They wait for MCP protocol messages. For an
MCP client that launches a shell, source your helper file explicitly and change
to the intended host workspace before invoking one. Clients that execute
commands directly should use the supplied `mcp.json` entries with an absolute
workspace path; shell functions are not standalone executables.
