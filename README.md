# Security Docker Environments

Docker environments for web and mobile pentesting, reverse engineering,
cryptographic analysis, OSINT, networks, Active Directory, and cloud configurations.
Includes MCP integration for Claude, Codex, Grok CLI, and Google Antigravity.

## Environments

| Environment | Purpose | Command guide | MCP guide |
| --- | --- | --- | --- |
| [webPTDocker](webPTDocker/README.md) | Web application pentesting | [Usage](webPTDocker/USAGE.md) | [MCP setup](webPTDocker/MCPUSAGE.md) |
| [mobilePTDocker](mobilePTDocker/README.md) | Android and iOS assessment | [Usage](mobilePTDocker/USAGE.md) | [MCP setup](mobilePTDocker/MCPUSAGE.md) |
| [reDocker](reDocker/README.md) | ELF and native binary analysis | [Usage](reDocker/USAGE.md) | [MCP setup](reDocker/MCPUSAGE.md) |
| [cryptDocker](cryptDocker/README.md) | Cryptographic implementation analysis | [Usage](cryptDocker/USAGE.md) | [MCP setup](cryptDocker/MCPUSAGE.md) |
| [OSINTDocker](OSINTDocker/README.md) | Artifact and website reconnaissance, including REA | [Usage](OSINTDocker/USAGE.md) | [MCP setup](OSINTDocker/MCPUSAGE.md) |
| [networkPTDocker](networkPTDocker/README.md) | Network enumeration and packet analysis | [Usage](networkPTDocker/USAGE.md) | [MCP setup](networkPTDocker/MCPUSAGE.md) |
| [adPTDocker](adPTDocker/README.md) | Windows and Active Directory assessment | [Usage](adPTDocker/USAGE.md) | [MCP setup](adPTDocker/MCPUSAGE.md) |
| [cloudPTDocker](cloudPTDocker/README.md) | Cloud and container configuration assessment | [Usage](cloudPTDocker/USAGE.md) | [MCP setup](cloudPTDocker/MCPUSAGE.md) |

Start Docker Desktop or Docker Engine, choose an environment, and follow its
command guide. Build from the repository root so Docker can access `shared/`.
Each environment's documentation covers tools, expected outputs, and limitations.

## Quick shell access

After building an image, add these Bash/Zsh helpers to `~/.bashrc` or `~/.zshrc`
and source that file. They use the image's `0xdhanesh` account and the project's
capability and file-size defaults.

```bash
dockershell() {
    docker run --rm -it --entrypoint=/bin/bash \
        --cap-drop=ALL --security-opt=no-new-privileges \
        --ulimit fsize=16777216:16777216 "$@"
}

dockershellhere() {
    dockershell --mount "type=bind,src=${PWD},dst=/workspace" \
        --workdir /workspace "$@"
}
```

`dockershellhere` mounts the current folder read/write at `/workspace`, where
saved results persist on the host. Quote filenames containing spaces. Put any
extra Docker options before the image name:

```bash
dockershell webptdocker:latest              # Shell without a host mount
dockershellhere mobileptdocker:latest       # Android/iOS tools with current folder
dockershellhere --network=none redocker:latest
dockershellhere cryptdocker:latest
dockershellhere osintdocker:latest
dockershellhere networkptdocker:latest
dockershellhere adptdocker:latest
dockershellhere cloudptdocker:latest
```

See the [full helper guide](docs/SHELL_HELPERS.md) for tool and MCP shortcuts,
and each environment's usage guide for Linux workspace permissions.

## Project resources

- [Shell helpers](docs/SHELL_HELPERS.md): shortcuts for shells, tools, and MCP launchers.
- [Verification script](scripts/verify.sh): run `./scripts/verify.sh` for all environments, or pass an environment name.
- [Contributing](CONTRIBUTING.md)
- [MIT license](LICENSE); bundled tools retain their own licenses.

Maintained by **[0xdhanesh](https://github.com/0xdhanesh)** · dhanesh.professional@gmail.com
