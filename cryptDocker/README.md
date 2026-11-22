# cryptDocker

Cryptographic implementation analysis. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.

## Included tools

Executables: `openssl`, `gpg`, `hashcat`, `john`, `python3`.

Python libraries/packages: `cryptography>=44,<49`, `gmpy2>=2.2,<3`, `pycryptodome>=3.21,<4`, `sympy>=1.13,<2`, `z3-solver>=4.13,<5`.
The MCP bridge uses the [official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).

## Build and spawn

Run from the repository root with Docker Desktop or Docker Engine running:

```bash
mkdir -p cryptDocker/workspace
docker build -f cryptDocker/Dockerfile -t cryptdocker:latest .
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/cryptDocker/workspace,dst=/workspace" \
  cryptdocker:latest
# Or build and open the shell with Compose:
docker compose -f cryptDocker/compose.yaml run --build --rm tools
```

Inside the shell (supply your own files and authorized targets):

```bash
openssl version
openssl x509 -in /workspace/certificate.pem -text -noout
python3 -c "from Crypto.Hash import SHA256; print(SHA256.new(b'example').hexdigest())"
python3 -c "import sympy; print(sympy.factorint(65535))"
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

No SageMath or GPU runtime is bundled. Hashcat runs on the CPU through the bundled PoCL OpenCL runtime; supply wordlists in `/workspace`. GPU passthrough requires compatible native Linux drivers and an additional runtime; Docker Desktop on macOS does not provide CUDA. Distribution John supports fewer formats than Jumbo. Static review and test vectors cannot prove a cryptographic implementation secure.

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
