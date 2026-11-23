"""Run inside each built image: python3 - < tests/smoke_mcp.py."""
import asyncio
import json
import importlib
import os
import subprocess
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def check_projectdiscovery():
    import http.server
    from pathlib import Path
    import tempfile
    import threading

    def execute(*args):
        result = subprocess.run(args, text=True, capture_output=True, timeout=60)
        assert result.returncode == 0, (args, result.stdout, result.stderr)
        return result.stdout + result.stderr

    for tool in ['subfinder', 'dnsx', 'httpx-pd', 'katana', 'nuclei', 'naabu', 'interactsh-client']:
        execute(tool, '-version')
    assert Path('/opt/nuclei-templates/http').is_dir()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'security docker fixture')

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}'
    try:
        output = execute('httpx-pd', '-u', url, '-sc', '-silent', '-duc', '-timeout', '5')
        assert '200' in output, output
        output = execute('naabu', '-host', '127.0.0.1', '-p', str(server.server_port),
                         '-scan-type', 'c', '-silent', '-duc', '-verify')
        assert str(server.server_port) in output, output
        with tempfile.TemporaryDirectory() as directory:
            template = Path(directory) / 'fixture.yaml'
            template.write_text("""id: security-docker-fixture
info:
  name: Local fixture
  author: 0xdhanesh
  severity: info
http:
  - method: GET
    path:
      - "{{BaseURL}}"
    matchers:
      - type: word
        words:
          - "security docker fixture"
""")
            output = execute('nuclei', '-u', url, '-t', str(template), '-ni', '-duc', '-silent')
            assert 'security-docker-fixture' in output, output
    finally:
        server.shutdown()
        server.server_close()
    print('PASS: ProjectDiscovery versions, bundled templates, local HTTPX/Nuclei/Naabu operations')



def check_network_tools():
    from pathlib import Path
    import struct
    import tempfile
    # One synthetic Ethernet/IPv4/TCP packet, 192.0.2.1:12345 -> 198.51.100.2:443.
    packet = bytes.fromhex('00112233445566778899aabb0800'
                           '450000280000000040060000c0000201c6336402'
                           '303901bb00000000000000005002040000000000')
    with tempfile.TemporaryDirectory() as directory:
        capture = Path(directory) / 'fixture.pcap'
        capture.write_bytes(struct.pack('<IHHIIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1)
                            + struct.pack('<IIII', 1, 0, len(packet), len(packet)) + packet)
        result = subprocess.check_output(['tshark', '-r', str(capture), '-T', 'fields',
                                          '-e', 'ip.src', '-e', 'tcp.dstport'], text=True)
        assert '192.0.2.1' in result and '443' in result, result
        subprocess.run(['capinfos', str(capture)], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(['tcpdump', '-nn', '-r', str(capture), '-c', '1'], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['nmap', '--version'], check=True, stdout=subprocess.DEVNULL)
    for command in (['masscan', '--version'], ['arp-scan', '--version'], ['proxychains4', '-q', '/bin/true'],
                    ['chisel', '--version'], ['ligolo-proxy', '-h'], ['ligolo-agent', '-h'],
                    ['responder', '--help']):
        # Some print usage and exit non-zero for -h; require a clean exit or visible output.
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0 or result.stdout + result.stderr, (command, result)
    print('PASS: offline packet parsing with TShark, capinfos, tcpdump; Nmap starts')



def check_ad_tools():
    from impacket.smb3structs import SMB2Packet
    packet = SMB2Packet()
    packet['TreeID'] = 42
    encoded = packet.getData()
    parsed = SMB2Packet(encoded)
    assert encoded.startswith(b'\xfeSMB') and parsed['TreeID'] == 42, encoded
    for tool in ['GetADUsers.py', 'GetUserSPNs.py', 'findDelegation.py',
                 'smbclient.py', 'rpcdump.py', 'lookupsid.py', 'mssqlclient.py',
                 'secretsdump.py', 'ntlmrelayx.py', 'GetNPUsers.py', 'ticketer.py',
                 'certipy', 'bloodhound-python', 'evil-winrm']:
        subprocess.run([tool, '-h'], check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=30)
    subprocess.run(['kerbrute', 'version'], check=True, stdout=subprocess.DEVNULL, timeout=30)
    print('PASS: Impacket SMB2 serialization and AD client startup; no domain contacted')



def check_cloud_tools():
    import boto3
    from botocore.stub import Stubber

    assert 'aws-cli/1.46.3' in subprocess.check_output(['aws', '--version'], text=True)
    versions = json.loads(subprocess.check_output(['az', 'version', '--output', 'json'], text=True))
    assert versions['azure-cli'] == '2.93.0', versions
    assert '594.0.0' in subprocess.check_output(['gcloud', '--version'], text=True)
    assert '0.76.1' in subprocess.check_output(['trivy', '--version'], text=True)
    assert '5.48.0' in subprocess.check_output(['prowler', '--version'], text=True)
    for command in (['scout', '--help'], ['kube-hunter', '--help']):
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, timeout=120)
    # Explicit fake credentials and stubbed response: no provider or metadata call.
    client = boto3.client('sts', region_name='us-east-1',
                          aws_access_key_id='fixture', aws_secret_access_key='fixture')
    with Stubber(client) as stub:
        stub.add_response('get_caller_identity', {'UserId': 'fixture', 'Account': '123456789012',
                          'Arn': 'arn:aws:iam::123456789012:user/fixture'})
        assert client.get_caller_identity()['Account'] == '123456789012'
    print('PASS: cloud CLI startup and stubbed AWS SDK')


def check_crypt_tools():
    from pathlib import Path
    import tempfile
    devices = subprocess.run(['hashcat', '-I'], text=True, capture_output=True, timeout=120)
    assert devices.returncode == 0 and 'OpenCL' in devices.stdout, (devices.stdout, devices.stderr)
    with tempfile.TemporaryDirectory() as directory:
        hashes, words = Path(directory, 'hash.txt'), Path(directory, 'words.txt')
        hashes.write_text('5f4dcc3b5aa765d61d8327deb882cf99\n')  # MD5("password")
        words.write_text('letmein\npassword\n')
        result = subprocess.run(['hashcat', '-m', '0', '-a', '0', '--potfile-disable', '--quiet',
                                 '--outfile', str(Path(directory, 'out.txt')), '--outfile-format', '2',
                                 str(hashes), str(words)], text=True, capture_output=True, timeout=300)
        assert Path(directory, 'out.txt').read_text().strip() == 'password', (result.stdout, result.stderr)
    print('PASS: hashcat cracks with the bundled PoCL CPU OpenCL runtime')


async def main():
    assert subprocess.check_output(['whoami'], text=True).strip() == '0xdhanesh'
    modules = {
        'networkPTDocker': [],
        'adPTDocker': ['impacket', 'ldap3', 'dns'],
        'cloudPTDocker': ['boto3', 'requests'],
        'webPTDocker': ['bs4', 'requests', 'mitmproxy'],
        'mobilePTDocker': ['androguard', 'frida'],
        'reDocker': ['capstone', 'lief', 'pefile', 'pwnlib', 'elftools', 'unicorn'],
        'cryptDocker': ['cryptography', 'gmpy2', 'Crypto', 'sympy', 'z3'],
        'OSINTDocker': ['androguard', 'bs4', 'dns', 'requests'],
    }
    extra = {
        'webPTDocker': [['feroxbuster', '--version'], ['dalfox', '--version'], ['arjun', '-h'],
                        ['jwt_tool', '-h']],
        'cryptDocker': [['xortool', '--help']],
        'OSINTDocker': [['sherlock', '--version'], ['maigret', '--version'], ['theHarvester', '-h'],
                        ['subfinder', '-version'], ['dnsx', '-version'], ['httpx-pd', '-version']],
        'mobilePTDocker': [['objection', '--help']],
        'reDocker': [['ROPgadget', '--help'], ['checksec', '--help']],
    }
    for command in extra.get(os.environ['SECURITY_ENV'], []):
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    for module in modules[os.environ['SECURITY_ENV']]:
        importlib.import_module(module)
    if os.environ['SECURITY_ENV'] == 'webPTDocker':
        subprocess.run(['mitmdump', '--version'], check=True)
        check_projectdiscovery()
    if os.environ['SECURITY_ENV'] in {'mobilePTDocker', 'OSINTDocker'}:
        subprocess.run(['apktool', '--version'], check=True)
    if os.environ['SECURITY_ENV'] == 'mobilePTDocker':
        subprocess.run(['frida', '--version'], check=True)
    if os.environ['SECURITY_ENV'] == 'cloudPTDocker':
        check_cloud_tools()
    if os.environ['SECURITY_ENV'] == 'adPTDocker':
        check_ad_tools()
    if os.environ['SECURITY_ENV'] == 'networkPTDocker':
        check_network_tools()
    if os.environ['SECURITY_ENV'] == 'reDocker':
        subprocess.run(['readelf', '-h', '/bin/true'], check=True, stdout=subprocess.DEVNULL)
    if os.environ['SECURITY_ENV'] == 'cryptDocker':
        from Crypto.Hash import SHA256
        assert SHA256.new(b'abc').hexdigest() == 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
        import sympy
        assert sympy.factorint(65535) == {3: 1, 5: 1, 17: 1, 257: 1}
        check_crypt_tools()
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
