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

## Detailed usage guides

| Container | Commands and shell setup | MCP clients and operation prompts |
| --- | --- | --- |
| webPTDocker | [USAGE.md](webPTDocker/USAGE.md) | [MCPUSAGE.md](webPTDocker/MCPUSAGE.md) |
| mobilePTDocker | [USAGE.md](mobilePTDocker/USAGE.md) | [MCPUSAGE.md](mobilePTDocker/MCPUSAGE.md) |
| reDocker | [USAGE.md](reDocker/USAGE.md) | [MCPUSAGE.md](reDocker/MCPUSAGE.md) |
| cryptDocker | [USAGE.md](cryptDocker/USAGE.md) | [MCPUSAGE.md](cryptDocker/MCPUSAGE.md) |
| OSINTDocker | [USAGE.md](OSINTDocker/USAGE.md) | [MCPUSAGE.md](OSINTDocker/MCPUSAGE.md) |

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

## Expected outputs from each container

Starting a container opens a shell; it does not automatically scan a target or
create a report. Outputs depend on the command, supplied artifact/target, and
available device or analysis provider. The examples below run **inside the
corresponding container shell**, with inputs mounted under `/workspace`. Save
reports there to keep them after the container exits.

### OSINTDocker

| Tool/workflow | Expected output |
| --- | --- |
| `dig`, `host`, `whois` | DNS records, resolved addresses, and registration data when publicly available; redacted records, empty answers, or lookup errors are also possible. |
| `exiftool`, `file`, `binwalk` | File type, embedded metadata, and candidate embedded-file signatures/offsets. Metadata may be absent; signature matches need verification. |
| `nmap -sT -sV` | Reachable ports, port states, and service/version guesses for the scanned target. |
| `apktool`, Androguard | Decoded APK resources/manifest and Android analysis results, depending on the selected command. |
| REA JavaScript analysis | Structured JSON containing an application graph, analysis evidence, coverage, limitations, and unresolved information. Optional provider-dependent workflows can report missing prerequisites. |

Example: save metadata as JSON and inspect a locally extracted JavaScript app:

```bash
exiftool -json /workspace/document.pdf > /workspace/metadata.json
rea analyze-javascript-application /workspace/extracted-app --json > /workspace/rea-analysis.json
```

These are recon and analysis results; they do not automatically establish a
vulnerability or produce a complete assessment of a website or APK.

### cryptDocker

| Tool/workflow | Expected output |
| --- | --- |
| OpenSSL digest commands | A hexadecimal digest and algorithm/file label. |
| OpenSSL certificate inspection | Certificate subject, issuer, validity dates, public-key details, extensions, and signature algorithm. Inspection alone does not validate trust. |
| SymPy, GMP, PyCryptodome, cryptography, Z3 | Values printed by your Python script, such as factors, test-vector comparisons, decrypted bytes with valid inputs, or solver results/models. |
| John / hashcat | Supported hash-loading results, progress/status, and recovered candidates if a supplied candidate matches. Unsupported formats/backends or no matches are valid outcomes. |

Example: save a file digest and print a small factorization:

```bash
openssl dgst -sha256 /workspace/sample > /workspace/sample.sha256.txt
python3 -c 'import sympy; print(sympy.factorint(65535))'
# Expected factorization: {3: 1, 5: 1, 17: 1, 257: 1}
```

No automatic cryptographic audit or key recovery occurs when the shell starts.
GPU-dependent jobs may fail if no compatible backend is available.

### mobilePTDocker

| Tool/workflow | Expected output |
| --- | --- |
| `apktool d` | A decoded directory with `AndroidManifest.xml`, resources, and usually Smali code for included DEX files. This is not the original Java/Kotlin source. |
| Androguard | APK/DEX metadata and analysis information for the requested operation, such as package, permission, or code relationships. |
| `unzip`, `plistutil` | Extracted IPA contents and a readable plist representation; executable code may remain encrypted. |
| `adb devices -l`, `idevice_id -l` | Device identifiers and connection state, or an empty list when no device is reachable. |
| ADB logs, `idevicesyslog`, Frida | Device/application logs, process listings, or messages emitted by your instrumentation script when device access and instrumentation prerequisites are met. |

Example: decode an APK and extract an IPA into persistent directories:

```bash
apktool d /workspace/app.apk -o /workspace/decoded-apk
unzip /workspace/app.ipa -d /workspace/extracted-ipa
```

Offline extraction works without a connected phone. Runtime findings require a
reachable, authorized device; this container does not start an iOS Simulator or
an Android emulator.

### reDocker

| Tool/workflow | Expected output |
| --- | --- |
| `file`, `readelf`, `nm`, `strings` | Binary format/architecture, ELF headers and sections, available symbols, and printable strings. Stripped binaries contain fewer symbols. |
| `objdump -d`, Capstone | Disassembled instructions for supported code/architectures. These are assembly listings, not recovered source code. |
| GDB, `strace`, `ltrace` | Debugger state, registers/backtraces, system calls, or library calls when the target executes and tracing is supported. |
| `checksec`, YARA | Reported binary hardening properties or matching rule names; no match is also a valid result. |
| LIEF, pyelftools, pwntools | Parsed structures, transformed artifacts, or analysis results explicitly produced by your script. |

Example: save ELF metadata and disassembly without executing the sample:

```bash
readelf -h /workspace/sample > /workspace/elf-header.txt
objdump -d /workspace/sample > /workspace/disassembly.txt
```

Debug output depends on architecture, symbols, and ptrace support. The image
does not automatically generate decompiled C or a finished reverse-engineering
report.

### webPTDocker

| Tool/workflow | Expected output |
| --- | --- |
| `curl` | Response headers/body, HTTP status details when requested, or connection/TLS errors. |
| ffuf / gobuster | Matching URLs/paths or other requested discovery results, with status/size details depending on mode and filters. Empty results are possible. |
| sqlmap | Test progress, potential/confirmed SQL injection details when detected, and session/output files. A run can conclude that tested parameters are not injectable. |
| mitmproxy / `mitmdump` | HTTP(S) flows that actually pass through the configured proxy; saved flow files when explicitly requested. HTTPS inspection requires client CA trust. |
| `nmap`, OpenSSL | Port/service observations and TLS/certificate information for the requested target. |

Example: save discovery results as JSON and capture proxied flows:

```bash
ffuf -u https://example.com/FUZZ -w /workspace/wordlist.txt -of json -o /workspace/ffuf-results.json
mitmdump --listen-host 0.0.0.0 --listen-port 8080 -w /workspace/flows.mitm
```

Supply your own authorized target and wordlist. The proxy example waits for
traffic and runs until stopped; publish its port and configure the test client
as described in [webPTDocker](webPTDocker/README.md). For persistent sqlmap
results, pass `--output-dir=/workspace/sqlmap-results`. Discovery hits and scanner
messages need review before being treated as verified vulnerabilities.

### Outputs over MCP

All five command bridges return `list_tools` as executable names mapped to
installation booleans. A successful `run_tool` call returns the following fields
inside the MCP tool result (illustrative response for `python3 -c "print('hello')"`):

```json
{
  "exit_code": 0,
  "timed_out": false,
  "stdout": "hello\n",
  "stdout_truncated": false,
  "stderr": "",
  "stderr_truncated": false
}
```

A successful MCP request can still report a nonzero command exit code. Check
`exit_code`, `timed_out`, `stderr`, and truncation flags before interpreting the
output. Each captured stream is limited to 64 KiB; write larger reports to
`/workspace`. Invalid bridge requests return MCP tool errors. OSINTDocker's
separate native REA server returns its own structured analysis/evidence results
rather than this command-runner shape.

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
