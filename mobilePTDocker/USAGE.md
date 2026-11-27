# mobilePTDocker: command-line usage

Android and iOS application pentesting. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.
For agent clients, see [MCPUSAGE.md](MCPUSAGE.md); for image limitations, see [README.md](README.md).

## 1. Build on the host

Commands in this section run in a Bash/Zsh terminal on your **host**, from the
repository root. Docker must be installed and its daemon running. Replace input
filenames, device IDs, and example domains with your own artifacts and authorized
lab targets. Network examples perform real requests when run.

```bash
docker info
mkdir -p mobilePTDocker/workspace
docker build -f mobilePTDocker/Dockerfile -t mobileptdocker:latest .
# Put input files in mobilePTDocker/workspace before opening the shell.
```

The build context is the repository root (`.`), because `shared/` is required.
Builds download dependencies. Image tags are lowercase.

## 2. Spawn a shell or execute one command

On the host, from the repository root:

```bash
# Interactive Bash shell; the mounted folder becomes /workspace.
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=2147483648:2147483648 \
  --mount "type=bind,src=$PWD/mobilePTDocker/workspace,dst=/workspace" \
  mobileptdocker:latest

# Alternative: /bin/sh instead of Bash.
docker run --rm -it --entrypoint=/bin/sh \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=2147483648:2147483648 \
  --mount "type=bind,src=$PWD/mobilePTDocker/workspace,dst=/workspace" \
  mobileptdocker:latest

# One command, without a TTY or a persistent shell.
docker run --rm --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=2147483648:2147483648 \
  --mount "type=bind,src=$PWD/mobilePTDocker/workspace,dst=/workspace" \
  mobileptdocker:latest python3 -c 'print("container ready")'

# Compose alternative; uses the same workspace directory.
docker compose -f mobilePTDocker/compose.yaml run --build --rm tools
```

Inside the shell, `whoami` prints `0xdhanesh`, `pwd` prints `/workspace`, and
`ls -la /workspace` shows the mounted inputs. `exit` closes and removes the
container. Files under `/workspace` remain in `mobilePTDocker/workspace` on the host;
files elsewhere disappear unless separately mounted. To work from any host
folder, use the helpers in the [shell helpers guide](../docs/SHELL_HELPERS.md).

The user is UID 10001, without sudo. On native Linux, either grant this UID
workspace access or add `--user "$(id -u):$(id -g)" -e HOME=/tmp` before the image
in `docker run`. For offline artifact work, add `--network=none` there as well.
Compose overrides must supply equivalent settings. For a foreign architecture,
use matching `--platform linux/amd64` build/run options; emulated execution and
ptrace are not guaranteed. The supplied launches cap individual files at 2 GiB (Ghidra and JADX workspaces outgrow 16 MiB);
raise the `--ulimit fsize=SOFT:HARD` values deliberately for larger reports.

## 3. Execute the installed commands

All examples below run **inside the container**, not in the host terminal.
Each command exposed in [tools.json](tools.json) has a starter operation here.
They are independent examples; run the ones relevant to your input. For full
subcommand/flag coverage, consult that tool's help (usually `--help`; `john`
prints usage when invoked without arguments). Inputs such as `sample`,
`wordlist.txt`, `rules.yar`, or `hooks.js` must be supplied by you.

| Executable | Example command | Expected output |
| --- | --- | --- |
| `adb` | `adb devices -l` | Device serial, state, and transport details; may be empty. |
| `apktool` | `apktool d /workspace/app.apk -o /workspace/decoded-apk` | Decoded manifest/resources and usually Smali code. |
| `androguard` | `androguard apkid /workspace/app.apk` | JSON package name/version information. |
| `frida` | `frida -H DEVICE_IP:27042 -p PID -l /workspace/hooks.js` | Interactive instrumentation and messages from your supplied script. |
| `frida-ps` | `frida-ps -H DEVICE_IP:27042` | Processes visible to the reachable Frida server. |
| `frida-trace` | `frida-trace -H DEVICE_IP:27042 -p PID -i open` | Calls to matching native functions; generated handlers may be written in the current directory. |
| `idevice_id` | `idevice_id -l` | Connected iOS device identifiers, or an empty list. |
| `ideviceinfo` | `ideviceinfo -u UDID` | Device properties available through the trusted pairing. |
| `idevicepair` | `idevicepair -u UDID validate` | Pairing validation success/failure. |
| `idevicesyslog` | `idevicesyslog -u UDID` | Streaming device logs; Ctrl-C stops it. |
| `ideviceinstaller` | `ideviceinstaller -u UDID -l` | Installed user applications visible to the device service. |
| `plistutil` | `plistutil -i /workspace/ipa/Payload/App.app/Info.plist -o /workspace/Info.xml` | Converted plist; replace App.app with the actual directory. |
| `readelf` | `readelf -h /workspace/libnative.so` | ELF header for an extracted Android native library. |
| `strings` | `strings -a /workspace/libnative.so > /workspace/native-strings.txt` | Printable strings; occurrences are candidates, not executed behavior. |
| `unzip` | `unzip /workspace/app.ipa -d /workspace/ipa` | Extracted IPA contents; executables may remain encrypted. |
| `python3` | `python3 -c 'from androguard.core.apk import APK; a=APK("/workspace/app.apk"); print(a.get_package()); print(a.get_permissions())'` | Package ID and declared Android permissions. |
| `objection` | `objection -g com.example.app explore` | Frida-powered runtime exploration REPL (needs a reachable frida-server). |
| `ipa-rasp` | `ipa-rasp /workspace/app.ipa` | Static RASP / anti-debug / jailbreak / instrumentation detection report for an IPA. |

### iOS IPA static RASP analysis

Whenever you analyze an IPA, run the bundled static RASP scanner. It extracts the IPA, locates the main binary, and reports common anti-debug, jailbreak detection, and instrumentation (Frida) indicators using only tools already in the image (`unzip`, `strings`, `nm`, `plistutil`).

```bash
# Place the IPA in the workspace, then inside the container:
ipa-rasp /workspace/MyApp.ipa

# JSON output for further processing or MCP clients:
ipa-rasp /workspace/MyApp.ipa --json
```

The report is printed directly to the terminal. High-severity findings indicate strong static evidence of RASP controls. This is complementary to dynamic Frida checks (which require a reachable device and frida-server).

### Android connections and finite log collection

Inside the container, after enabling a trusted lab TCP ADB transport:

```bash
adb connect DEVICE_IP:5555
adb devices -l
adb -s DEVICE_SERIAL logcat -d -t 200 > /workspace/logcat.txt
adb -s DEVICE_SERIAL shell pm list packages
androguard axml /workspace/app.apk -o /workspace/AndroidManifest.xml
```

Android wireless debugging can instead require `adb pair DEVICE_IP:PAIRING_PORT`
and `adb connect DEVICE_IP:CONNECTION_PORT`. Device operations require a trusted
connection. To install your test APK deliberately, use
`adb -s DEVICE_SERIAL install /workspace/app.apk`; this changes the device.
For Frida, the matching 17.23.2 server and Gadget for each Android ABI are in
`$FRIDA_SERVER_DIR` (`/opt/frida/android`); push the one for the device ABI with
`adb push "$FRIDA_SERVER_DIR/frida-server-17.23.2-android-arm64" /data/local/tmp/frida-server`.
`PID`, `DEVICE_SERIAL`, and `DEVICE_IP` are placeholders.

To reuse a host ADB server, add
`-e ADB_SERVER_SOCKET=tcp:host.docker.internal:5037` **before the image** in the
host launch command. Configure the host server to accept the lab connection.
Native Linux also needs `--add-host host.docker.internal:host-gateway`.

### iOS connections

On native Linux, run usbmuxd on the host, then add
`--mount type=bind,src=/var/run/usbmuxd,dst=/var/run/usbmuxd` before the image in
the host launch command. The container user must have socket access. Unlock and
trust the device. `idevicepair -u UDID pair` explicitly establishes pairing;
`validate` checks it. USB through Docker Desktop on macOS is not equivalent to
native Linux: use host-side device tools there, or use offline APK/IPA analysis.

### Decompilation and REA

JADX, Ghidra and REA's engines are bundled and preconfigured; no host install or
path setting is needed:

```bash
jadx -d /workspace/jadx-out /workspace/app.apk
rea doctor --provider jadx --provider ghidra
analyzeHeadless /workspace/ghidra-project lib -import /workspace/decoded/lib/arm64-v8a/libnative.so
apksigner verify --print-certs /workspace/app.apk
```

No emulator, Xcode, iOS Simulator, or Apple code-signing environment is bundled.
Encrypted IPA code must be legitimately decrypted before meaningful code review.

## 4. Preserve results and verify the environment

Shell redirection works inside the shell. For example:

```bash
mkdir -p /workspace/results
python3 -c 'print("analysis notes")' > /workspace/results/notes.txt
cat /workspace/results/notes.txt
exit
```

Back on the host, from the repository root:

```bash
ls -la mobilePTDocker/workspace/results
./scripts/verify.sh mobilePTDocker
```

The verification script checks the image build, installed tools, account, and
real stdio MCP interactions using local fixtures. It does not validate your
specific target, physical device, or optional analysis providers.

| Problem | Check |
| --- | --- |
| Cannot connect to Docker | Start Docker Desktop/Engine and run `docker info` on the host. |
| Image missing | Build from the repository root using the exact lowercase tag above. |
| Input file missing | Check the host bind path and use `/workspace/...` inside the container. |
| Permission denied writing reports | Check workspace ownership/UID mapping on native Linux. |
| File size limit exceeded | Adjust the supplied fsize limit for the intended artifact/report size. |
| Network lookup or connection fails | Check offline mode, lab reachability, DNS, and service settings. |
| Tool reports missing engine/device | Follow [README.md](README.md); installing a CLI does not supply an external provider or device. |
