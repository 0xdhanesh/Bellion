# reDocker

ELF and native binary reverse engineering. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.

## Included tools

Executables: `rea`, `analyzeHeadless` (Ghidra), `rizin`, `rz-bin`, `wasm-objdump`, `wasm2wat`, `wasm-validate`, `file`, `readelf`, `objdump`, `strings`, `nm`, `gdb`, `strace`, `ltrace`, `gcc`, `make`, `nasm`, `patchelf`, `eu-readelf`, `yara`, `pwn`, `checksec`, `java`, `python3`.

Python libraries/packages: `capstone>=5,<6`, `lief>=0.16,<1`, `pefile>=2024.8.26`, `pwntools==4.15.0`, `pyelftools==0.33`, `unicorn==2.1.2`.

Everything a tool needs ships in the image; see [Bundled engines](#bundled-engines). Nothing is read from the host except the mounted workspace.
The MCP bridge uses the [official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).

## Build and spawn

Run from the repository root with Docker Desktop or Docker Engine running:

```bash
mkdir -p reDocker/workspace
docker build -f reDocker/Dockerfile -t redocker:latest .
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=2147483648:2147483648 \
  --mount "type=bind,src=$PWD/reDocker/workspace,dst=/workspace" \
  redocker:latest
# Or build and open the shell with Compose:
docker compose -f reDocker/compose.yaml run --build --rm tools
```

Inside the shell (supply your own files and authorized targets):

```bash
file /workspace/sample
readelf -h /workspace/sample
objdump -d /workspace/sample
gdb /workspace/sample
rizin -A /workspace/sample
rea doctor --provider ghidra   # bundled Ghidra reports healthy
```

The default account is `0xdhanesh` (UID 10001), with no sudo. On native Linux,
make the workspace writable by UID 10001, or pass `--user "$(id -u):$(id -g)"`
and `-e HOME=/tmp` to `docker run`. Matching Compose overrides must set `user`
and `environment.HOME` too. Docker Desktop normally translates bind permissions.
The images build for the host architecture by default; set `--platform` explicitly
for a different architecture, with matching run settings. Emulation is slower.

## Connect via MCP

Copy the server entries in [mcp.json](mcp.json) into a stdio-capable MCP client's
`mcpServers` map. Replace `/ABSOLUTE/PATH/TO/workspace` with an existing absolute
host path. Build the image first. The client starts an ephemeral container using
`docker run --rm -i` (no TTY); no listening MCP port is required.

The `rea` entry starts `rea mcp` in the same image, exposing REA's native analysis
tools (rather than only `run_tool`) with the bundled engines already configured. Do not
run `rea setup` or set engine paths in the client: they are baked into the image.
Use container paths such as `/workspace/app.apk` in REA requests.

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

No GUI or commercial decompiler is bundled; Ghidra 12.2 runs headless for REA and `analyzeHeadless`. Native debugging needs a matching architecture and kernel support; emulation on Apple Silicon does not guarantee ptrace works. Add `--platform linux/amd64` at build and run for x86 tools. Only for debugging, add `--cap-add SYS_PTRACE --security-opt seccomp=unconfined` (also on the MCP launch if needed). Executing an analyzed sample runs it with the container network and writable mounts.

Treat MCP access as code execution: Python, debuggers, and tool scripting options
can access all container files and network endpoints. The command manifest is a
convenience list, not a security sandbox. Use a trusted local client and mount only
needed artifacts. Containers have outbound networking by default. Add
`--network=none` for offline analysis (and to the MCP launch arguments). No host
Docker socket or privileged mode is required. The examples drop capabilities;
TCP connect scanning works without raw sockets. Output is buffered to temporary
files, with a 2 GiB file-size limit in the supplied launch configurations: Ghidra
projects for real binaries exceed the 16 MiB limit the other images use.

Ubuntu packages and Python dependencies resolve within their declared ranges at
build time; these are maintained starter environments, not bit-for-bit locked
images. Keep build logs or freeze package versions when reproducibility is needed.

## Bundled engines

| Engine | Version | Location | Selected by |
| --- | --- | --- | --- |
| REA (`rea-agents`) with Node.js | 6.10.1 / 24.22.1 | `/usr/local/lib/node_modules/rea-agents` | `rea` on `PATH` |
| Ghidra (REA native decompiler) | 12.2, SHA-256 pinned | `/opt/ghidra` | `GHIDRA_INSTALL_DIR` |
| OpenJDK (Ghidra 12.2 requires 25) | 25 | `/usr/lib/jvm/java-25-openjdk-*` | `JAVA_HOME` |
| Rizin, built from verified source | 0.9.1 | `/opt/rizin` | `REA_RIZIN_COMMAND` |
| WABT | 1.0.42, SHA-256 pinned | `/opt/wabt/bin` | `REA_WABT_BIN_DIRECTORY` |
| GDB / objdump | Ubuntu 24.04 | `/usr/bin` | `REA_GDB_COMMAND`, `REA_OBJDUMP_COMMAND` |
| pwntools profile REA verifies | 4.15.0 | `/opt/venv` | `REA_PWNTOOLS_PYTHON` |

The variables are set with `ENV` in the Dockerfile, so the shell, the command
bridge and `rea mcp` all see the same engines without any host configuration.
Download pins live in [artifacts.json](artifacts.json), [rizin.json](rizin.json)
and [shared/rea](../shared/rea); [shared/install_artifacts.py](../shared/install_artifacts.py)
refuses any file whose SHA-256 differs. Ghidra's release has Linux decompiler
natives for x86_64 only, and Rizin publishes a static build for x86_64 only, so
builder stages compile both for arm64. REA supports its pwntools provider on Linux
x64 only, so build with `--platform linux/amd64` for that workflow on Apple Silicon.

Proprietary engines REA can also drive (IDA Pro, Hopper, JEB, Kuna) are not
redistributable and are not bundled. REA works without them.

## Usage guides

- [USAGE.md](USAGE.md): build, shell startup, command examples, outputs, and troubleshooting.
- [MCPUSAGE.md](MCPUSAGE.md): Claude, Codex, Grok CLI, and Antigravity setup with operation prompts.
