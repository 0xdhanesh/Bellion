# networkPTDocker

Network enumeration and packet analysis, with a non-root shell and local stdio MCP bridge.
Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.

## Included tools

`nmap`, `tcpdump`, `tshark`, `capinfos`, `socat`, `nc`, `dig`, `host`, `nslookup`, `ldapsearch`, `smbclient`, `ip`, `ss`, `ping`, `traceroute`, `openssl`, `curl`, `wget`, `whois`, `jq`, `python3`.

## Build and spawn

From the repository root with Docker running:

```bash
mkdir -p networkPTDocker/workspace
docker build -f networkPTDocker/Dockerfile -t networkptdocker:latest .
docker compose -f networkPTDocker/compose.yaml run --rm tools
```

The account is `0xdhanesh` (UID 10001); mounted artifacts and reports live under
`/workspace`. Images use Ubuntu 24.04 and build for the host architecture.
Ubuntu/Python dependencies resolve at build time unless explicitly pinned.

## MCP connection

[mcp.json](mcp.json) launches an ephemeral Docker stdio server with `-i`, without
a TTY. Replace its absolute workspace placeholder. The bridge exposes
`list_tools` (installation inventory) and `run_tool` (argument-array execution,
working directory under `/workspace`, timeout 1–300 seconds). Each captured
stream is capped at 64 KiB. Persist larger reports in the mounted workspace.
The supplied launch configurations limit individual output files to 16 MiB;
raise that limit deliberately for larger captures/reports. MCP access permits
code execution inside the container; use a trusted local client and mount only
needed files. There is no HTTP MCP endpoint or host Docker-socket mount.

## Guides and limitations

- [USAGE.md](USAGE.md): all exposed commands, expected outputs, runtime requirements, and troubleshooting.
- [MCPUSAGE.md](MCPUSAGE.md): Claude, Codex, Grok CLI, and Antigravity setup and operation prompts.

Default networking is container-scoped. TCP-connect scans and offline captures work without raw-socket capabilities; live capture, raw scanning, host VPN routes, and ICMP access need host-specific configuration. No VPN or physical-interface capture setup is bundled.

Use `./scripts/verify.sh networkPTDocker` to build and run the offline MCP/tool checks.
