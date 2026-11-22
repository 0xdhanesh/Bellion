# networkPTDocker: command-line usage

Network enumeration and packet analysis. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.
For agent clients, see [MCPUSAGE.md](MCPUSAGE.md); for image limitations, see [README.md](README.md).

## 1. Build on the host

Commands in this section run in a Bash/Zsh terminal on your **host**, from the
repository root. Docker must be installed and its daemon running. Replace input
filenames, device IDs, and example domains with your own artifacts and authorized
lab targets. Network examples perform real requests when run.

```bash
docker info
mkdir -p networkPTDocker/workspace
docker build -f networkPTDocker/Dockerfile -t networkptdocker:latest .
# Put input files in networkPTDocker/workspace before opening the shell.
```

The build context is the repository root (`.`), because `shared/` is required.
Builds download dependencies. Image tags are lowercase.

## 2. Spawn a shell or execute one command

On the host, from the repository root:

```bash
# Interactive Bash shell; the mounted folder becomes /workspace.
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/networkPTDocker/workspace,dst=/workspace" \
  networkptdocker:latest

# Alternative: /bin/sh instead of Bash.
docker run --rm -it --entrypoint=/bin/sh \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/networkPTDocker/workspace,dst=/workspace" \
  networkptdocker:latest

# One command, without a TTY or a persistent shell.
docker run --rm --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/networkPTDocker/workspace,dst=/workspace" \
  networkptdocker:latest python3 -c 'print("container ready")'

# Compose alternative; uses the same workspace directory.
docker compose -f networkPTDocker/compose.yaml run --build --rm tools
```

Inside the shell, `whoami` prints `0xdhanesh`, `pwd` prints `/workspace`, and
`ls -la /workspace` shows the mounted inputs. `exit` closes and removes the
container. Files under `/workspace` remain in `networkPTDocker/workspace` on the host;
files elsewhere disappear unless separately mounted. To work from any host
folder, use the helpers in the [shell helpers guide](../docs/SHELL_HELPERS.md).

The user is UID 10001, without sudo. On native Linux, either grant this UID
workspace access or add `--user "$(id -u):$(id -g)" -e HOME=/tmp` before the image
in `docker run`. For offline artifact work, add `--network=none` there as well.
Compose overrides must supply equivalent settings. For a foreign architecture,
use matching `--platform linux/amd64` build/run options; emulated execution and
ptrace are not guaranteed. The supplied launches cap individual files at 16 MiB;
raise the `--ulimit fsize=SOFT:HARD` values deliberately for larger reports.

## 3. Execute the installed commands

Run these examples **inside the container** with your own input files and
explicitly authorized targets. Each executable in tools.json is covered below.
Use its help for all options. Report files under `/workspace` persist on the host.

| Executable | Example | Expected output |
| --- | --- | --- |
| `nmap` | `nmap -sT -sV -p 22,80,443 -oA /workspace/ports LAB_HOST` | TCP port states/service guesses and text/XML reports. |
| `tcpdump` | `tcpdump -nn -r /workspace/capture.pcap -c 50` | First 50 packets from an existing capture; no live sniffing. |
| `tshark` | `tshark -r /workspace/capture.pcap -q -z conv,tcp` | TCP conversation summary from an offline capture. |
| `capinfos` | `capinfos /workspace/capture.pcap` | Capture file size, packet count, timestamps and interfaces. |
| `socat` | `socat - TCP:LAB_HOST:80,connect-timeout=5` | Interactive TCP connection; Ctrl-C stops it. |
| `nc` | `nc -vz -w 3 LAB_HOST 443` | TCP connection success/refusal/timeout. |
| `dig` | `dig example.com A` | DNS answers and resolver details. |
| `host` | `host example.com` | Resolved DNS records. |
| `nslookup` | `nslookup example.com` | Resolver and DNS answer details. |
| `ldapsearch` | `ldapsearch -x -H ldap://DC_HOST -s base -b "" namingContexts` | LDAP rootDSE naming contexts if anonymous access is permitted. |
| `smbclient` | `smbclient -L //LAB_HOST -N` | Shares visible without credentials, or an authentication error. |
| `ip` | `ip address show` | Container interface addresses, not necessarily host interfaces. |
| `ss` | `ss -lnt` | Listening TCP sockets visible in the container namespace. |
| `ping` | `ping -c 3 LAB_HOST` | ICMP reachability or a permission/filtering error. |
| `traceroute` | `traceroute -m 8 -w 1 LAB_HOST` | Route-hop replies when the lab network permits them. |
| `openssl` | `openssl s_client -connect LAB_HOST:443 -servername LAB_HOST </dev/null` | TLS negotiation and certificate details. |
| `curl` | `curl -I --max-time 15 https://example.com` | HTTP response headers or connection errors. |
| `wget` | `wget -O /workspace/page.html https://example.com` | Downloaded response body. |
| `whois` | `whois example.com` | Available registration records, with possible redactions. |
| `jq` | `jq . /workspace/report.json` | Formatted JSON or a parsing error. |
| `python3` | `python3 -c 'import socket; print(socket.getaddrinfo("example.com",443))'` | Resolved address candidates. |

### Captures, routing, and portability

The default non-root container drops all capabilities. Offline tcpdump/TShark
analysis and TCP-connect scans work without raw sockets. Live capture and some
ICMP/raw operations need additional OS permissions; they are not enabled by the
provided launch commands. Capture packets with the host's approved tooling,
put the capture in the workspace, then analyze it here. This also avoids
pretending Docker Desktop exposes the host's physical interfaces.

The Docker network namespace has its own routing and interfaces. Connect the
host's VPN first and verify the lab route from the container. On native Linux,
`--network=host` is an optional launch choice when the engagement requires host
network visibility; Docker Desktop behavior differs. No VPN client, packet
injection, Wi-Fi monitor mode, or host capture setup is bundled.

For packet-level CSV output inside the container:

```bash
tshark -r /workspace/capture.pcap -T fields -e frame.number -e ip.src -e ip.dst -e tcp.dstport -E header=y -E separator=, > /workspace/packets.csv
```

Expect empty fields for protocols without IP/TCP. Large captures/reports may
require raising the launch's file-size limit. Streaming network services should
be run from a shell; the MCP bridge is designed for bounded commands.



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
ls -la networkPTDocker/workspace/results
./scripts/verify.sh networkPTDocker
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
