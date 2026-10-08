from yuspeak.models import download, Cancelled
import threading
import pytest

def test_cancelled_download(tmp_path, monkeypatch):
    class Response:
        headers={'content-length':'2'}
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def raise_for_status(self):pass
        def iter_content(self,*args):yield b'ok'
    monkeypatch.setattr('yuspeak.models.requests.get', lambda *a,**k:Response())
    c=threading.Event(); c.set()
    with pytest.raises(Cancelled):download('https://fixture/model',tmp_path/'x',lambda *_:None,c)
    assert not (tmp_path/'x').exists() and not (tmp_path/'x.part').exists()

def test_checksum_mismatch(tmp_path,monkeypatch):
    class Response:
        headers={'content-length':'2'}
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def raise_for_status(self):pass
        def iter_content(self,*args):yield b'ok'
    monkeypatch.setattr('yuspeak.models.requests.get',lambda *a,**k:Response())
    with pytest.raises(ValueError,match='SHA256'):download('https://fixture/model',tmp_path/'x',lambda *_:None,threading.Event(),sha256='bad')
    assert not (tmp_path/'x').exists()
