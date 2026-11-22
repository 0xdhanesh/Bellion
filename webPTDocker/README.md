# webPTDocker

Web application pentesting. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.

## Included tools

Executables: `curl`, `wget`, `dig`, `ffuf`, `gobuster`, `nmap`, `openssl`, `sqlmap`, `mitmdump`, `mitmproxy`, `python3`, `subfinder`, `dnsx`, `httpx-pd`, `katana`, `nuclei`, `naabu`, `interactsh-client`.

Python libraries/packages: `beautifulsoup4>=4.12,<5`, `mitmproxy>=11,<13`, `requests>=2.32,<3`.
The MCP bridge uses the [official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).

## Build and spawn

Run from the repository root with Docker Desktop or Docker Engine running:

```bash
mkdir -p webPTDocker/workspace
docker build -f webPTDocker/Dockerfile -t webptdocker:latest .
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/webPTDocker/workspace,dst=/workspace" \
  webptdocker:latest
# Or build and open the shell with Compose:
docker compose -f webPTDocker/compose.yaml run --build --rm tools
```

Inside the shell (supply your own files and authorized targets):

```bash
curl -I https://example.com
ffuf -u https://example.com/FUZZ -w /workspace/wordlist.txt
mitmdump --listen-host 0.0.0.0 --listen-port 8080
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

No Burp Suite, browser, commercial scanners, or bundled wordlists; supply wordlists in `/workspace`. mitmproxy certificates are created on first use; explicitly trust the lab CA on test devices if intercepting HTTPS. Publish a proxy only when needed with `-p 127.0.0.1:8080:8080`.

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

## Usage guides

- [USAGE.md](USAGE.md): build, shell startup, command examples, outputs, and troubleshooting.
- [MCPUSAGE.md](MCPUSAGE.md): Claude, Codex, Grok CLI, and Antigravity setup with operation prompts.

## ProjectDiscovery tools

Pinned upstream binaries are recorded in [releases.json](releases.json) and
verified against upstream SHA-256 checksum manifests during the build. Both
Linux amd64 and arm64 are supported. ProjectDiscovery HTTPX is named `httpx-pd`
to avoid shadowing the Python `httpx` CLI installed with MCP dependencies.

The image bundles Nuclei templates v10.5.2 under `/opt/nuclei-templates`.
Use `-t /opt/nuclei-templates` explicitly. For portable runtime state, mount
`./workspace` and put provider configuration, templates, wordlists and reports
there. No provider API keys or wordlists are shipped. Subfinder's coverage depends
on configured sources. Katana's standard crawler works as is; its headless mode needs a browser, which is not bundled.
Naabu defaults here should use TCP connect mode (`-scan-type c`) with dropped
capabilities. Interactsh contacts an external OAST service when started; run it
only when that interaction is intended. Nuclei template matches need validation.
See [ProjectDiscovery documentation](https://docs.projectdiscovery.io/opensource).
