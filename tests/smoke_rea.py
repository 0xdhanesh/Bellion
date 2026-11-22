"""Verify REA and its bundled engines inside an image: python3 - < tests/smoke_rea.py."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import tempfile
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Engines each image bundles; `rea doctor --provider` must report them healthy
# using only paths baked into the image.
PROVIDERS = {
    'OSINTDocker': ['jadx'],
    'mobilePTDocker': ['jadx', 'ghidra'],
    'reDocker': ['ghidra'],
}


def doctor(provider: str) -> None:
    result = subprocess.run(['rea', 'doctor', '--provider', provider, '--json'],
                            text=True, capture_output=True, timeout=180)
    report = json.loads(result.stdout)
    checks = [check for check in report['checks'] if check['name'] == provider]
    assert checks and all(check['ok'] for check in checks), (provider, checks, result.stderr[-2000:])


def engine_versions(environment: str) -> None:
    def run(*args):
        return subprocess.run(args, text=True, capture_output=True, check=True, timeout=120).stdout

    if environment == 'mobilePTDocker':
        assert '1.5.6' in run('jadx', '--version')
        servers = sorted(Path(os.environ['FRIDA_SERVER_DIR']).glob('frida-server-17.23.2-android-*'))
        assert len(servers) == 4 and all(os.access(path, os.X_OK) for path in servers), servers
        assert run('frida', '--version').strip() == '17.23.2'
    if environment == 'reDocker':
        assert '0.9.1' in run(os.environ['REA_RIZIN_COMMAND'], '-v')
        assert run(str(Path(os.environ['REA_WABT_BIN_DIRECTORY']) / 'wasm-objdump'), '--version').strip() == '1.0.42'
        import pwnlib
        assert pwnlib.__version__ == '4.15.0', pwnlib.__version__


def rea_json(*args, timeout=600):
    result = subprocess.run(['rea', *args, '--json'], text=True, capture_output=True, timeout=timeout)
    assert result.returncode == 0, (args, result.stdout[-3000:], result.stderr[-3000:])
    return result.stdout


def real_analysis(environment: str) -> list[str]:
    """Doctor checks configuration only; run each bundled engine on a real target."""
    done = []
    apk = Path('/fixtures/ApiDemos-debug.apk')
    if 'jadx' in PROVIDERS[environment]:
        assert apk.is_file(), 'mount tests/fixtures at /fixtures (scripts/verify.sh does this)'
        output = rea_json('inspect-android-method', str(apk), 'io.appium.android.apis.ApiDemos', 'onCreate')
        assert '"id":"jadx"' in output and 'onCreate' in output and '"isError":true' not in output, output[:3000]
        done.append('JADX method decompile of ApiDemos')
    if 'ghidra' in PROVIDERS[environment]:
        if environment == 'reDocker':
            source = Path('/tmp/sample.c')
            source.write_text('int secret_check(int x) { return (x * 7) ^ 0x1337; }\n'
                              'int main(int c, char **v) { return secret_check(c); }\n')
            subprocess.run(['gcc', '-O0', '-o', '/tmp/sample', str(source)], check=True)
            target, procedure, marker = '/tmp/sample', 'secret_check', '0x1337'
        else:
            target = str(next(Path('/usr/lib').glob('*-linux-gnu/libplist-2.0.so.4')))
            procedure, marker = 'plist_new_dict', 'plist_new_dict'
        output = rea_json('decompile', target, procedure, '--provider', 'ghidra')
        assert '"id":"ghidra"' in output and marker in output, output[:3000]
        done.append(f'Ghidra decompile of {procedure}')
    return done


async def main():
    environment = os.environ['SECURITY_ENV']
    for provider in PROVIDERS[environment]:
        doctor(provider)
    engine_versions(environment)
    analysed = real_analysis(environment)
    async with stdio_client(StdioServerParameters(command='rea', args=['mcp'])) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = {tool.name for tool in (await session.list_tools()).tools}
            assert 'inspect_artifact' in names, names
            assert 'analyze_javascript_application' in names, names
            with tempfile.TemporaryDirectory(dir='/workspace') as directory:
                target = Path(directory)
                (target / 'package.json').write_text(json.dumps({'name': 'mcp-fixture', 'type': 'module'}))
                (target / 'index.js').write_text('export function greet(name) { return "Hello " + name; }\n')
                result = await session.call_tool('analyze_javascript_application', {'input_path': directory})
                assert not result.isError, result
            print(f'PASS: REA MCP handshake, {len(names)} native tools, static JavaScript analysis, '
                  f'bundled engines healthy: {", ".join(PROVIDERS[environment])}; '
                  f'real analysis: {", ".join(analysed)}')

asyncio.run(main())
