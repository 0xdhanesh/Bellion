# adPTDocker: command-line usage

Windows and Active Directory assessment. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.
For agent clients, see [MCPUSAGE.md](MCPUSAGE.md); for image limitations, see [README.md](README.md).

## 1. Build on the host

Commands in this section run in a Bash/Zsh terminal on your **host**, from the
repository root. Docker must be installed and its daemon running. Replace input
filenames, device IDs, and example domains with your own artifacts and authorized
lab targets. Network examples perform real requests when run.

```bash
docker info
mkdir -p adPTDocker/workspace
docker build -f adPTDocker/Dockerfile -t adptdocker:latest .
# Put input files in adPTDocker/workspace before opening the shell.
```

The build context is the repository root (`.`), because `shared/` is required.
Builds download dependencies. Image tags are lowercase.

## 2. Spawn a shell or execute one command

On the host, from the repository root:

```bash
# Interactive Bash shell; the mounted folder becomes /workspace.
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/adPTDocker/workspace,dst=/workspace" \
  adptdocker:latest

# Alternative: /bin/sh instead of Bash.
docker run --rm -it --entrypoint=/bin/sh \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/adPTDocker/workspace,dst=/workspace" \
  adptdocker:latest

# One command, without a TTY or a persistent shell.
docker run --rm --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/adPTDocker/workspace,dst=/workspace" \
  adptdocker:latest python3 -c 'print("container ready")'

# Compose alternative; uses the same workspace directory.
docker compose -f adPTDocker/compose.yaml run --build --rm tools
```

Inside the shell, `whoami` prints `0xdhanesh`, `pwd` prints `/workspace`, and
`ls -la /workspace` shows the mounted inputs. `exit` closes and removes the
container. Files under `/workspace` remain in `adPTDocker/workspace` on the host;
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
| `GetADUsers.py` | `GetADUsers.py -all -k -no-pass -dc-ip DC_IP LAB.EXAMPLE/0xdhanesh` | Directory user attributes visible to your ticket identity. |
| `GetUserSPNs.py` | `GetUserSPNs.py -k -no-pass -dc-ip DC_IP LAB.EXAMPLE/0xdhanesh` | SPN account information; this example does not request roastable tickets. |
| `findDelegation.py` | `findDelegation.py -k -no-pass -dc-ip DC_IP LAB.EXAMPLE/0xdhanesh` | Delegation configuration visible to the authenticated identity. |
| `smbclient.py` | `smbclient.py -k -no-pass LAB.EXAMPLE/0xdhanesh@SERVER_FQDN` | Interactive SMB client; commands depend on account permissions. |
| `rpcdump.py` | `rpcdump.py -port 135 SERVER_FQDN` | RPC endpoint mapper information if the endpoint permits it. |
| `lookupsid.py` | `lookupsid.py -k -no-pass LAB.EXAMPLE/0xdhanesh@SERVER_FQDN` | SID/name enumeration where the account and target permit it. |
| `mssqlclient.py` | `mssqlclient.py -k -no-pass -windows-auth LAB.EXAMPLE/0xdhanesh@SQL_FQDN` | Interactive SQL session if the account can authenticate; no query is automatically run by this example. |
| `kinit` | `kinit -c /workspace/0xdhanesh.ccache 0xdhanesh@LAB.EXAMPLE` | Prompts for credentials in a shell and obtains a ticket cache. |
| `klist` | `klist -c /workspace/0xdhanesh.ccache` | Ticket principals, validity periods, and expiry times, or a cache error. |
| `kvno` | `kvno cifs/SERVER_FQDN` | Service-ticket acquisition/status using the current ticket cache. |
| `ldapsearch` | `ldapsearch -LLL -x -H ldap://DC_HOST -s base -b "" namingContexts` | RootDSE information if anonymous reads are allowed. |
| `smbclient` | `smbclient --use-kerberos=required -N -L //SERVER_FQDN` | Shares visible with the configured Kerberos identity. |
| `rpcclient` | `rpcclient --use-kerberos=required -N SERVER_FQDN -c srvinfo` | Server information if authenticated RPC access is permitted. |
| `dig` | `dig _ldap._tcp.dc._msdcs.lab.example SRV` | Domain-controller service records from the configured resolver. |
| `host` | `host DC_FQDN` | DC address resolution or a DNS error. |
| `nslookup` | `nslookup DC_FQDN` | Resolver and DC address results. |
| `openssl` | `openssl s_client -connect DC_FQDN:636 -servername DC_FQDN </dev/null` | LDAPS handshake/certificate details. |
| `curl` | `curl -I --max-time 15 https://LAB_HOST` | HTTP headers for a supplied lab service. |
| `jq` | `jq . /workspace/report.json` | Formatted JSON or a parsing error. |
| `python3` | `python3 -c 'import impacket,ldap3; print(ldap3.__version__)'` | Checks the Impacket/LDAP Python environment. |
| `secretsdump.py` | `secretsdump.py -k -no-pass LAB.EXAMPLE/0xdhanesh@DC_FQDN` | Credential-dump output for an account you are authorized to use; usage text with `-h`. |
| `ntlmrelayx.py` | `ntlmrelayx.py -tf /workspace/targets.txt -smb2support` | Relay listener status; needs ports 445/80 (root with `NET_BIND_SERVICE`) for live relaying. |
| `GetNPUsers.py` | `GetNPUsers.py -dc-ip DC_IP -usersfile /workspace/users.txt LAB.EXAMPLE/` | AS-REP-roastable accounts and hashes. |
| `ticketer.py` | `ticketer.py -nthash HASH -domain-sid SID -domain LAB.EXAMPLE USER` | A forged ticket `.ccache` written to the working directory. |
| `certipy` | `certipy find -u 0xdhanesh@lab.example -k -no-pass -dc-ip DC_IP -stdout` | ADCS templates, CAs and vulnerable-configuration findings. |
| `bloodhound-python` | `bloodhound-python -c All -d lab.example -u 0xdhanesh -k -no-pass -ns DC_IP --zip` | BloodHound collection ZIP in the working directory. |
| `kerbrute` | `kerbrute userenum -d lab.example --dc DC_IP /workspace/users.txt` | Valid usernames via Kerberos pre-auth responses. |
| `evil-winrm` | `evil-winrm -i SERVER_FQDN -u 0xdhanesh -r LAB.EXAMPLE` | Interactive WinRM shell (needs port 5985/5986 reachability). |

### Configure DNS, time, and Kerberos

Use a reachable lab DC and a resolver that knows the domain. Docker may need
`--dns DC_IP` before the image for AD DNS discovery. The host clock must be
synchronized with the domain; the container cannot fix host time. Use FQDNs for
Kerberos service names and verify the VPN route from the container.

Place your lab-specific Kerberos configuration at `/workspace/krb5.conf`:

```ini
[libdefaults]
    default_realm = LAB.EXAMPLE
    dns_lookup_kdc = true
    rdns = false
[realms]
    LAB.EXAMPLE = {
        kdc = dc.lab.example
    }
[domain_realm]
    .lab.example = LAB.EXAMPLE
    lab.example = LAB.EXAMPLE
```

Inside an interactive shell:

```bash
export KRB5_CONFIG=/workspace/krb5.conf
export KRB5CCNAME=FILE:/workspace/0xdhanesh.ccache
kinit -c /workspace/0xdhanesh.ccache 0xdhanesh@LAB.EXAMPLE
klist
# Use your own lab domain, DC address and server FQDNs in the command table.
```

Kerberos caches and keytabs are credentials. Do not commit them or print their
contents into an agent conversation. For authorized keytab-based authentication
without a password prompt, use:

```bash
kinit -kt /workspace/0xdhanesh.keytab -c /workspace/0xdhanesh.ccache 0xdhanesh@LAB.EXAMPLE
```

For a targeted authenticated LDAP read with GSSAPI:

```bash
ldapsearch -LLL -Y GSSAPI -H ldap://dc.lab.example -b 'DC=lab,DC=example' -s base distinguishedName
```

This image is a Linux client environment, not a Windows host or an AD lab. No
Windows-only GUI, domain controller, NetExec, BloodHound server/collector, password
corpus, or VPN client is bundled. Authentication failures, denied enumeration,
expired caches, and partial results are normal outcomes to report accurately.
Interactive SMB/SQL clients belong in a shell. The Impacket source project is
[fortra/impacket](https://github.com/fortra/impacket).



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
ls -la adPTDocker/workspace/results
./scripts/verify.sh adPTDocker
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
