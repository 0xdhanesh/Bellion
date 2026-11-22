# webPTDocker: MCP usage

- Connects the **webPTDocker** image to Claude Code/Desktop, Codex, Grok Build CLI, or Google Antigravity (`agy`).
- Setup examples target local clients running on the same Docker host.
- Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>

## 1. Prepare the image and workspace

On the host in a Bash/Zsh terminal, from the repository root:

```bash
mkdir -p webPTDocker/workspace
docker build -f webPTDocker/Dockerfile -t webptdocker:latest .
docker info
command -v docker
```

- Run the registration commands below from the directory you want mounted as `/workspace`; `$(pwd)` expands to it.
- JSON/TOML configs need a literal absolute path instead (replace `/ABSOLUTE/PATH/TO/workspace`).
- Use Docker's absolute path if a GUI client cannot find `docker` on its PATH.
- The client launches `docker run --rm -i` (no `-t`) and talks to the server over stdin/stdout; there is no port, URL or login.
- The Docker daemon and workspace must be reachable from the machine running the client; hosted chats cannot use this.

## 2. Claude Code

On the host, after step 1:

```bash
claude mcp add --transport stdio --scope user webPTDocker -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=16777216:16777216 --mount "type=bind,src=$(pwd),dst=/workspace" \
  webptdocker:latest python3 /opt/security/mcp_server.py
claude mcp list
claude mcp get webPTDocker
```

Start or restart Claude Code, then open `/mcp` to inspect the connection.

### Claude Desktop

- Open Settings → Developer → Edit Config.
- Merge the server entry from [mcp.json](mcp.json) into `mcpServers`, replace the workspace placeholder, save and restart Claude Desktop.
- Config file: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows).

## 3. Codex CLI / local desktop or IDE client

On the host, after step 1:

```bash
codex mcp add webPTDocker -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=16777216:16777216 --mount "type=bind,src=$(pwd),dst=/workspace" \
  webptdocker:latest python3 /opt/security/mcp_server.py
codex mcp list
codex mcp get webPTDocker
```

Restart the local Codex session and use `/mcp` to inspect available tools.
For longer commands, add timeouts to this server's table in `~/.codex/config.toml`:

```toml
[mcp_servers.webPTDocker]
startup_timeout_sec = 30
tool_timeout_sec = 330
```

`run_tool.timeout` is capped at 300 seconds, so keep the client timeout above it.

## 4. Grok Build CLI

This means the local `grok` coding CLI, not a hosted Grok conversation. On the
host, after step 1:

```bash
grok mcp add --scope user webPTDocker -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=16777216:16777216 --mount "type=bind,src=$(pwd),dst=/workspace" \
  webptdocker:latest python3 /opt/security/mcp_server.py
grok mcp list
grok mcp doctor webPTDocker
```

Start a new Grok session and use `/mcps` to inspect or refresh the connection.
For longer commands set `tool_timeout_sec = 330` for this server in `~/.grok/config.toml`.

## 5. Google Antigravity (`agy`)

On the host, after step 1:

```bash
agy mcp add --type stdio webPTDocker -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=16777216:16777216 --mount "type=bind,src=$(pwd),dst=/workspace" \
  webptdocker:latest python3 /opt/security/mcp_server.py
agy mcp list
```

Flags such as `--type` must precede the server name. Start a new local Antigravity
session and use `/mcp` to inspect/reload it. The installed CLI's exact flags can
be checked with `agy mcp add --help`.

For JSON configuration, merge the server entry from [mcp.json](mcp.json) into
`~/.gemini/config/mcp_config.json` or the workspace's `.agents/mcp_config.json`.
Replace the bind-path placeholder and set `"timeoutSeconds": 330` in this
server's object for long bridge calls. In the IDE, open MCP Servers → Manage MCP
Servers → View raw config to edit the active file.

## 6. Check connectivity and make the first request

In any of these clients, ask:

> Use the webPTDocker MCP server. Call its list_tools tool, report any missing
> executables, then run python3 with args ["-c", "print('MCP connected')"] in
> /workspace with a 30-second timeout. Show the exit code and stdout.

On successful connection we can see two tools: `list_tools` and `run_tool`.

Example `run_tool` payload:

```json
{
  "command": "curl",
  "args": [
    "-I",
    "https://example.com"
  ],
  "cwd": "/workspace",
  "timeout": 30
}
```

## 7. Ask for specific operations

These requests work across the four clients once connected. Replace uppercase
placeholders with your actual authorized scope/device. State the input, desired
output path, execution limits, and whether runtime/network actions are allowed.

### Headers

> Use webPTDocker to fetch only the response headers for https://example.com. Use a 30-second timeout and explain the status, redirects, and security-related headers. Do not follow links or scan other hosts.

### Content discovery

> On my authorized lab https://LAB_HOST, run ffuf with /workspace/wordlist.txt, 2 threads and a rate limit of 5 requests per second. Save JSON to /workspace/ffuf.json. Report matches, filters, and any errors; stay on this host.

### Review a capture

> Read /workspace/flows.mitm with mitmdump in replay-read mode (-nr), without contacting captured URLs. Summarize observed hosts, methods, response codes, and gaps. Do not reproduce credentials in the report.

### SQL injection test

> Test only the id parameter of my authorized lab URL https://LAB_HOST/item?id=1 with sqlmap at level 1 and risk 1. Save outputs under /workspace/sqlmap. Report test evidence and limitations; do not dump database contents.

## 8. Files, argument arrays, and limits

Use `/workspace/...` in tool requests; host paths are used only in Docker's
bind mount. To list files through the bridge, ask it to run:

```json
{
  "command": "python3",
  "args": ["-c", "from pathlib import Path; print('\\n'.join(str(p) for p in Path('/workspace').iterdir()))"],
  "cwd": "/workspace",
  "timeout": 30
}
```

`run_tool` does not interpret shell pipes, `>`, wildcard expansion, or heredocs.
Pass each argument separately. Prefer a tool's output-file option. For a tool
that prints a report, ask the agent to write stdout with Python or run a mounted
Python script that saves it. For example, this explicit bridge call creates a
notes file:

```json
{
  "command": "python3",
  "args": ["-c", "from pathlib import Path; Path('/workspace/notes.txt').write_text('analysis notes\\n')"],
  "cwd": "/workspace",
  "timeout": 30
}
```

Commands run as `0xdhanesh` (UID 10001). Workspace permissions must allow writes;
see [USAGE.md](USAGE.md). Calls have no interactive stdin and a 1–300 second
execution timeout; the bridge kills the command's process group when it ends.
Detached services cannot be kept running across bridge calls. Each output stream
is capped at 64 KiB; save larger output under `/workspace`. Supplied launch args
also cap individual files at 16 MiB; adjust `fsize` deliberately if needed.

For proxy capture, add a deliberate port mapping before the image in the MCP launch arguments. A long-running proxy is better run in a separate shell; bridge commands are killed at their timeout and cannot remain running between calls.

MCP access permits code execution inside the container, including interpreter
and debugger scripting. Use trusted clients and mount only needed artifacts.
For offline analysis add `--network=none` before the image in registration args;
network recon and remote device access then become unavailable. No Docker socket
mount or privileged container is required.

## 9. Troubleshooting and verification

| Symptom | Action |
| --- | --- |
| `docker` not found / ENOENT | Use `command -v docker` on the host, then set that absolute executable path in the client. |
| Docker connection failure | Start the daemon and confirm the client uses the same Docker context/environment. |
| Missing image or invalid mount | Rebuild step 1; use an existing absolute host path, with no unexpanded `$PWD` in JSON/TOML. |
| Server seems to hang when launched manually | A stdio server waits for protocol messages; connect with the client rather than typing shell commands. |
| MCP protocol parse failure | Remove `-t`/`-it`, shell startup banners, and wrappers that print on stdout. |
| Tool unavailable after editing configuration | Restart/reload the MCP server and inspect the client's MCP manager. |
| Permission denied for a report | Check host directory ownership and native Linux UID mapping. |
| Truncated output or timeout | Request a bounded operation, save a report file, and align client/bridge deadlines. |
| External engine or device unavailable | Follow the environment-specific prerequisites; connection alone does not install them. |

On the host, from the repository root:

```bash
./scripts/verify.sh webPTDocker
```

This exercises real image/MCP interactions with local fixtures. The registration
syntax was checked against installed client help and linked documentation on
2026-11-22; this guide does not claim authenticated end-to-end sessions in every
client or live device/provider verification.

## ProjectDiscovery operations through MCP

The bridge also permits `subfinder`, `dnsx`, `httpx-pd`, `katana`, `nuclei`,
`naabu`, and `interactsh-client`. Request argument arrays, not shell pipelines.
For example, ask any configured client:

> Using webPTDocker, probe only the URLs in /workspace/urls.txt with httpx-pd.
> Save status codes, titles, and technology guesses as JSONL to
> /workspace/http.jsonl. Report errors and do not expand the target list.

> Use webPTDocker to run Nuclei against my authorized /workspace/urls.txt,
> using /opt/nuclei-templates, high/critical severity, at 5 requests per second.
> Disable Interactsh with -ni and update checks with -duc. Save JSONL to
> /workspace/nuclei.jsonl. Use a 120-second command timeout and clearly report
> partial coverage if it expires; do not treat matches as verified exploitation.

> Discover passive subdomain candidates for example.com using Subfinder in
> webPTDocker. Save them to /workspace/subdomains.txt. Do not resolve or probe
> discovered hosts until they have been checked against the engagement scope.

The bundled Nuclei template snapshot is read-only. Updating templates is an
explicit network operation; use a writable directory under `/workspace`.
Naabu should use `-scan-type c` in the default non-root container. Katana headless
mode needs additional browser prerequisites. Interactsh runs are bounded by the
bridge timeout and are not persistent services; use the shell for ongoing OAST.
