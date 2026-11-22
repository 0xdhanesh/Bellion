# mobilePTDocker

Android and iOS application pentesting. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.

## Included tools

Executables: `rea`, `jadx`, `analyzeHeadless` (Ghidra), `adb`, `apktool`, `apksigner`, `zipalign`, `androguard`, `frida`, `frida-ps`, `frida-trace`, `idevice_id`, `ideviceinfo`, `idevicepair`, `idevicesyslog`, `ideviceinstaller`, `plistutil`, `readelf`, `strings`, `unzip`, `java`, `python3`.

Python libraries/packages: `androguard>=4.1,<5`, `frida==17.23.2`, `frida-tools>=14,<15`.

Everything a tool needs ships in the image; see [Bundled engines](#bundled-engines). Nothing is read from the host except the mounted workspace.
The MCP bridge uses the [official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).

## Build and spawn

Run from the repository root with Docker Desktop or Docker Engine running:

```bash
mkdir -p mobilePTDocker/workspace
docker build -f mobilePTDocker/Dockerfile -t mobileptdocker:latest .
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=2147483648:2147483648 \
  --mount "type=bind,src=$PWD/mobilePTDocker/workspace,dst=/workspace" \
  mobileptdocker:latest
# Or build and open the shell with Compose:
docker compose -f mobilePTDocker/compose.yaml run --build --rm tools
```

Inside the shell (supply your own files and authorized targets):

```bash
apktool d /workspace/app.apk -o /workspace/decoded
androguard --help
unzip /workspace/app.ipa -d /workspace/ipa
plistutil -i /workspace/ipa/Payload/App.app/Info.plist -o /workspace/Info.xml
jadx -d /workspace/jadx-out /workspace/app.apk
rea doctor --provider jadx --provider ghidra   # bundled engines report healthy
apksigner sign --ks /workspace/lab.keystore /workspace/rebuilt.apk
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

Linux cannot run Xcode, iOS Simulator, codesign with Apple tooling, or native iOS apps. IPA inspection works offline; encrypted App Store binaries need a legitimately decrypted copy for code inspection. No Android emulator or SDK image is bundled. Frida needs a reachable device with suitable permissions; the matching frida-server and Gadget binaries are bundled (see below). USB passthrough is host dependent; Docker Desktop does not expose devices like native Linux.

Treat MCP access as code execution: Python, debuggers, and tool scripting options
can access all container files and network endpoints. The command manifest is a
convenience list, not a security sandbox. Use a trusted local client and mount only
needed artifacts. Containers have outbound networking by default. Add
`--network=none` for offline analysis (and to the MCP launch arguments). No host
Docker socket or privileged mode is required. The examples drop capabilities;
TCP connect scanning works without raw sockets. Output is buffered to temporary
files, with a 2 GiB file-size limit in the supplied launch configurations: Ghidra
projects and JADX caches for real APKs exceed the 16 MiB limit the other images use.

Ubuntu packages and Python dependencies resolve within their declared ranges at
build time; these are maintained starter environments, not bit-for-bit locked
images. Keep build logs or freeze package versions when reproducibility is needed.

## Bundled engines

| Engine | Version | Location | Selected by |
| --- | --- | --- | --- |
| REA (`rea-agents`) with Node.js | 6.10.1 / 24.22.1 | `/usr/local/lib/node_modules/rea-agents` | `rea` on `PATH` |
| jadx-headless-mcp (REA Android provider) | 0.7.1, SHA-256 pinned | `/opt/rea-engines/jadx/` | `REA_JADX_MCP_JAR` |
| Ghidra (REA native decompiler for APK `.so` files) | 12.2, SHA-256 pinned | `/opt/ghidra` | `GHIDRA_INSTALL_DIR` |
| OpenJDK (Ghidra 12.2 requires 25) | 25 | `/usr/lib/jvm/java-25-openjdk-*` | `JAVA_HOME` |
| JADX CLI | 1.5.6, SHA-256 pinned | `/opt/jadx` | `jadx` on `PATH` |
| frida-server and Gadget for Android arm, arm64, x86, x86_64 | 17.23.2, SHA-256 pinned | `/opt/frida/android/` | `FRIDA_SERVER_DIR` |

The variables are set with `ENV` in the Dockerfile, so the shell, the command
bridge and `rea mcp` all see the same engines without any host configuration.
Download pins live in [artifacts.json](artifacts.json) and
[shared/rea](../shared/rea); [shared/install_artifacts.py](../shared/install_artifacts.py)
refuses any file whose SHA-256 differs. Ghidra's release has Linux decompiler
natives for x86_64 only, so arm64 builds compile them in a builder stage.
The Frida Python bindings, REA's Frida bindings and the bundled server all use
17.23.2, so versions match on both sides.

Push the server that matches the device ABI (`adb shell getprop ro.product.cpu.abi`):

```bash
adb push "$FRIDA_SERVER_DIR/frida-server-17.23.2-android-arm64" /data/local/tmp/frida-server
adb shell 'chmod 755 /data/local/tmp/frida-server && su -c /data/local/tmp/frida-server -D'
```

Proprietary engines REA can also drive (JEB, IDA Pro, Hopper, Kuna) are not
redistributable and are not bundled. REA works without them.

## Device connections

For Android, connect a device over a trusted lab TCP ADB transport:

```bash
adb connect DEVICE_IP:5555
adb devices -l
frida-ps -H DEVICE_IP:27042
```

Enable the transport on the device first. Android wireless debugging may require
`adb pair DEVICE_IP:PAIRING_PORT` followed by its separate connection port.
Keep ADB/Frida on the lab network. For host-attached Android devices, run the ADB
server on the host with an explicit reachable bind address, then start this image
with `-e ADB_SERVER_SOCKET=tcp:host.docker.internal:5037`. Native Linux needs
`--add-host host.docker.internal:host-gateway`; firewall the server to the lab.

For iOS USB on native Linux, add
`--mount type=bind,src=/var/run/usbmuxd,dst=/var/run/usbmuxd` after starting the
host usbmuxd service. Pairing and trust must be established; socket permissions
must permit UID 10001. `idevice_id -l` checks connectivity. This exposes the host's
usbmuxd device access. On macOS, use host-side libimobiledevice/Frida for USB
sessions; offline APK/IPA work remains available in this container.

## Usage guides

- [USAGE.md](USAGE.md): build, shell startup, command examples, outputs, and troubleshooting.
- [MCPUSAGE.md](MCPUSAGE.md): Claude, Codex, Grok CLI, and Antigravity setup with operation prompts.
