from yuspeak.storage import Store
from yuspeak.domain import Caption

def test_export(tmp_path):
    s=Store(tmp_path/'x.db'); sid=s.session(1,'system','en'); s.add(sid, Caption(1,1,2,'Hello','你好','en'))
    for k in ('txt','json','srt','vtt'):
        p=tmp_path/f'x.{k}'; s.export(sid,p,k); assert p.exists() and p.stat().st_size > 0
    s.close_db()
