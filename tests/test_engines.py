from pathlib import Path
import pytest
from yuspeak.engines import ASR,Translator
def test_missing_asr(tmp_path):
    with pytest.raises(FileNotFoundError,match='ASR model missing'):ASR(tmp_path,'cuda')
def test_gpu_load_error_propagates(tmp_path,monkeypatch):
    (tmp_path/'model.bin').write_bytes(b'x')
    def fail(*a,**k):raise RuntimeError('cudnn DLL missing')
    monkeypatch.setattr('faster_whisper.WhisperModel',fail)
    with pytest.raises(RuntimeError,match='cudnn'):ASR(tmp_path,'cuda')
def test_translation_missing_is_not_fake(tmp_path,monkeypatch):
    monkeypatch.setenv('YUSPEAK_DATA_DIR',str(tmp_path)); t=Translator()
    monkeypatch.setattr(t.packages,'get_installed_packages',lambda:[])
    with pytest.raises(FileNotFoundError):t.translate('hello','en')
    with pytest.raises(ValueError):t.translate('bonjour','fr')
