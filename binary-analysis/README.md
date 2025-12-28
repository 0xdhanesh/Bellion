# Binary Analysis Environment

Ubuntu 22.04 Docker environment pre-configured with essential binary analysis and reverse engineering tools.

## Features

- **Platform**: x86_64 (amd64) with Rosetta 2 support on Apple Silicon
- **Tools**: file, binutils, strace, ltrace, gdb, hexdump, od
- **Optimized**: For macOS binary analysis workflows

## Quick Start

### Build

```bash
docker build -t binary-analysis:latest ./binary-analysis/
```

### Run

```bash
docker run --rm -it binary-analysis:latest
```

### Analyze Files

```bash
docker run --rm -it -v $(pwd):/analysis binary-analysis:latest
```

## Documentation

- [Detailed Usage Guide](docs/USAGE.md)
- [Tool Reference](docs/TOOLS.md)

## Included Tools

| Tool | Purpose |
|------|---------|
| `file` | File type identification |
| `objdump` | Disassemble binaries |
| `readelf` | ELF file analysis |
| `strings` | Extract printable strings |
| `nm` | List symbols |
| `strace` | Trace system calls |
| `ltrace` | Trace library calls |
| `gdb` | GNU Debugger |
| `hexdump` | Hex viewer |
| `od` | Octal/hex dump |

## Architecture

Built for x86_64 architecture, enabling seamless binary analysis on ARM-based systems through Rosetta 2 emulation on Apple Silicon Macs.
