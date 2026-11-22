# cryptDocker: command-line usage

Cryptographic implementation analysis. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.
For agent clients, see [MCPUSAGE.md](MCPUSAGE.md); for image limitations, see [README.md](README.md).

## 1. Build on the host

Commands in this section run in a Bash/Zsh terminal on your **host**, from the
repository root. Docker must be installed and its daemon running. Replace input
filenames, device IDs, and example domains with your own artifacts and authorized
lab targets. Network examples perform real requests when run.

```bash
docker info
mkdir -p cryptDocker/workspace
docker build -f cryptDocker/Dockerfile -t cryptdocker:latest .
# Put input files in cryptDocker/workspace before opening the shell.
```

The build context is the repository root (`.`), because `shared/` is required.
Builds download dependencies. Image tags are lowercase.

## 2. Spawn a shell or execute one command

On the host, from the repository root:

```bash
# Interactive Bash shell; the mounted folder becomes /workspace.
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/cryptDocker/workspace,dst=/workspace" \
  cryptdocker:latest

# Alternative: /bin/sh instead of Bash.
docker run --rm -it --entrypoint=/bin/sh \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/cryptDocker/workspace,dst=/workspace" \
  cryptdocker:latest

# One command, without a TTY or a persistent shell.
docker run --rm --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/cryptDocker/workspace,dst=/workspace" \
  cryptdocker:latest python3 -c 'print("container ready")'

# Compose alternative; uses the same workspace directory.
docker compose -f cryptDocker/compose.yaml run --build --rm tools
```

Inside the shell, `whoami` prints `0xdhanesh`, `pwd` prints `/workspace`, and
`ls -la /workspace` shows the mounted inputs. `exit` closes and removes the
container. Files under `/workspace` remain in `cryptDocker/workspace` on the host;
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
| `openssl` | `openssl dgst -sha256 /workspace/sample` | SHA-256 file digest with an algorithm/file label. |
| `gpg` | `gpg --show-keys --with-fingerprint /workspace/public-key.asc` | Public-key identities and fingerprints; no key import requested. |
| `hashcat` | `hashcat -m 0 -a 0 /workspace/hashes.txt /workspace/wordlist.txt --session lab --potfile-path /workspace/hashcat.pot` | Progress and recovered candidates for raw MD5 test hashes, if a usable backend exists. |
| `john` | `john --wordlist=/workspace/wordlist.txt /workspace/john-hashes.txt` | Supported hashes loaded, candidate progress, and matches if found. |
| `python3` | `python3 -c 'import sympy; print(sympy.factorint(65535))'` | Factorization {3: 1, 5: 1, 17: 1, 257: 1}. |

### Certificate and digest reports

Inside the container:

```bash
openssl x509 -in /workspace/certificate.pem -text -noout > /workspace/certificate.txt
openssl dgst -sha256 /workspace/sample > /workspace/sample.sha256.txt
gpg --show-keys --with-fingerprint /workspace/public-key.asc
```

Certificate inspection prints properties; it does not by itself establish a
trusted chain. GPG may create its normal configuration directory in the
container's home. Mount that directory separately if you need its state retained.

### Python math, test vectors, and constraints

```bash
python3 - <<'PYCODE'
import gmpy2
import sympy
from Crypto.Hash import SHA256
from cryptography.hazmat.primitives import hashes
from z3 import Int, Solver
print('gcd:', gmpy2.gcd(48, 18))
print('factors:', sympy.factorint(65535))
expected = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
print('PyCryptodome vector:', SHA256.new(b'abc').hexdigest() == expected)
hash_state = hashes.Hash(hashes.SHA256())
hash_state.update(b'abc')
print('cryptography vector:', hash_state.finalize().hex() == expected)
x = Int('x')
solver = Solver()
solver.add(x * 3 == 21)
print('solver:', solver.check(), solver.model())
PYCODE
```

Expected values include gcd `6`, the factors above, two `True` test-vector
results, and a satisfiable Z3 model with `x = 7`.

### Password-hash lab inputs

Use only hashes and candidate lists you are authorized to test. Hashcat mode
`0` in the table is specifically **raw MD5**, not a format auto-detection step.
Choose the correct mode for other inputs. Distribution John supports fewer
formats than Jumbo. To display recovered results in the same container after a run:

```bash
hashcat -m 0 /workspace/hashes.txt --show --potfile-path /workspace/hashcat.pot
john --show /workspace/john-hashes.txt
```

This distribution's John does not support Jumbo's `--pot` flag. It stores state
in `/home/0xdhanesh/.john`, which disappears with an unmounted ephemeral
container. To retain it, first create `cryptDocker/workspace/john-state` on the
host, then add this mount before the image in the shell/MCP Docker arguments:

```bash
--mount "type=bind,src=$PWD/cryptDocker/workspace/john-state,dst=/home/0xdhanesh/.john"
```

This is an extra Docker argument, not a standalone shell command. In JSON/TOML,
replace `$PWD` with an absolute path. The host state folder must be writable by
UID 10001 (or the runtime user override).

The container does not bundle a GPU runtime, wordlists, SageMath, or a guarantee
of an OpenCL backend. No matches and unsupported-device errors are valid
outcomes. A successful test vector does not prove an implementation secure.

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
ls -la cryptDocker/workspace/results
./scripts/verify.sh cryptDocker
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
