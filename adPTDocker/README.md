# adPTDocker

Windows and Active Directory assessment, with a non-root shell and local stdio MCP bridge.
Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.

## Included tools

`GetADUsers.py`, `GetUserSPNs.py`, `findDelegation.py`, `smbclient.py`, `rpcdump.py`, `lookupsid.py`, `mssqlclient.py`, `kinit`, `klist`, `kvno`, `ldapsearch`, `smbclient`, `rpcclient`, `dig`, `host`, `nslookup`, `openssl`, `curl`, `jq`, `secretsdump.py`, `ntlmrelayx.py`, `GetNPUsers.py`, `ticketer.py`, `certipy`, `bloodhound-python`, `kerbrute`, `evil-winrm`, `python3`.

## Build and spawn

From the repository root with Docker running:

```bash
mkdir -p adPTDocker/workspace
docker build -f adPTDocker/Dockerfile -t adptdocker:latest .
docker compose -f adPTDocker/compose.yaml run --rm tools
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

This is a Linux client toolkit, not a Windows/AD lab. Domain DNS, VPN reachability, clock synchronization and a valid authorized credential or Kerberos ticket are external prerequisites. MCP has no interactive password input: add -e KRB5_CONFIG=/workspace/krb5.conf and -e KRB5CCNAME=FILE:/workspace/0xdhanesh.ccache before the image in its Docker args for mounted lab configuration/cache. Interactive SMB/SQL sessions belong in the shell. No NetExec or BloodHound deployment is included.

Use `./scripts/verify.sh adPTDocker` to build and run the offline MCP/tool checks.

`kerbrute` is built from the pinned `v1.0.3` source tag (upstream ships no arm64 binary) and `evil-winrm` is installed as the pinned `4.1` Ruby gem.
