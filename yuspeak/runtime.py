"""Register CUDA DLL paths before importing CTranslate2; handles must stay alive."""
import os
import sys
from pathlib import Path
_handles = []


def setup_dlls():
    if sys.platform != 'win32':
        return
    roots = [Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent)), Path(sys.prefix) / 'Lib' / 'site-packages']
    candidates = []
    for root in roots:
        candidates.extend(root.glob('nvidia/*/bin'))
        candidates.extend(root.glob('nvidia/*/lib'))
        candidates.extend(root.glob('cuda_runtime'))
        candidates.extend(root.glob('ctranslate2'))
    explicit = os.environ.get('YUSPEAK_CUDA_DIRS', '')
    candidates += [Path(x) for x in explicit.split(os.pathsep) if x]
    for p in candidates:
        if p.is_dir():
            _handles.append(os.add_dll_directory(str(p)))
            os.environ['PATH'] = str(p) + os.pathsep + os.environ.get('PATH', '')
