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
