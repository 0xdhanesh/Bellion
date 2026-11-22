"""Install the pinned Google Cloud SDK archive after SHA-256 verification."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

releases = json.loads(Path('/opt/security/gcloud-release.json').read_text())
release = releases[sys.argv[1]]
with tempfile.TemporaryDirectory() as directory:
    archive = Path(directory) / 'sdk.tar.gz'
    subprocess.run(['curl', '-fsSL', '--retry', '3', '-o', str(archive), release['url']], check=True)
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != release['sha256']:
        raise ValueError('Google Cloud SDK checksum mismatch')
    with tarfile.open(archive) as package:
        package.extractall('/opt', filter='data')
Path('/usr/local/bin/gcloud').symlink_to('/opt/google-cloud-sdk/bin/gcloud')
