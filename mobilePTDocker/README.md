# mobilePTDocker

Android and iOS application pentesting. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.

## Included tools

Executables: `adb`, `apktool`, `androguard`, `frida`, `frida-ps`, `frida-trace`, `idevice_id`, `ideviceinfo`, `idevicepair`, `idevicesyslog`, `ideviceinstaller`, `plistutil`, `readelf`, `strings`, `unzip`, `python3`.

Python libraries/packages: `androguard>=4.1,<5`, `frida-tools>=14,<15`.
The MCP bridge uses the [official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).

## Build and spawn

Run from the repository root with Docker Desktop or Docker Engine running:

```bash
mkdir -p mobilePTDocker/workspace
docker build -f mobilePTDocker/Dockerfile -t mobileptdocker:latest .
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
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

Linux cannot run Xcode, iOS Simulator, codesign with Apple tooling, or native iOS apps. IPA inspection works offline; encrypted App Store binaries need a legitimately decrypted copy for code inspection. No Android emulator or SDK image is bundled. Frida requires a matching frida-server or Gadget and suitable device permissions. USB passthrough is host dependent; Docker Desktop does not expose devices like native Linux.

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
