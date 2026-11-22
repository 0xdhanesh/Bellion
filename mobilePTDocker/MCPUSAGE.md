# mobilePTDocker: MCP usage

Connect the **mobilePTDocker** image to Claude Code/Desktop, Codex, Grok Build CLI,
or Google Antigravity (`agy`). Setup examples target local clients running on
the same Docker host. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.

## 1. Prepare the image and workspace

On the host in a Bash/Zsh terminal, from the repository root:

```bash
mkdir -p mobilePTDocker/workspace
docker build -f mobilePTDocker/Dockerfile -t mobileptdocker:latest .
export MCP_WORKSPACE="$PWD/mobilePTDocker/workspace"
docker info
command -v docker
```

Keep using that terminal for the registration commands below, so
`$MCP_WORKSPACE` expands to an existing absolute host path. The client records
that expanded path. JSON/TOML examples instead use a literal placeholder: replace
`/ABSOLUTE/PATH/TO/workspace` yourself; do not rely on shell expansion in JSON.
Use the Docker executable's absolute path if a GUI client's PATH cannot find it.
Place your inputs in the host workspace before requesting analysis.

The MCP client launches a new container with `docker run --rm -i`, **without
`-t` or `-it`**. It starts `/opt/security/mcp_server.py` over stdin/stdout. There
is no published MCP port, HTTP URL, or OAuth login for this local bridge. The
Docker daemon and workspace must be reachable from the machine executing the
MCP server command. Hosted chats cannot directly execute this local command;
this repository does not supply a remote HTTP gateway.

## 2. Claude Code

On the host, after step 1:

```bash
claude mcp add --transport stdio --scope user mobilePTDocker -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=16777216:16777216 --mount "type=bind,src=$MCP_WORKSPACE,dst=/workspace" \
  mobileptdocker:latest python3 /opt/security/mcp_server.py
claude mcp list
claude mcp get mobilePTDocker
```

Start or restart Claude Code, then open `/mcp` to inspect the connection. The
user scope applies across your projects; use `--scope project` instead if you
want registration in the current project's `.mcp.json`. Keep existing servers
when adding entries. See [Claude Code's MCP guide](https://code.claude.com/docs/en/mcp).

### Claude Desktop

Open Settings → Developer → Edit Config. Merge the matching server entry from
[mcp.json](mcp.json) into the existing `mcpServers` map, replace the absolute
workspace placeholder, save, and fully restart Claude Desktop. On macOS the
file is `~/Library/Application Support/Claude/claude_desktop_config.json`;
on Windows it is `%APPDATA%\Claude\claude_desktop_config.json`.
See the [local MCP setup guide](https://modelcontextprotocol.io/docs/develop/connect-local-servers).
Do not replace unrelated configuration. With Windows Docker Desktop, use a
host path valid for the environment launching `docker`; these shell examples
are intended for Bash/Zsh or a configured WSL workflow.

## 3. Codex CLI / local desktop or IDE client

On the host, after step 1:

```bash
codex mcp add mobilePTDocker -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=16777216:16777216 --mount "type=bind,src=$MCP_WORKSPACE,dst=/workspace" \
  mobileptdocker:latest python3 /opt/security/mcp_server.py
codex mcp list
codex mcp get mobilePTDocker
```

Restart the local Codex session and use `/mcp` to inspect available tools.
For explicit timeouts, edit this server's table in `~/.codex/config.toml`
(or the trusted project's `.codex/config.toml`). This is an **alternative
configuration of the same server**, not a second entry to append:

```toml
[mcp_servers.mobilePTDocker]
command = "docker"
args = [
  "run",
  "--rm",
  "-i",
  "--cap-drop=ALL",
  "--security-opt=no-new-privileges",
  "--ulimit",
  "fsize=16777216:16777216",
  "--mount",
  "type=bind,src=/ABSOLUTE/PATH/TO/workspace,dst=/workspace",
  "mobileptdocker:latest",
  "python3",
  "/opt/security/mcp_server.py"
]
startup_timeout_sec = 30
tool_timeout_sec = 330
```

Replace the placeholder path. Codex uses TOML, so the JSON `mcpServers` object
from `mcp.json` cannot be pasted directly into `config.toml`.
See [OpenAI's MCP configuration guide](https://developers.openai.com/codex/mcp/).
The client timeout is distinct from `run_tool.timeout` (maximum 300 seconds).

## 4. Grok Build CLI

This means the local `grok` coding CLI, not a hosted Grok conversation. On the
host, after step 1:

```bash
grok mcp add --scope user mobilePTDocker -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=16777216:16777216 --mount "type=bind,src=$MCP_WORKSPACE,dst=/workspace" \
  mobileptdocker:latest python3 /opt/security/mcp_server.py
grok mcp list
grok mcp doctor mobilePTDocker
```

Start a new Grok session and use `/mcps` to inspect or refresh the connection.
User registration uses `~/.grok/config.toml`; `--scope project` writes the
current project's `.grok/config.toml`. This server uses the same `command` and
`args` structure as the Codex TOML example; a `tool_timeout_sec = 330` setting
provides room for a 300-second bridge command. Do not overwrite other entries.
See [Grok Build's MCP guide](https://docs.x.ai/build/features/mcp-servers).

## 5. Google Antigravity (`agy`)

On the host, after step 1:

```bash
agy mcp add --type stdio mobilePTDocker -- docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges --ulimit fsize=16777216:16777216 --mount "type=bind,src=$MCP_WORKSPACE,dst=/workspace" \
  mobileptdocker:latest python3 /opt/security/mcp_server.py
agy mcp list
```

Flags such as `--type` must precede the server name. Start a new local Antigravity
session and use `/mcp` to inspect/reload it. The installed CLI's exact flags can
be checked with `agy mcp add --help`.

For JSON configuration, merge the server entry from [mcp.json](mcp.json) into
`~/.gemini/config/mcp_config.json` or the workspace's `.agents/mcp_config.json`.
Replace the bind-path placeholder and set `"timeoutSeconds": 330` in this
server's object for long bridge calls. In the IDE, open MCP Servers → Manage MCP
Servers → View raw config to edit the active file. Preserve existing entries,
then reload the server/session. See [Antigravity's MCP guide](https://antigravity.google/docs/mcp).

## 6. Check connectivity and make the first request

In any of these clients, ask:

> Use the mobilePTDocker MCP server. Call its list_tools tool, report any missing
> executables, then run python3 with args ["-c", "print('MCP connected')"] in
> /workspace with a 30-second timeout. Show the exit code and stdout.

A successful check returns installation booleans from `list_tools` and
`MCP connected` in the command output. `list_tools` is this bridge's inventory
tool; it is separate from MCP's protocol-level tool discovery. Clients can
prefix tool names with the server name, so select the tool belonging to
`mobilePTDocker` when several bridges are connected.

The bridge exposes only `list_tools` and `run_tool`. A concrete operation payload
for `run_tool` is:

```json
{
  "command": "androguard",
  "args": [
    "apkid",
    "/workspace/app.apk"
  ],
  "cwd": "/workspace",
  "timeout": 60
}
```

The tool result includes `exit_code`, `timed_out`, `stdout`, `stderr`,
`stdout_truncated`, and `stderr_truncated`. Inspect all of them. A valid MCP
response can contain a failed command. Invalid commands, cwd values, or timeout
values instead produce a tool error. Output depends on your input/target;
missing files, no matches, or unavailable services are not successful findings.

## 7. Ask for specific operations

These requests work across the four clients once connected. Replace uppercase
placeholders with your actual authorized scope/device. State the input, desired
output path, execution limits, and whether runtime/network actions are allowed.

### APK metadata

> Use mobilePTDocker to inspect /workspace/app.apk offline. Report the package ID, version, declared permissions, exported components and intent filters from the manifest. Decode into /workspace/decoded-apk and cite the inspected files; do not install or launch it.

### IPA metadata

> Extract /workspace/app.ipa into /workspace/ipa. Locate its Info.plist and report the bundle ID, URL schemes, usage-description keys, and transport-security settings. Explain any encrypted-code limitations; do not claim iOS runtime behavior.

### Android log snapshot

> List reachable ADB devices with mobilePTDocker. If exactly one authorized lab device is available, collect a finite 200-line logcat snapshot with -d -t 200 and save it to /workspace/logcat.txt. Summarize errors without streaming indefinitely.

### Frida process inventory

> Use frida-ps through mobilePTDocker to list processes on my lab Frida endpoint DEVICE_IP:27042. Do not attach, spawn, or load a script. Report connectivity or version errors exactly.

### iOS inventory

> Using the configured usbmuxd connection in mobilePTDocker, list iOS devices and validate the existing pairing for UDID. Report available device metadata. Do not install apps or change pairing.

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

Device settings must also be present in the MCP Docker args: add the ADB server environment variable, Linux host-gateway mapping, or usbmuxd socket mount before the image as needed. A shell container and an MCP container are separate processes. Use finite ADB log dumps; interactive Frida sessions belong in the shell. Frida script loading and app installation change device state.

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
./scripts/verify.sh mobilePTDocker
```

This exercises real image/MCP interactions with local fixtures. The registration
syntax was checked against installed client help and linked documentation on
2026-11-22; this guide does not claim authenticated end-to-end sessions in every
client or live device/provider verification.
