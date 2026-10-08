from yuspeak.config import Settings
from yuspeak.hotkeys import parse_hotkey
import pytest

def test_settings_roundtrip(tmp_path,monkeypatch):
    monkeypatch.setenv('YUSPEAK_DATA_DIR',str(tmp_path)); s=Settings(); s.caption.size=34; s.ui_language='en'; s.save(); r=Settings.load(); assert r.caption.size==34 and r.ui_language=='en'
def test_invalid_settings_recovers(tmp_path,monkeypatch):
    monkeypatch.setenv('YUSPEAK_DATA_DIR',str(tmp_path)); (tmp_path/'settings.json').write_text('{'); assert Settings.load().ui_language=='zh'
def test_hotkey_validation():
    assert parse_hotkey('Ctrl+Alt+S')==(0x4003,ord('S'))
    with pytest.raises(ValueError):parse_hotkey('S')
    with pytest.raises(ValueError):parse_hotkey('Foo+S')
