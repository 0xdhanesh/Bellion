"""Install pinned release artifacts (JARs, archives, xz files), verifying SHA-256.

Manifest entries:
  name     label printed in the build log
  url      download URL, or {"amd64": url, "arm64": url}
  sha256   expected digest, or {"amd64": digest, "arm64": digest}
  install  file | xz | zip | tar
  dest     target file (file/xz) or directory (zip/tar)
  strip    leading path components dropped from archive members (zip/tar)
  mode     octal permission string for file/xz targets (default "0644")
"""
import hashlib
import json
import lzma
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile


def pick(value, architecture: str):
    if isinstance(value, dict):
        if architecture not in value:
            raise ValueError(f'No {architecture} variant in {value}')
        return value[architecture]
    return value


def download(url: str, target: Path) -> None:
    subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                    '--retry', '3', '--output', str(target), url], check=True)


def safe_member(name: str, strip: int) -> PurePosixPath | None:
    parts = PurePosixPath(name).parts[strip:]
    if not parts:
        return None
    if any(part in ('..', '') for part in parts) or PurePosixPath(name).is_absolute():
        raise ValueError(f'Unsafe archive member: {name}')
    return PurePosixPath(*parts)


def extract_zip(archive: Path, dest: Path, strip: int) -> None:
    with zipfile.ZipFile(archive) as package:
        for info in package.infolist():
            relative = safe_member(info.filename, strip)
            if relative is None:
                continue
            target = dest / relative
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with package.open(info) as source, target.open('wb') as sink:
                shutil.copyfileobj(source, sink)
            unix_mode = (info.external_attr >> 16) & 0o777
            target.chmod(unix_mode or 0o644)


def extract_tar(archive: Path, dest: Path, strip: int) -> None:
    with tarfile.open(archive) as package:
        for member in package.getmembers():
            relative = safe_member(member.name, strip)
            if relative is None:
                continue
            member.name = str(relative)
            if member.islnk():
                hard = safe_member(member.linkname, strip)
                if hard is None:
                    raise ValueError(f'Unsafe hard link in archive: {member.linkname}')
                member.linkname = str(hard)
            # The 'data' filter refuses absolute paths and links escaping dest.
            package.extract(member, dest, filter='data')


def install(manifest_path: str, architecture: str) -> None:
    if architecture not in {'amd64', 'arm64'}:
        raise ValueError(f'Unsupported architecture: {architecture}')
    for entry in json.loads(Path(manifest_path).read_text()):
        url, expected = pick(entry['url'], architecture), pick(entry['sha256'], architecture).lower()
        dest, kind = Path(entry['dest']), entry['install']
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / 'artifact'
            download(url, artifact)
            with artifact.open('rb') as handle:
                actual = hashlib.file_digest(handle, 'sha256').hexdigest()
            if actual != expected:
                raise ValueError(f"{entry['name']}: SHA-256 {actual} does not match pinned {expected}")
            if kind in {'file', 'xz'}:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if kind == 'xz':
                    with lzma.open(artifact) as source, dest.open('wb') as sink:
                        shutil.copyfileobj(source, sink)
                else:
                    shutil.copyfile(artifact, dest)
                dest.chmod(int(entry.get('mode', '0644'), 8))
            elif kind in {'zip', 'tar'}:
                dest.mkdir(parents=True, exist_ok=True)
                (extract_zip if kind == 'zip' else extract_tar)(artifact, dest, int(entry.get('strip', 0)))
            else:
                raise ValueError(f'Unknown install kind: {kind}')
        print(f"Installed {entry['name']} -> {dest} ({architecture}, sha256 verified)", flush=True)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('usage: install_artifacts.py MANIFEST.json amd64|arm64')
    os.umask(0o022)
    install(*sys.argv[1:])
