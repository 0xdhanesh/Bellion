"""Install pinned upstream release executables, verifying published SHA-256 sums."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import zipfile


def download(url: str, target: Path) -> None:
    subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                    '--retry', '3', '--output', str(target), url], check=True)


def install(manifest_path: str, architecture: str) -> None:
    if architecture not in {'amd64', 'arm64'}:
        raise ValueError(f'Unsupported architecture: {architecture}')
    for entry in json.loads(Path(manifest_path).read_text()):
        artifact = entry['assets'][architecture]
        url = f"https://github.com/{entry['repository']}/releases/download/{entry['version']}/"
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            archive, checksums = directory / artifact, directory / 'checksums.txt'
            download(url + artifact, archive)
            download(url + entry['checksums'], checksums)
            expected = None
            for line in checksums.read_text().splitlines():
                fields = line.split()
                if len(fields) == 2 and fields[1].lstrip('*') == artifact:
                    expected = fields[0].lower()
            if expected is None or hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest() != expected:
                raise ValueError(f'Checksum missing or mismatched for {artifact}')
            if artifact.endswith('.zip'):
                with zipfile.ZipFile(archive) as package:
                    contents = package.read(entry['binary'])
            else:
                with tarfile.open(archive) as package:
                    member = package.extractfile(entry['binary'])
                    if member is None:
                        raise ValueError('Executable missing in archive')
                    contents = member.read()
            target = Path('/usr/local/bin') / entry.get('install_as', entry['binary'])
            target.write_bytes(contents)
            target.chmod(0o755)
            print(f"Installed {target.name} {entry['version']} ({architecture})", flush=True)


if __name__ == '__main__':
    install(*sys.argv[1:])
