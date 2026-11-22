# Shell helpers for this project

These Bash/Zsh functions adapt the pasted Docker shortcuts to this repository's
available images. Add them to `~/.zshrc` or `~/.bashrc`, then reload that file with
`source ~/.zshrc` or `source ~/.bashrc`. Build the images once from the repository
root before using the helpers from any directory:

```bash
for environment in webPTDocker mobilePTDocker reDocker cryptDocker OSINTDocker networkPTDocker adPTDocker cloudPTDocker; do
  image=$(printf '%s' "$environment" | tr '[:upper:]' '[:lower:]')
  docker build -f "$environment/Dockerfile" -t "$image:latest" .
done
```

The `here` helpers mount your current directory read/write at `/workspace` and
use it as the working directory. They quote paths containing spaces and retain
the image's `0xdhanesh` account. See each environment's usage guide for native
Linux bind-mount permissions. Files saved under `/workspace` remain on your host.

```bash
# Shared defaults for this project's containers.
_securitydocker() {
    docker run --rm --cap-drop=ALL --security-opt=no-new-privileges \
        --ulimit fsize=16777216:16777216 "$@"
}

_securitydockerhere() {
    _securitydocker --mount "type=bind,src=${PWD},dst=/workspace" \
        --workdir /workspace "$@"
}

# Ghidra projects and JADX caches outgrow 16 MiB files; the Docker CLI applies the
# last --ulimit given, so this raises the cap for mobilePTDocker and reDocker only.
_bellionlarge=(--ulimit fsize=2147483648:2147483648)

# Generic shells: Docker options go before the image; shell arguments after it.
dockershell() {
    _securitydocker -it --entrypoint=/bin/bash "$@"
}

dockershellsh() {
    _securitydocker -it --entrypoint=/bin/sh "$@"
}

dockershellhere() {
    _securitydockerhere -it --entrypoint=/bin/bash "$@"
}

dockershellshhere() {
    _securitydockerhere -it --entrypoint=/bin/sh "$@"
}

# Open a shell in one of the available environments, with the current folder mounted.
webpthere() {
    dockershellhere webptdocker:latest "$@"
}

mobilepthere() {
    dockershellhere "${_bellionlarge[@]}" mobileptdocker:latest "$@"
}

rehere() {
    dockershellhere "${_bellionlarge[@]}" redocker:latest "$@"
}

crypthere() {
    dockershellhere cryptdocker:latest "$@"
}

osinthere() {
    dockershellhere osintdocker:latest "$@"
}

networkpthere() {
    dockershellhere networkptdocker:latest "$@"
}

adpthere() {
    dockershellhere adptdocker:latest "$@"
}

cloudpthere() {
    dockershellhere cloudptdocker:latest "$@"
}

# Direct tool shortcuts, using tools actually installed in these images.
sqlmaphere() {
    _securitydockerhere -it webptdocker:latest sqlmap "$@"
}

apktoolhere() {
    _securitydockerhere -it mobileptdocker:latest apktool "$@"
}

jadxhere() {
    _securitydockerhere -it "${_bellionlarge[@]}" mobileptdocker:latest jadx "$@"
}

gdbhere() {
    _securitydockerhere -it --cap-add=SYS_PTRACE \
        --security-opt=seccomp=unconfined redocker:latest gdb "$@"
}

rizinhere() {
    _securitydockerhere -it "${_bellionlarge[@]}" redocker:latest rizin "$@"
}

opensslhere() {
    _securitydockerhere -it cryptdocker:latest openssl "$@"
}

# REA CLI with each image's bundled engines: OSINT (JADX),
# mobile (JADX, Ghidra), RE (Ghidra, Rizin, WABT, GDB, pwntools).
reahere() {
    _securitydockerhere -it osintdocker:latest rea "$@"
}

reamobilehere() {
    _securitydockerhere -it "${_bellionlarge[@]}" mobileptdocker:latest rea "$@"
}

rearehere() {
    _securitydockerhere -it "${_bellionlarge[@]}" redocker:latest rea "$@"
}

exiftoolhere() {
    _securitydockerhere -it osintdocker:latest exiftool "$@"
}

# Serve the current directory over HTTP, reachable from the host on port 8000.
httphere() {
    _securitydockerhere -it -p 127.0.0.1:8000:8000 webptdocker:latest \
        python3 -m http.server 8000 --bind 0.0.0.0 "$@"
}

# MCP uses stdin/stdout without a TTY. Pass an image, then optional Docker flags.
dockermcphere() {
    if [ "$#" -eq 0 ]; then
        printf '%s\n' 'Usage: dockermcphere IMAGE [DOCKER_OPTIONS...]' >&2
        return 2
    fi
    local image="$1"
    shift
    _securitydockerhere -i "$@" "$image" python3 /opt/security/mcp_server.py
}

# Independent REA MCP server, also without a TTY. Optional IMAGE selects which
# image's bundled engines REA uses (default osintdocker:latest).
reamcphere() {
    local image="${1:-osintdocker:latest}"
    [ "$#" -gt 0 ] && shift
    case "$image" in
        mobileptdocker:*|redocker:*) _securitydockerhere -i "${_bellionlarge[@]}" "$@" "$image" rea mcp ;;
        *) _securitydockerhere -i "$@" "$image" rea mcp ;;
    esac
}

# Register an environment's MCP bridge (or, with MODE rea, its native REA server)
# with a client, mounting the current directory.
# Usage: _bellionmcp CLIENT SERVER_NAME IMAGE [bridge|rea]
_bellionmcp() {
    local client="$1" name="$2" image="$3" mode="${4:-bridge}"
    if ! command -v "$client" >/dev/null 2>&1; then
        printf '%s\n' "$client CLI not found in PATH" >&2
        return 127
    fi
    if ! docker image inspect "$image" >/dev/null 2>&1; then
        printf '%s\n' "Image $image not found; build it first (see above)." >&2
        return 1
    fi
    local fsize=16777216
    case "$image" in mobileptdocker:*|redocker:*) fsize=2147483648 ;; esac
    local -a server=(python3 /opt/security/mcp_server.py)
    [ "$mode" = rea ] && server=(rea mcp)
    local -a launch=(docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges
        --ulimit "fsize=$fsize:$fsize"
        --mount "type=bind,src=$(pwd),dst=/workspace"
        "$image" "${server[@]}")
    case "$client" in
        claude)
            claude mcp add --transport stdio --scope user "$name" -- "${launch[@]}" \
                && claude mcp list && claude mcp get "$name" ;;
        codex)
            codex mcp add "$name" -- "${launch[@]}" \
                && codex mcp list && codex mcp get "$name" ;;
        grok)
            grok mcp add --scope user "$name" -- "${launch[@]}" \
                && grok mcp list && grok mcp doctor "$name" ;;
        agy)
            agy mcp add --type stdio "$name" -- "${launch[@]}" \
                && agy mcp list ;;
    esac
}

# Claude Code
webptmcp-claude()     { _bellionmcp claude webPTDocker     webptdocker:latest; }
mobptmcp-claude()     { _bellionmcp claude mobilePTDocker  mobileptdocker:latest; }
remcp-claude()        { _bellionmcp claude reDocker        redocker:latest; }
cryptmcp-claude()     { _bellionmcp claude cryptDocker     cryptdocker:latest; }
osintmcp-claude()     { _bellionmcp claude OSINTDocker     osintdocker:latest; }
netptmcp-claude()     { _bellionmcp claude networkPTDocker networkptdocker:latest; }
adptmcp-claude()      { _bellionmcp claude adPTDocker      adptdocker:latest; }
cloudptmcp-claude()   { _bellionmcp claude cloudPTDocker   cloudptdocker:latest; }

# Codex
webptmcp-codex()      { _bellionmcp codex webPTDocker     webptdocker:latest; }
mobptmcp-codex()      { _bellionmcp codex mobilePTDocker  mobileptdocker:latest; }
remcp-codex()         { _bellionmcp codex reDocker        redocker:latest; }
cryptmcp-codex()      { _bellionmcp codex cryptDocker     cryptdocker:latest; }
osintmcp-codex()      { _bellionmcp codex OSINTDocker     osintdocker:latest; }
netptmcp-codex()      { _bellionmcp codex networkPTDocker networkptdocker:latest; }
adptmcp-codex()       { _bellionmcp codex adPTDocker      adptdocker:latest; }
cloudptmcp-codex()    { _bellionmcp codex cloudPTDocker   cloudptdocker:latest; }

# Grok Build CLI
webptmcp-grok()       { _bellionmcp grok webPTDocker     webptdocker:latest; }
mobptmcp-grok()       { _bellionmcp grok mobilePTDocker  mobileptdocker:latest; }
remcp-grok()          { _bellionmcp grok reDocker        redocker:latest; }
cryptmcp-grok()       { _bellionmcp grok cryptDocker     cryptdocker:latest; }
osintmcp-grok()       { _bellionmcp grok OSINTDocker     osintdocker:latest; }
netptmcp-grok()       { _bellionmcp grok networkPTDocker networkptdocker:latest; }
adptmcp-grok()        { _bellionmcp grok adPTDocker      adptdocker:latest; }
cloudptmcp-grok()     { _bellionmcp grok cloudPTDocker   cloudptdocker:latest; }

# Google Antigravity
webptmcp-agy()        { _bellionmcp agy webPTDocker     webptdocker:latest; }
mobptmcp-agy()        { _bellionmcp agy mobilePTDocker  mobileptdocker:latest; }
remcp-agy()           { _bellionmcp agy reDocker        redocker:latest; }
cryptmcp-agy()        { _bellionmcp agy cryptDocker     cryptdocker:latest; }
osintmcp-agy()        { _bellionmcp agy OSINTDocker     osintdocker:latest; }
netptmcp-agy()        { _bellionmcp agy networkPTDocker networkptdocker:latest; }
adptmcp-agy()         { _bellionmcp agy adPTDocker      adptdocker:latest; }
cloudptmcp-agy()      { _bellionmcp agy cloudPTDocker   cloudptdocker:latest; }

# Native REA servers, one per image that bundles REA engines.
for _client in claude codex grok agy; do
    eval "osintreamcp-$_client() { _bellionmcp $_client osint-rea  osintdocker:latest    rea; }"
    eval "mobreamcp-$_client()   { _bellionmcp $_client mobile-rea mobileptdocker:latest rea; }"
    eval "rereamcp-$_client()    { _bellionmcp $_client re-rea     redocker:latest       rea; }"
done
unset _client
```

### One-command MCP registration

Each `<env>mcp-<client>` function registers that environment's MCP bridge with the
client, mounting the **directory you run it from** as `/workspace`, then lists the
registered servers and checks the new one (`mcp get` for Claude/Codex, `mcp doctor`
for Grok). The prefixes are `webpt`, `mobpt`, `re`, `crypt`, `osint`, `netpt`,
`adpt`, and `cloudpt`; the clients are `claude`, `codex`, `grok`, and `agy`.
`osintreamcp-<client>`, `mobreamcp-<client>` and `rereamcp-<client>` register the
native REA server of that image as `osint-rea`, `mobile-rea` or `re-rea`; each
uses only the engines bundled in its image.

```bash
cd ~/engagements/app1
mobptmcp-claude      # mobilePTDocker -> Claude Code, mounting ~/engagements/app1
adptmcp-grok         # adPTDocker -> Grok Build CLI, mounting the current folder
```

The mount path is recorded at registration time, so run the function from the folder
you want the agent to see. Registering an existing name again fails; remove it with the
client's `mcp remove` command first. These helpers need the image built and the client
CLI in `PATH`, and they stop with a message if either is missing.

Examples, run from the directory holding your artifacts:

```bash
webpthere                              # Interactive web testing shell
mobilepthere                           # Interactive Android/iOS tooling shell
rehere                                 # Interactive native binary analysis shell
crypthere                              # Interactive crypto analysis shell
osinthere                              # Interactive OSINT/recon shell

dockershell webptdocker:latest          # Shell without a host mount
dockershellshhere mobileptdocker:latest # /bin/sh with the current folder mounted
dockershellhere --network=none redocker:latest

sqlmaphere --help
apktoolhere d /workspace/app.apk -o /workspace/decoded
gdbhere /workspace/sample
opensslhere dgst -sha256 /workspace/sample
reahere analyze-javascript-application /workspace/extracted-app --json
reamobilehere doctor --provider jadx --provider ghidra
jadxhere -d /workspace/jadx-out /workspace/app.apk
rizinhere -A /workspace/sample
exiftoolhere /workspace/document.pdf
httphere                               # Visit http://127.0.0.1:8000; Ctrl-C to stop
```

`gdbhere` enables ptrace and relaxes seccomp for debugging; it still requires
compatible host architecture/kernel support. Use `dockershellhere --network=none
redocker:latest` for offline static work. `httphere` serves the entire current
directory without authentication, so choose the directory deliberately. This
Python HTTP server provides basic file serving; it does not supply HTTPS,
WebDAV, SMB, or request-body uploads. The Windows-context, Impacket, Metasploit,
and specialized serving shortcuts from the original snippet depend on images
outside this project and are replaced here by the available shells and tools.

`dockermcphere webptdocker:latest --network=none` and `reamcphere [IMAGE]` are stdio MCP
launchers, not interactive shells. They wait for MCP protocol messages. For an
MCP client that launches a shell, source your helper file explicitly and change
to the intended host workspace before invoking one. Clients that execute
commands directly should use the supplied `mcp.json` entries with an absolute
workspace path; shell functions are not standalone executables.
