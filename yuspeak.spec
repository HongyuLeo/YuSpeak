# Directory build keeps model/runtime DLL paths inspectable.
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
hiddenimports = collect_submodules('faster_whisper') + ['argostranslate.package', 'argostranslate.tokenizer', 'sentencepiece', 'sacremoses']
datas = [('assets', 'assets')]
a = Analysis(['launcher.py'], pathex=['.'], hiddenimports=hiddenimports, datas=datas, hookspath=['hooks'], excludes=['torch','stanza','spacy','argostranslate.translate','PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets','PySide6.QtPdf'])
# Qt on Windows imports the system ICU shim. A Poppler directory on PATH can
# contribute an incompatible same-named ICU library during dependency scanning.
a.binaries = [entry for entry in a.binaries if entry[0].lower() not in ('icuuc.dll', 'icudt78.dll')]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, exclude_binaries=True, name='YuSpeak', console=False)
coll = COLLECT(exe, a.binaries, a.datas, name='YuSpeak')
