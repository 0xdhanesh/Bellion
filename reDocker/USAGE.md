# reDocker: command-line usage

ELF and native binary reverse engineering. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.
For agent clients, see [MCPUSAGE.md](MCPUSAGE.md); for image limitations, see [README.md](README.md).

## 1. Build on the host

Commands in this section run in a Bash/Zsh terminal on your **host**, from the
repository root. Docker must be installed and its daemon running. Replace input
filenames, device IDs, and example domains with your own artifacts and authorized
lab targets. Network examples perform real requests when run.

```bash
docker info
mkdir -p reDocker/workspace
docker build -f reDocker/Dockerfile -t redocker:latest .
# Put input files in reDocker/workspace before opening the shell.
```

The build context is the repository root (`.`), because `shared/` is required.
Builds download dependencies. Image tags are lowercase.

## 2. Spawn a shell or execute one command

On the host, from the repository root:

```bash
# Interactive Bash shell; the mounted folder becomes /workspace.
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=2147483648:2147483648 \
  --mount "type=bind,src=$PWD/reDocker/workspace,dst=/workspace" \
  redocker:latest

# Alternative: /bin/sh instead of Bash.
docker run --rm -it --entrypoint=/bin/sh \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=2147483648:2147483648 \
  --mount "type=bind,src=$PWD/reDocker/workspace,dst=/workspace" \
  redocker:latest

# One command, without a TTY or a persistent shell.
docker run --rm --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=2147483648:2147483648 \
  --mount "type=bind,src=$PWD/reDocker/workspace,dst=/workspace" \
  redocker:latest python3 -c 'print("container ready")'

# Compose alternative; uses the same workspace directory.
docker compose -f reDocker/compose.yaml run --build --rm tools
```

Inside the shell, `whoami` prints `0xdhanesh`, `pwd` prints `/workspace`, and
`ls -la /workspace` shows the mounted inputs. `exit` closes and removes the
container. Files under `/workspace` remain in `reDocker/workspace` on the host;
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
| `file` | `file /workspace/sample` | File type, architecture, and format hints. |
| `readelf` | `readelf -a /workspace/sample > /workspace/elf.txt` | ELF headers, sections, symbols, relocations, and notes. |
| `objdump` | `objdump -d /workspace/sample > /workspace/disassembly.txt` | Assembly listing for supported executable sections. |
| `strings` | `strings -a /workspace/sample > /workspace/strings.txt` | Printable strings with no guarantee of runtime use. |
| `nm` | `nm -C /workspace/sample` | Available symbols, with C++ demangling; stripped input may have none. |
| `gdb` | `gdb /workspace/sample` | Interactive debugger; target execution starts when you request run. |
| `strace` | `strace -f -o /workspace/syscalls.txt /workspace/sample` | Observed system calls; this executes the sample. |
| `ltrace` | `ltrace -o /workspace/libcalls.txt /workspace/sample` | Observed library calls when supported; this executes the sample. |
| `gcc` | `gcc -g /workspace/demo.c -o /workspace/demo` | A native executable from your supplied C source. |
| `make` | `make -C /workspace/project` | Outputs defined by the supplied Makefile; it executes build recipes. |
| `nasm` | `nasm -f elf64 /workspace/demo.asm -o /workspace/demo.o` | An x86-64 object file from your supplied assembly. |
| `patchelf` | `patchelf --print-rpath /workspace/sample` | Declared runtime library search path, possibly empty. |
| `eu-readelf` | `eu-readelf -n /workspace/sample` | ELF notes, such as build ID when present. |
| `yara` | `yara /workspace/rules.yar /workspace/sample` | Matching rule names, or no matches. |
| `pwn` | `pwn checksec /workspace/sample` | ELF mitigation summary through pwntools. |
| `checksec` | `checksec /workspace/sample` | Reported RELRO, stack-canary, NX, PIE, and related properties. |
| `python3` | `python3 -c 'import lief; b=lief.parse("/workspace/sample"); print(b.header)'` | Parsed binary header using LIEF. |
| `ROPgadget` | `ROPgadget --binary ./sample --only 'pop|ret'` | Gadget addresses and instructions. |

### Debugging with ptrace

Run this **on the host**, from the repository root, only when debugging is needed:

```bash
docker run --rm -it --cap-drop=ALL --cap-add=SYS_PTRACE \
  --security-opt=no-new-privileges --security-opt=seccomp=unconfined \
  --ulimit fsize=2147483648:2147483648 --network=none \
  --mount "type=bind,src=$PWD/reDocker/workspace,dst=/workspace" \
  redocker:latest
```

Then inside the container, with a compatible executable:

```bash
gdb /workspace/sample
```

At the `(gdb)` prompt (these are debugger commands, not shell commands; `run`
executes the target):

```text
break main
run
info registers
bt
quit
```

A debugger or trace can execute arbitrary target behavior. Native execution needs
matching architecture and kernel support. For x86-64 tools on an ARM host, build
and run with `--platform linux/amd64`; emulation still may not support ptrace.
Static inspection does not need these debug permissions. The image has no
GUI decompiler; Ghidra 12.2 runs headless and recovered pseudocode is not original source.

### Bundled REA engines

Ghidra, Rizin, WABT, GDB and the pwntools profile REA verifies are preconfigured
through image environment variables; no host install or path setting is needed:

```bash
rea doctor --provider ghidra
analyzeHeadless /workspace/ghidra-project sample -import /workspace/sample
rizin -A -qc 'afl' /workspace/sample
wasm-objdump -x /workspace/module.wasm
```

### Python analysis libraries

Inside the container, these examples inspect supplied artifacts without launching them:

```bash
python3 - <<'PYCODE'
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64
from pwnlib.elf.elf import ELF
for instruction in Cs(CS_ARCH_X86, CS_MODE_64).disasm(b'\x90\xc3', 0x1000):
    print(hex(instruction.address), instruction.mnemonic)
with open('/workspace/sample', 'rb') as stream:
    print(ELFFile(stream).header)
print(ELF('/workspace/sample', checksec=False).arch)
print(Uc(UC_ARCH_X86, UC_MODE_64))  # Emulator object; no target code run here.
PYCODE
# For a PE input instead of ELF:
python3 -c 'import pefile; p=pefile.PE("/workspace/sample.exe"); print(p.FILE_HEADER)'
```

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
ls -la reDocker/workspace/results
./scripts/verify.sh reDocker
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
