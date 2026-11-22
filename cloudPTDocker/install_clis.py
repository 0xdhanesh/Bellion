"""Install AWS and Azure CLIs in isolated, version-pinned Python environments."""
import json
from pathlib import Path
import subprocess
import sys

versions = json.loads(Path('/opt/security/versions.json').read_text())
for package, directory, command in [('awscli', '/opt/aws-venv', 'aws'),
                                     ('azure-cli', '/opt/azure-venv', 'az')]:
    subprocess.run([sys.executable, '-m', 'venv', directory], check=True)
    subprocess.run([directory + '/bin/pip', 'install', '--no-cache-dir',
                    package + '==' + versions[package]], check=True)
    Path('/usr/local/bin', command).symlink_to(Path(directory, 'bin', command))
