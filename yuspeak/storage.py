from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from .config import data_dir
from .domain import Caption


class Store:
    def __init__(self, path: Path | None = None):
        self.path = path or data_dir() / 'history.sqlite3'
        self.db = sqlite3.connect(self.path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('''CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY, started REAL, ended REAL, source TEXT, language TEXT)''')
        self.db.execute('''CREATE TABLE IF NOT EXISTS captions (id INTEGER PRIMARY KEY, session_id INTEGER, start REAL, end REAL, original TEXT, translation TEXT, language TEXT, source TEXT, final INTEGER)''')
        self.db.commit()

    def session(self, started, source, language):
        cur = self.db.execute('INSERT INTO sessions(started,source,language) VALUES (?,?,?)', (started, source, language))
        self.db.commit()
        return cur.lastrowid

    def add(self, sid, caption: Caption):
        self.db.execute('INSERT INTO captions(session_id,start,end,original,translation,language,source,final) VALUES (?,?,?,?,?,?,?,?)',
                        (sid, caption.start, caption.end, caption.original, caption.translation, caption.language, caption.source, int(caption.final)))
        self.db.commit()

    def close(self, sid, ended):
        self.db.execute('UPDATE sessions SET ended=? WHERE id=?', (ended, sid)); self.db.commit()

    def upsert(self, sid, caption):
        row = self.db.execute('SELECT id FROM captions WHERE session_id=? AND start=? AND end=?', (sid, caption.start, caption.end)).fetchone()
        if row:
            self.db.execute('UPDATE captions SET original=?,translation=? WHERE id=?', (caption.original, caption.translation, row[0])); self.db.commit()
        else:
            self.add(sid, caption)

    def search(self, term=''):
        return self.db.execute('SELECT id,started,ended,source,language FROM sessions WHERE source LIKE ? ORDER BY started DESC', (f'%{term}%',)).fetchall()

    def captions(self, sid):
        return self.db.execute('SELECT start,end,original,translation,language,source FROM captions WHERE session_id=? ORDER BY start', (sid,)).fetchall()

    def export(self, sid, path, kind):
        rows = self.captions(sid)
        out = Path(path)
        if kind == 'json':
            out.write_text(json.dumps([dict(start=a, end=b, original=c, translation=d, language=e, source=f) for a,b,c,d,e,f in rows], ensure_ascii=False, indent=2), 'utf-8')
        elif kind == 'txt':
            out.write_text('\n\n'.join(f'{c}\n{d}'.strip() for a,b,c,d,e,f in rows), 'utf-8')
        else:
            def stamp(seconds):
                milliseconds=round(max(0,seconds)*1000)
                h,r=divmod(milliseconds,3600000); m,r=divmod(r,60000); s,ms=divmod(r,1000)
                return f'{h:02}:{m:02}:{s:02},{ms:03}'
            sep = ',' if kind == 'srt' else '.'
            blocks = []
            for i,(a,b,c,d,e,f) in enumerate(rows, 1):
                line = f'{c}\n{d}'.strip()
                blocks.append(f'{i}\n{stamp(a).replace(",", sep)} --> {stamp(b).replace(",", sep)}\n{line}')
            out.write_text(('WEBVTT\n\n' if kind == 'vtt' else '') + '\n\n'.join(blocks) + '\n', 'utf-8')

    def close_db(self): self.db.close()
