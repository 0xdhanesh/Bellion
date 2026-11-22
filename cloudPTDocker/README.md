# cloudPTDocker

Cloud and container configuration assessment, with a non-root shell and local stdio MCP bridge.
Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.

## Included tools

`aws`, `az`, `gcloud`, `trivy`, `openssl`, `curl`, `jq`, `python3`.

## Build and spawn

From the repository root with Docker running:

```bash
mkdir -p cloudPTDocker/workspace
docker build -f cloudPTDocker/Dockerfile -t cloudptdocker:latest .
docker compose -f cloudPTDocker/compose.yaml run --rm tools
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

Cloud identities, account permissions, and provider connectivity are external prerequisites. No credentials are embedded. AWS CLI v1 is included (not v2 SSO login). Azure and Google Cloud interactive logins belong in a shell with separately mounted persistent configuration directories, which must also be added to the MCP Docker args. Vulnerability databases are not bundled; Trivy configuration scans can use embedded checks offline, while vulnerability scans need an available database. No Kubernetes client, VPN, or automatic cloud remediation is included.

Use `./scripts/verify.sh cloudPTDocker` to build and run the offline MCP/tool checks.

## Pinned tooling

AWS CLI v1.46.3, Azure CLI 2.93.0, Google Cloud CLI 594.0.0, and Trivy v0.76.2
are recorded in [versions.json](versions.json). AWS/Azure run in isolated Python
environments. Release archives use SHA-256 verification; the Google SDK archive
pins are in [gcloud-release.json](gcloud-release.json). Both amd64 and arm64 have
explicit archive mappings. Database downloads, credential setup, and cloud API
access are separate runtime operations; nothing logs in during the build.
