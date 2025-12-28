# Docker Environments Collection

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

A collection of specialized Docker environments for security research, reverse engineering, and development workflows. Optimized for macOS (Apple Silicon).

## Available Environments

### 🔍 [Binary Analysis](binary-analysis/)

Ubuntu 22.04 environment with comprehensive binary analysis and reverse engineering tools.

**Tools**: file, binutils (objdump, readelf, strings, nm), strace, ltrace, gdb, hexdump, od

**Quick Start**:
```bash
docker build -t binary-analysis:latest ./binary-analysis/
docker run --rm -it binary-analysis:latest
```

**Use Cases**:
- Static binary analysis
- Dynamic analysis with strace/ltrace
- Debugging with GDB
- Reverse engineering x86_64 binaries

[📖 Full Documentation](binary-analysis/README.md)

---

## Planned Environments

### 🔧 Firmware Analysis *(Coming Soon)*
Tools for embedded firmware extraction, analysis, and reverse engineering.

**Planned Tools**: binwalk, firmware-mod-kit, QEMU, radare2, ghidra

### 🌐 Network Reconnaissance *(Coming Soon)*
Comprehensive network scanning and reconnaissance toolkit.

**Planned Tools**: nmap, masscan, gobuster, ffuf, nuclei, httpx

### 🛡️ Web Application Testing *(Coming Soon)*
Environment for web application security testing and analysis.

**Planned Tools**: Burp Suite CLI, sqlmap, nikto, wpscan, ffuf

---

## Project Structure

```
.
├── binary-analysis/          # Binary analysis environment
│   ├── Dockerfile
│   ├── README.md
│   ├── .dockerignore
│   └── docs/
│       ├── USAGE.md
│       └── TOOLS.md
├── firmware-analysis/        # (Coming soon)
├── network-recon/           # (Coming soon)
├── web-testing/             # (Coming soon)
├── README.md                # This file
├── LICENSE
└── CONTRIBUTING.md
```

## General Usage

Each environment follows a consistent structure:

```bash
# Build an environment
docker build -t <env-name>:latest ./<env-directory>/

# Run interactively
docker run --rm -it <env-name>:latest

# Mount files for analysis
docker run --rm -it -v $(pwd):/analysis <env-name>:latest
```

## Requirements

- [Docker](https://www.docker.com/get-started) installed
- For Apple Silicon Macs: Rosetta 2 (automatically used for x86_64 environments)

## macOS Optimization

All environments are optimized for macOS, particularly Apple Silicon:

- **Platform Emulation**: x86_64 environments use Rosetta 2 for seamless emulation
- **Performance**: Optimized for M-series chip architecture
- **Compatibility**: Full support for analyzing x86_64 binaries on ARM hardware

## Contributing

Contributions are welcome! Whether you want to:
- Improve existing environments
- Add new tools to current environments
- Propose new environment types
- Fix bugs or improve documentation

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**0xdhanesh**
- GitHub: [@0xdhanesh](https://github.com/0xdhanesh)
- Email: dhanesh.professional@gmail.com

## Acknowledgments

- Built on industry-standard tools and frameworks
- Designed for security researchers and developers
- Community-driven development

---

## Quick Links

- [Binary Analysis Environment](binary-analysis/) - Available now ✅
- [Contributing Guidelines](CONTRIBUTING.md)
- [License](LICENSE)
