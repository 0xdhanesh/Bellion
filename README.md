# Security Docker Environments

Docker environments for web and mobile pentesting, reverse engineering,
cryptographic analysis, and OSINT, with MCP integration for Claude, Codex,
Grok CLI, and Google Antigravity.

## Environments

| Environment | Purpose | Command guide | MCP guide |
| --- | --- | --- | --- |
| [webPTDocker](webPTDocker/README.md) | Web application pentesting | [Usage](webPTDocker/USAGE.md) | [MCP setup](webPTDocker/MCPUSAGE.md) |
| [mobilePTDocker](mobilePTDocker/README.md) | Android and iOS assessment | [Usage](mobilePTDocker/USAGE.md) | [MCP setup](mobilePTDocker/MCPUSAGE.md) |
| [reDocker](reDocker/README.md) | ELF and native binary analysis | [Usage](reDocker/USAGE.md) | [MCP setup](reDocker/MCPUSAGE.md) |
| [cryptDocker](cryptDocker/README.md) | Cryptographic implementation analysis | [Usage](cryptDocker/USAGE.md) | [MCP setup](cryptDocker/MCPUSAGE.md) |
| [OSINTDocker](OSINTDocker/README.md) | Artifact and website reconnaissance, including REA | [Usage](OSINTDocker/USAGE.md) | [MCP setup](OSINTDocker/MCPUSAGE.md) |

Start Docker Desktop or Docker Engine, choose an environment, and follow its
command guide. Build from the repository root so Docker can access `shared/`.
Each environment's documentation covers tools, expected outputs, and limitations.

## Project resources

- [Shell helpers](docs/SHELL_HELPERS.md): shortcuts for shells, tools, and MCP launchers.
- [Verification script](scripts/verify.sh): run `./scripts/verify.sh` for all environments, or pass an environment name.
- [Contributing](CONTRIBUTING.md)
- [MIT license](LICENSE); bundled tools retain their own licenses.

Maintained by **[0xdhanesh](https://github.com/0xdhanesh)** · dhanesh.professional@gmail.com
