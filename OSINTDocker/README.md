# OSINTDocker

OSINT and artifact/website reconnaissance. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.

## Included tools

Executables: `rea`, `androguard`, `apktool`, `binwalk`, `curl`, `wget`, `dig`, `host`, `nslookup`, `whois`, `exiftool`, `file`, `strings`, `readelf`, `nmap`, `openssl`, `rg`, `jq`, `python3`.

Python libraries/packages: `androguard>=4.1,<5`, `beautifulsoup4>=4.12,<5`, `dnspython>=2.7,<3`, `requests>=2.32,<3`.
The MCP bridge uses the [official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).

## Build and spawn

Run from the repository root with Docker Desktop or Docker Engine running:

```bash
mkdir -p OSINTDocker/workspace
docker build -f OSINTDocker/Dockerfile -t osintdocker:latest .
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/OSINTDocker/workspace,dst=/workspace" \
  osintdocker:latest
# Or build and open the shell with Compose:
docker compose -f OSINTDocker/compose.yaml run --build --rm tools
```

Inside the shell (supply your own files and authorized targets):

```bash
whois example.com
dig example.com MX
exiftool /workspace/document.pdf
apktool d /workspace/app.apk -o /workspace/apk
rea analyze-javascript-application /workspace/extracted-app --json
nmap -sT -sV example.com
```

The default account is `0xdhanesh` (UID 10001), with no sudo. On native Linux,
make the workspace writable by UID 10001, or pass `--user "$(id -u):$(id -g)"`
and `-e HOME=/tmp` to `docker run`. Matching Compose overrides must set `user`
and `environment.HOME` too. Docker Desktop normally translates bind permissions.
The images build for the host architecture by default; set `--platform` explicitly
for a different architecture, with matching run settings. Emulation is slower.

## Connect via MCP

Copy the server entry in [mcp.json](mcp.json) into a stdio-capable MCP client's
`mcpServers` map. Replace `/ABSOLUTE/PATH/TO/workspace` with an existing absolute
host path. Build the image first. The client starts an ephemeral container using
`docker run --rm -i` (no TTY); no listening MCP port is required.

The bridge exposes `list_tools` (installation inventory) and `run_tool`:

```json
{"command": "python3", "args": ["-c", "print('MCP connected')"], "cwd": "/workspace", "timeout": 30}
```

Commands use argument arrays, with no shell expansion. Working directories must
resolve under `/workspace`. Timeouts range from 1 to 300 seconds; stdout/stderr
are each truncated to 64 KiB with explicit flags. Exit codes and timeouts are
returned. For long reports, use the tool's output-file option under `/workspace`.
Client tool deadlines should exceed the requested command timeout. Each MCP server
has its own container; files persist only in mounted storage.

## Limitations and access

DNS, WHOIS, and certificate queries avoid direct probing of the target website but still contact third parties; nmap and HTTP requests are active recon. REA is installed with its CLI and native MCP server; Ghidra, IDA, Hopper, JADX, Chromium/CDP, and proprietary engines are not bundled. APK archive inspection works with apktool/Androguard; REA Android code analysis needs an external compatible JADX installation. Website runtime analysis needs an externally configured reachable browser/CDP endpoint. A URL is not a local JavaScript tree: download/export the relevant artifacts first, or use REA browser workflows. No paid API accounts or recon service credentials are included.

Treat MCP access as code execution: Python, debuggers, and tool scripting options
can access all container files and network endpoints. The command manifest is a
convenience list, not a security sandbox. Use a trusted local client and mount only
needed artifacts. Containers have outbound networking by default. Add
`--network=none` for offline analysis (and to the MCP launch arguments). No host
Docker socket or privileged mode is required. The examples drop capabilities;
TCP connect scanning works without raw sockets. Output is buffered to temporary
files, with a 16 MiB file-size limit in the supplied launch configurations.

Ubuntu packages and Python dependencies resolve within their declared ranges at
build time; these are maintained starter environments, not bit-for-bit locked
images. Keep build logs or freeze package versions when reproducibility is needed.

## Native REA MCP server

REA is pinned to `rea-agents@6.10.1`, with Node 24.22.1 per its
[declared runtime requirements](https://github.com/morluto/rea/blob/main/package.json).
The second `rea` entry in `mcp.json` starts `rea mcp` directly, independently of
the command bridge. It exposes REA's native analysis tools rather than only
`run_tool`. There is no need to run `rea setup` inside the image or modify host
client settings during the build. Use container paths such as `/workspace/app.apk`
in REA requests. The two servers see the same mounted workspace.

See the [REA installation and provider guide](https://github.com/morluto/rea/blob/main/docs/getting-started/installation.md)
for optional engines. REA does not install an analysis engine automatically.

## Usage guides

- [USAGE.md](USAGE.md): build, shell startup, command examples, outputs, and troubleshooting.
- [MCPUSAGE.md](MCPUSAGE.md): Claude, Codex, Grok CLI, and Antigravity setup with operation prompts.
