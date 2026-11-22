# reDocker: MCP usage

- Connects the **reDocker** image to Claude Code/Desktop, Codex, Grok Build CLI, or Google Antigravity (`agy`).
- Setup examples target local clients running on the same Docker host.
- Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>

## 1. Prepare the image and workspace

On the host in a Bash/Zsh terminal, from the repository root:

```bash
mkdir -p reDocker/workspace
docker build -f reDocker/Dockerfile -t redocker:latest .
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
claude mcp add --transport stdio --scope user reDocker -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=2147483648:2147483648 --mount "type=bind,src=$(pwd),dst=/workspace" \
  redocker:latest python3 /opt/security/mcp_server.py
claude mcp list
claude mcp get reDocker
```

Start or restart Claude Code, then open `/mcp` to inspect the connection.

### Claude Desktop

- Open Settings → Developer → Edit Config.
- Merge the server entry from [mcp.json](mcp.json) into `mcpServers`, replace the workspace placeholder, save and restart Claude Desktop.
- Config file: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows).

## 3. Codex CLI / local desktop or IDE client

On the host, after step 1:

```bash
codex mcp add reDocker -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=2147483648:2147483648 --mount "type=bind,src=$(pwd),dst=/workspace" \
  redocker:latest python3 /opt/security/mcp_server.py
codex mcp list
codex mcp get reDocker
```

Restart the local Codex session and use `/mcp` to inspect available tools.
For longer commands, add timeouts to this server's table in `~/.codex/config.toml`:

```toml
[mcp_servers.reDocker]
startup_timeout_sec = 30
tool_timeout_sec = 330
```

`run_tool.timeout` is capped at 300 seconds, so keep the client timeout above it.

## 4. Grok Build CLI

This means the local `grok` coding CLI, not a hosted Grok conversation. On the
host, after step 1:

```bash
grok mcp add --scope user reDocker -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=2147483648:2147483648 --mount "type=bind,src=$(pwd),dst=/workspace" \
  redocker:latest python3 /opt/security/mcp_server.py
grok mcp list
grok mcp doctor reDocker
```

Start a new Grok session and use `/mcps` to inspect or refresh the connection.
For longer commands set `tool_timeout_sec = 330` for this server in `~/.grok/config.toml`.

## 5. Google Antigravity (`agy`)

On the host, after step 1:

```bash
agy mcp add --type stdio reDocker -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=2147483648:2147483648 --mount "type=bind,src=$(pwd),dst=/workspace" \
  redocker:latest python3 /opt/security/mcp_server.py
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

> Use the reDocker MCP server. Call its list_tools tool, report any missing
> executables, then run python3 with args ["-c", "print('MCP connected')"] in
> /workspace with a 30-second timeout. Show the exit code and stdout.

On successful connection we can see two tools: `list_tools` and `run_tool`.

Example `run_tool` payload:

```json
{
  "command": "readelf",
  "args": [
    "-h",
    "/workspace/sample"
  ],
  "cwd": "/workspace",
  "timeout": 30
}
```

## 7. Ask for specific operations

These requests work across the four clients once connected. Replace uppercase
placeholders with your actual authorized scope/device. State the input, desired
output path, execution limits, and whether runtime/network actions are allowed.

### Static ELF triage

> Use reDocker to inspect /workspace/sample without executing it. Report format, architecture, entry point, sections, symbols, linked libraries, and mitigations. Save the raw listings under /workspace/results and cite the evidence for each conclusion.

### Disassembly

> Disassemble /workspace/sample with objdump in reDocker. Save the listing to /workspace/disassembly.txt and explain the available main function if present. If symbols are missing, say so; do not invent function names or source code.

### Rule scan

> Apply only /workspace/rules.yar to /workspace/sample using reDocker. Report matching rule names and exit status. Do not execute the input; distinguish no matches from a scan error.

### Finite dynamic trace

> Execute my authorized lab sample /workspace/demo in reDocker with strace for at most 15 seconds, using the debug-enabled offline configuration. Save calls to /workspace/syscalls.txt and summarize observed file/network syscalls. Report a timeout explicitly.

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
also cap individual files at 2 GiB (Ghidra and JADX workspaces outgrow 16 MiB); adjust `fsize` deliberately if needed.

For debugging or strace, add --cap-add=SYS_PTRACE and --security-opt=seccomp=unconfined before the image in the MCP args. Use --network=none for offline work. The bridge has no interactive stdin, so use GDB batch commands (-batch -ex ...) or the shell for an interactive session. Native tracing remains dependent on host architecture and kernel support.

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
| External engine or device unavailable | Engines are bundled: run `rea doctor` in the image. Devices and proprietary engines remain external. |

On the host, from the repository root:

```bash
./scripts/verify.sh reDocker
```

This exercises real image/MCP interactions with local fixtures. The registration
syntax was checked against installed client help and linked documentation on
2026-11-22; this guide does not claim authenticated end-to-end sessions in every
client or live device/provider verification.

## 10. Connect the native REA server as well

The repository's `mcp.json` calls this entry `rea`. If another plugin already
registers that name, rename it; the commands below use `re-rea`. It is optional
and independent of the command bridge. Its engines (Ghidra 12.2, Rizin 0.9.1, WABT 1.0.42, GDB and pwntools 4.15.0) are bundled and
configured inside the image: do not run `rea setup` or set engine paths in the
client. Run the applicable command from the host directory you want mounted as
`/workspace`:

### Claude Code

```bash
claude mcp add --transport stdio --scope user re-rea -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=2147483648:2147483648 --mount "type=bind,src=$(pwd),dst=/workspace" \
  redocker:latest rea mcp
```

### Codex

```bash
codex mcp add re-rea -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=2147483648:2147483648 --mount "type=bind,src=$(pwd),dst=/workspace" \
  redocker:latest rea mcp
```

### Grok Build

```bash
grok mcp add --scope user re-rea -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=2147483648:2147483648 --mount "type=bind,src=$(pwd),dst=/workspace" \
  redocker:latest rea mcp
```

### Antigravity

```bash
agy mcp add --type stdio re-rea -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=2147483648:2147483648 --mount "type=bind,src=$(pwd),dst=/workspace" \
  redocker:latest rea mcp
```

For Claude Desktop or Antigravity JSON, merge the `rea` entry from
[mcp.json](mcp.json), rename its key if needed, and replace the workspace path.
For Codex/Grok TOML, use the bridge's args above but replace the final
`"python3", "/opt/security/mcp_server.py"` pair with `"rea", "mcp"`. Native
decompilation can take minutes on large inputs: give the client a generous tool
deadline.

Ask the client to discover `re-rea` tools, then open `/workspace/sample` and
request an overview, procedures and pseudocode. Export needed evidence before ending the REA session; files in the
shared mount persist, while in-memory sessions do not.
