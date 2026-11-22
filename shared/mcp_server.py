"""Local stdio MCP bridge for the tools installed in one security image."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile

from mcp.server.fastmcp import FastMCP

MANIFEST = Path(os.environ.get("TOOL_MANIFEST", "/opt/security/tools.json"))
WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace")).resolve()
MAX_OUTPUT = 65536
mcp = FastMCP(os.environ.get("SECURITY_ENV", "security-tools"))


def manifest() -> dict:
    return json.loads(MANIFEST.read_text())


@mcp.tool()
def list_tools() -> dict:
    """List this image's permitted executables and whether each is installed."""
    return {name: shutil.which(name) is not None for name in manifest()["commands"]}


@mcp.tool()
def run_tool(command: str, args: list[str], cwd: str = "/workspace", timeout: int = 60) -> dict:
    """Run an installed executable directly, without shell expansion.

    args is an argument array; cwd must remain under /workspace. Output is
    capped at 64 KiB per stream; timeout is 1–300 seconds. Interpreters and
    tool scripting options can execute code, so use only with trusted clients.
    """
    if command not in manifest()["commands"]:
        raise ValueError("Command is not in this environment's tool manifest")
    if not 1 <= timeout <= 300:
        raise ValueError("timeout must be between 1 and 300 seconds")
    directory = Path(cwd).resolve()
    if not directory.is_relative_to(WORKSPACE) or not directory.is_dir():
        raise ValueError("cwd must be an existing directory under /workspace")
    executable = shutil.which(command)
    if executable is None:
        raise ValueError(f"Executable is not installed: {command}")
    # Files avoid unbounded in-memory PIPE buffers. Container storage quotas
    # still matter for noisy commands; see the README.
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen(
            [executable, *args], cwd=directory, stdin=subprocess.DEVNULL,
            stdout=stdout, stderr=stderr, start_new_session=True,
        )
        timed_out = False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            # Clean up descendants even if their parent exited before timeout.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        result = {"exit_code": process.returncode, "timed_out": timed_out}
        for name, stream in (("stdout", stdout), ("stderr", stderr)):
            stream.seek(0)
            data = stream.read(MAX_OUTPUT + 1)
            result[name] = data[:MAX_OUTPUT].decode("utf-8", errors="replace")
            result[f"{name}_truncated"] = len(data) > MAX_OUTPUT
        return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
