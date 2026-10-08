"""Explicit network operations only: immutable HF revisions and Argos packages."""
from __future__ import annotations
import hashlib
import json
import shutil
import threading
import zipfile
from pathlib import Path
import requests

ASR_REPOS = {size: f'Systran/faster-whisper-{size}' for size in ('tiny', 'base', 'small', 'medium', 'large-v3')}
ARGOS_INDEX = 'https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json'


class Cancelled(Exception): pass


def download(url, target, progress, cancel, expected_size=None, sha256=None):
    target = Path(target); target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_suffix(target.suffix + '.part')
    digest = hashlib.sha256(); received = 0
    try:
        with requests.get(url, stream=True, timeout=(15, 60)) as response:
            response.raise_for_status()
            total = expected_size or int(response.headers.get('content-length', 0)) or None
            with part.open('wb') as f:
                for chunk in response.iter_content(64 * 1024):
                    if cancel.is_set(): raise Cancelled('Cancelled')
                    if not chunk: continue
                    f.write(chunk); digest.update(chunk); received += len(chunk); progress(received, total)
        if expected_size and received != expected_size: raise ValueError('Download size mismatch')
        if sha256 and digest.hexdigest() != sha256: raise ValueError('SHA256 mismatch')
        part.replace(target)
        return digest.hexdigest(), received
    finally:
        part.unlink(missing_ok=True)


def install_asr(size, root, progress, cancel):
    repo = ASR_REPOS[size]
    response = requests.get(f'https://huggingface.co/api/models/{repo}?blobs=true', timeout=30)
    response.raise_for_status(); info = response.json(); revision = info['sha']
    dest = Path(root) / f'whisper-{size}'; staging = dest.with_name(dest.name + '.installing'); staging.mkdir(parents=True, exist_ok=True)
    files = [x for x in info['siblings'] if x['rfilename'] in ('model.bin', 'config.json', 'tokenizer.json', 'vocabulary.json', 'vocabulary.txt', 'preprocessor_config.json')]
    record = dict(repo=repo, revision=revision, license=info.get('cardData', {}).get('license'), files=[])
    try:
        for item in files:
            name = item['rfilename']; lfs = item.get('lfs', {}); size_bytes = item.get('size') or lfs.get('size')
            sha, count = download(f'https://huggingface.co/{repo}/resolve/{revision}/{name}', staging / name,
                                  lambda n, t: progress(name, n, t), cancel, size_bytes, lfs.get('sha256'))
            record['files'].append(dict(name=name, sha256=sha, size=count, upstream_sha256=lfs.get('sha256')))
        if not (staging / 'model.bin').exists(): raise ValueError('Model weights missing from repository')
        (staging / 'provenance.json').write_text(json.dumps(record, indent=2), 'utf-8')
        if dest.exists(): raise FileExistsError('Delete existing model before reinstalling')
        staging.rename(dest)
    finally:
        if staging.exists(): shutil.rmtree(staging)
    return dest


def install_argos(source, target, package_dir, progress, cancel):
    response = requests.get(ARGOS_INDEX, timeout=30); response.raise_for_status()
    entries = [x for x in response.json() if x['from_code'] == source and x['to_code'] == target]
    if not entries: raise ValueError('Translation direction absent in official index')
    item = entries[-1]; package_dir = Path(package_dir); package_dir.mkdir(parents=True, exist_ok=True)
    file = package_dir / f'{source}-{target}.argosmodel'
    sha, count = download(item['links'][0], file, lambda n,t: progress(file.name,n,t), cancel,
                          sha256=item.get('sha256'))
    # Verify ZIP structure and CRC before calling the package installer.
    with zipfile.ZipFile(file) as archive:
        if archive.testzip(): raise ValueError('Argos archive CRC failure')
        for name in archive.namelist():
            if Path(name).is_absolute() or '..' in Path(name).parts: raise ValueError('Unsafe archive member')
    from .config import data_dir
    import os
    os.environ['ARGOS_PACKAGES_DIR'] = str(data_dir() / 'argos')
    os.environ.setdefault('XDG_DATA_HOME', str(data_dir() / 'vendor' / 'data'))
    os.environ.setdefault('XDG_CONFIG_HOME', str(data_dir() / 'vendor' / 'config'))
    os.environ.setdefault('XDG_CACHE_HOME', str(data_dir() / 'vendor' / 'cache'))
    from argostranslate.package import install_from_path
    if cancel.is_set(): raise Cancelled('Cancelled')
    install_from_path(file)
    (file.with_suffix('.json')).write_text(json.dumps(dict(index=item, sha256=sha, size=count, upstream_checksum_available=bool(item.get('sha256'))), indent=2), 'utf-8')
    return file
