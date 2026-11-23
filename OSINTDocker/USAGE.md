# OSINTDocker: command-line usage

OSINT and artifact/website reconnaissance. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.
For agent clients, see [MCPUSAGE.md](MCPUSAGE.md); for image limitations, see [README.md](README.md).

## 1. Build on the host

Commands in this section run in a Bash/Zsh terminal on your **host**, from the
repository root. Docker must be installed and its daemon running. Replace input
filenames, device IDs, and example domains with your own artifacts and authorized
lab targets. Network examples perform real requests when run.

```bash
docker info
mkdir -p OSINTDocker/workspace
docker build -f OSINTDocker/Dockerfile -t osintdocker:latest .
# Put input files in OSINTDocker/workspace before opening the shell.
```

The build context is the repository root (`.`), because `shared/` is required.
Builds download dependencies. Image tags are lowercase.

## 2. Spawn a shell or execute one command

On the host, from the repository root:

```bash
# Interactive Bash shell; the mounted folder becomes /workspace.
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/OSINTDocker/workspace,dst=/workspace" \
  osintdocker:latest

# Alternative: /bin/sh instead of Bash.
docker run --rm -it --entrypoint=/bin/sh \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/OSINTDocker/workspace,dst=/workspace" \
  osintdocker:latest

# One command, without a TTY or a persistent shell.
docker run --rm --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/OSINTDocker/workspace,dst=/workspace" \
  osintdocker:latest python3 -c 'print("container ready")'

# Compose alternative; uses the same workspace directory.
docker compose -f OSINTDocker/compose.yaml run --build --rm tools
```

Inside the shell, `whoami` prints `0xdhanesh`, `pwd` prints `/workspace`, and
`ls -la /workspace` shows the mounted inputs. `exit` closes and removes the
container. Files under `/workspace` remain in `OSINTDocker/workspace` on the host;
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

All examples below run **inside the container**, not in the host terminal.
Each command exposed in [tools.json](tools.json) has a starter operation here.
They are independent examples; run the ones relevant to your input. For full
subcommand/flag coverage, consult that tool's help (usually `--help`; `john`
prints usage when invoked without arguments). Inputs such as `sample`,
`wordlist.txt`, `rules.yar`, or `hooks.js` must be supplied by you.

| Executable | Example command | Expected output |
| --- | --- | --- |
| `rea` | `rea analyze-javascript-application /workspace/extracted-app --json > /workspace/rea-analysis.json` | Static application graph/evidence JSON; no native provider needed for this workflow. |
| `androguard` | `androguard apkid /workspace/app.apk` | APK package/version JSON. |
| `apktool` | `apktool d /workspace/app.apk -o /workspace/decoded-apk` | Decoded Android manifest/resources and usually Smali. |
| `binwalk` | `binwalk /workspace/firmware.bin` | Candidate embedded signatures and offsets; not automatic validation/extraction. |
| `curl` | `curl -I https://example.com` | HTTP response headers, or a network/TLS error. |
| `wget` | `wget -O /workspace/page.html https://example.com` | Downloaded HTML file. |
| `dig` | `dig example.com MX` | Mail-exchange DNS answers/status. |
| `host` | `host example.com` | Resolved records or lookup failure. |
| `nslookup` | `nslookup example.com` | Resolver and answer details. |
| `whois` | `whois example.com` | Available registration data, potentially redacted or rate limited. |
| `exiftool` | `exiftool -json /workspace/document.pdf > /workspace/metadata.json` | Metadata report, potentially with missing fields. |
| `file` | `file /workspace/artifact` | File-format/architecture identification hints. |
| `strings` | `strings -a /workspace/artifact > /workspace/strings.txt` | Printable strings, without proof of their use. |
| `readelf` | `readelf -h /workspace/libnative.so` | ELF header for a supplied native library. |
| `nmap` | `nmap -sT -sV -p 80,443 -oA /workspace/recon example.com` | Active TCP/service observations in text, XML, and grepable reports. |
| `openssl` | `openssl s_client -connect example.com:443 -servername example.com </dev/null` | Observed TLS negotiation/certificate details. |
| `rg` | `rg -n -i "https?://" /workspace/decoded-apk > /workspace/url-candidates.txt` | Literal URL candidates from decoded files, not confirmed live endpoints. |
| `jq` | `jq . /workspace/metadata.json` | Formatted JSON or a parse error. |
| `python3` | `python3 -c 'import dns.resolver; print([str(r) for r in dns.resolver.resolve("example.com", "A")])'` | DNS answers through dnspython. |
| `sherlock` | `sherlock USERNAME --timeout 10` | Sites where the username exists. |
| `maigret` | `maigret USERNAME` | Profile matches and optional report files. |
| `theHarvester` | `theHarvester -d example.com -b duckduckgo` | Emails, hosts and subdomains from public sources. |
| `subfinder` | `subfinder -d example.com -silent` | Passive subdomain list. |
| `dnsx` | `dnsx -l /workspace/subs.txt -resp` | Resolved records for each host. |
| `httpx-pd` | `httpx-pd -l /workspace/subs.txt -sc -title` | Live web hosts with status code and title. |

### Combine artifact metadata and local search

Inside the container:

```bash
file /workspace/artifact
exiftool -json /workspace/artifact > /workspace/metadata.json
strings -a /workspace/artifact > /workspace/strings.txt
rg -n -i 'https?://' /workspace/strings.txt > /workspace/url-candidates.txt
jq . /workspace/metadata.json
```

`rg` exits `1` for no matches; that is not a read error. Literal strings can
include examples, dead code, and third-party URLs; do not automatically probe them.

### REA workflows

```bash
rea --version
rea analyze-javascript-application /workspace/extracted-app --json > /workspace/rea-analysis.json
rea providers --json
rea --help
# Starts a stdio MCP server and waits for a client; not an interactive REPL:
rea mcp
```

For APKs, apktool/Androguard and REA's Android code analysis both work offline:
the jadx-headless-mcp JAR REA needs is bundled and preconfigured
(`rea doctor --provider jadx` reports it healthy). No browser is bundled, so REA
browser workflows are unavailable. Native decompilation with
Ghidra is bundled in mobilePTDocker and reDocker instead. IDA, Hopper, JEB and
Kuna are proprietary and not bundled. Inspect a subcommand with
`rea COMMAND --help` before use. A URL is not an extracted JavaScript tree.

DNS/WHOIS queries contact resolvers or registration services. HTTP, TLS probes,
and nmap contact the target directly. Limit active recon to an authorized scope.

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
ls -la OSINTDocker/workspace/results
./scripts/verify.sh OSINTDocker
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
