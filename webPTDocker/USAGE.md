# webPTDocker: command-line usage

Web application pentesting. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.
For agent clients, see [MCPUSAGE.md](MCPUSAGE.md); for image limitations, see [README.md](README.md).

## 1. Build on the host

Commands in this section run in a Bash/Zsh terminal on your **host**, from the
repository root. Docker must be installed and its daemon running. Replace input
filenames, device IDs, and example domains with your own artifacts and authorized
lab targets. Network examples perform real requests when run.

```bash
docker info
mkdir -p webPTDocker/workspace
docker build -f webPTDocker/Dockerfile -t webptdocker:latest .
# Put input files in webPTDocker/workspace before opening the shell.
```

The build context is the repository root (`.`), because `shared/` is required.
Builds download dependencies. Image tags are lowercase.

## 2. Spawn a shell or execute one command

On the host, from the repository root:

```bash
# Interactive Bash shell; the mounted folder becomes /workspace.
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/webPTDocker/workspace,dst=/workspace" \
  webptdocker:latest

# Alternative: /bin/sh instead of Bash.
docker run --rm -it --entrypoint=/bin/sh \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/webPTDocker/workspace,dst=/workspace" \
  webptdocker:latest

# One command, without a TTY or a persistent shell.
docker run --rm --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/webPTDocker/workspace,dst=/workspace" \
  webptdocker:latest python3 -c 'print("container ready")'

# Compose alternative; uses the same workspace directory.
docker compose -f webPTDocker/compose.yaml run --build --rm tools
```

Inside the shell, `whoami` prints `0xdhanesh`, `pwd` prints `/workspace`, and
`ls -la /workspace` shows the mounted inputs. `exit` closes and removes the
container. Files under `/workspace` remain in `webPTDocker/workspace` on the host;
files elsewhere disappear unless separately mounted. To work from any host
folder, use the helpers in the [root README](../README.md#shell-helpers-for-this-project).

The user is UID 10001, without sudo. On native Linux, either grant this UID
workspace access or add `--user "$(id -u):$(id -g)" -e HOME=/tmp` before the image
in `docker run`. For offline artifact work, add `--network=none` there as well.
Compose overrides must supply equivalent settings. For a foreign architecture,
use matching `--platform linux/amd64` build/run options; emulated execution and
ptrace are not guaranteed. The supplied launches cap individual files at 16 MiB;
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
| `curl` | `curl -I https://example.com` | Response headers, or a connection/TLS error. |
| `wget` | `wget -O /workspace/page.html https://example.com` | Saved response body in page.html. |
| `dig` | `dig example.com A` | DNS answer/status and resolver details. |
| `ffuf` | `ffuf -u https://example.com/FUZZ -w /workspace/wordlist.txt -of json -o /workspace/ffuf.json` | Matching paths and a JSON report; results depend on filters. |
| `gobuster` | `gobuster dir -u https://example.com -w /workspace/wordlist.txt -o /workspace/gobuster.txt` | Discovered paths/statuses and a text report. |
| `nmap` | `nmap -sT -sV -p 80,443 -oA /workspace/web-ports example.com` | Port/service observations in .nmap, .gnmap, and .xml files. |
| `openssl` | `openssl s_client -connect example.com:443 -servername example.com </dev/null` | TLS negotiation/certificate details; this contacts the server. |
| `sqlmap` | `sqlmap -u "https://example.com/item?id=1" --batch --output-dir=/workspace/sqlmap` | Test progress and persistent sessions/findings, including no injectable parameters. |
| `mitmdump` | `mitmdump --listen-host 0.0.0.0 --listen-port 8080 -w /workspace/flows.mitm` | Saved traffic that passes through the proxy; Ctrl-C stops capture. |
| `mitmproxy` | `mitmproxy --listen-host 0.0.0.0 --listen-port 8080` | Interactive flow viewer; q opens the quit prompt. |
| `python3` | `python3 -c 'import requests; r=requests.get("https://example.com", timeout=15); print(r.status_code)'` | HTTP status from a small requests script. |

### Publish a local interception proxy

Run this **on the host**, from the repository root:

```bash
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 -p 127.0.0.1:8080:8080 \
  --mount "type=bind,src=$PWD/webPTDocker/workspace,dst=/workspace" \
  webptdocker:latest mitmdump --listen-host 0.0.0.0 --listen-port 8080 -w /workspace/flows.mitm
```

Point a host test client's HTTP/HTTPS proxy at `127.0.0.1:8080`. HTTPS inspection
needs the mitmproxy CA trusted by that client. The ephemeral container's default
CA directory disappears on exit; mount `/home/0xdhanesh/.mitmproxy` separately
if you need a stable lab CA. For a phone, use a deliberately configured lab
interface/port and a reachable host address; the loopback mapping above is for
host clients. No traffic appears until the client actually uses the proxy.

### Python parsing

Inside the container:

```bash
python3 - <<'PYCODE'
from pathlib import Path
from bs4 import BeautifulSoup
page = BeautifulSoup(Path('/workspace/page.html').read_text(), 'html.parser')
print([a.get('href') for a in page.find_all('a')])
PYCODE
```

Wordlists, Burp Suite, and a GUI browser are not bundled. Treat discovery hits
and scanner output as evidence to review, rather than proof of a vulnerability.

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
ls -la webPTDocker/workspace/results
./scripts/verify.sh webPTDocker
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
