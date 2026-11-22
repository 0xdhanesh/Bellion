"""Run inside each built image: python3 - < tests/smoke_mcp.py."""
import asyncio
import json
import importlib
import os
import subprocess
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    assert subprocess.check_output(['whoami'], text=True).strip() == '0xdhanesh'
    modules = {
        'webPTDocker': ['bs4', 'requests', 'mitmproxy'],
        'mobilePTDocker': ['androguard', 'frida'],
        'reDocker': ['capstone', 'lief', 'pefile', 'pwnlib', 'elftools', 'unicorn'],
        'cryptDocker': ['cryptography', 'gmpy2', 'Crypto', 'sympy', 'z3'],
        'OSINTDocker': ['androguard', 'bs4', 'dns', 'requests'],
    }
    for module in modules[os.environ['SECURITY_ENV']]:
        importlib.import_module(module)
    if os.environ['SECURITY_ENV'] == 'webPTDocker':
        subprocess.run(['mitmdump', '--version'], check=True)
    if os.environ['SECURITY_ENV'] in {'mobilePTDocker', 'OSINTDocker'}:
        subprocess.run(['apktool', '--version'], check=True)
    if os.environ['SECURITY_ENV'] == 'mobilePTDocker':
        subprocess.run(['frida', '--version'], check=True)
    if os.environ['SECURITY_ENV'] == 'reDocker':
        subprocess.run(['readelf', '-h', '/bin/true'], check=True, stdout=subprocess.DEVNULL)
    if os.environ['SECURITY_ENV'] == 'cryptDocker':
        from Crypto.Hash import SHA256
        assert SHA256.new(b'abc').hexdigest() == 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
        import sympy
        assert sympy.factorint(65535) == {3: 1, 5: 1, 17: 1, 257: 1}
    params = StdioServerParameters(command=sys.executable, args=['/opt/security/mcp_server.py'])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = {tool.name for tool in (await session.list_tools()).tools}
            assert names == {'list_tools', 'run_tool'}, names
            inventory = await session.call_tool('list_tools', {})
            installed = json.loads(inventory.content[0].text)
            assert all(installed.values()), installed

            async def run(args, **overrides):
                result = await session.call_tool('run_tool', {'command': 'python3', 'args': args, **overrides})
                assert not result.isError, result
                return json.loads(result.content[0].text)

            result = await run(['-c', 'import sys; print("connected"); print("err", file=sys.stderr); sys.exit(7)'])
            assert result['exit_code'] == 7 and result['stdout'] == 'connected\n' and result['stderr'] == 'err\n', result
            result = await run(['-c', 'import time; time.sleep(10)'], timeout=1)
            assert result['timed_out'] is True, result
            result = await run(['-c', 'print("x" * 70000)'])
            assert result['stdout_truncated'] and len(result['stdout']) == 65536, result
            result = await run(['-c', 'import sys; print(sys.argv[1])', '$(id); echo injected'])
            assert result['stdout'] == '$(id); echo injected\n', result
            for arguments in (
                {'command': '/bin/sh', 'args': []},
                {'command': 'python3', 'args': [], 'cwd': '/etc'},
                {'command': 'python3', 'args': [], 'timeout': 301},
            ):
                result = await session.call_tool('run_tool', arguments)
                assert result.isError, result
            # Symlink traversal must also fail cwd validation.
            os.symlink('/etc', '/workspace/outside')
            try:
                result = await session.call_tool('run_tool', {'command': 'python3', 'args': [], 'cwd': '/workspace/outside'})
                assert result.isError, result
            finally:
                os.unlink('/workspace/outside')
    print('PASS: identity, installed tools, MCP handshake, execution, timeout, truncation, argument boundaries, validation')


asyncio.run(main())
