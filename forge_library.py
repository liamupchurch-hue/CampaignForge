"""Local, opt-in document Archive for Campaign Forge.

Files are copied to an app-owned directory; searchable excerpts are stored in a
local SQLite database.  No web access or background upload happens here.
"""
from __future__ import annotations
from pathlib import Path
import os, sqlite3, shutil, uuid, json, zipfile
from datetime import datetime, timezone

EXTENSIONS = {'.pdf', '.docx', '.txt', '.md', '.png', '.jpg', '.jpeg', '.webp', '.json'}
MAX_BYTES = 75 * 1024 * 1024
MAX_TEXT = 400_000

def archive_home():
    base = Path(os.environ.get('LOCALAPPDATA') or (Path.home() / '.local' / 'share'))
    return base / 'CampaignForge' / 'Archives'


def extract_readable_text(path):
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in ('.txt', '.md', '.json'):
        return p.read_text('utf-8-sig', errors='replace')[:MAX_TEXT], False
    if suffix == '.docx':
        from docx import Document
        d = Document(str(p))
        text = '\n'.join([x.text for x in d.paragraphs] +
                         ['\n'.join(' | '.join(c.text for c in row.cells) for row in t.rows) for t in d.tables])
        return text[:MAX_TEXT], len(text) > MAX_TEXT
    if suffix == '.pdf':
        from pypdf import PdfReader
        reader = PdfReader(str(p))
        pieces = []
        length = 0
        for page in reader.pages[:500]:
            s = (page.extract_text() or '')
            pieces.append(s)
            length += len(s)
            if length >= MAX_TEXT:
                break
        text = '\n'.join(pieces)
        return text[:MAX_TEXT], len(text) > MAX_TEXT or len(reader.pages) > 500
    return '', False


class Archive:
    def __init__(self, root=None):
        self.root = Path(root) if root is not None else archive_home()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / 'files').mkdir(exist_ok=True)
        self.db = self.root / 'index.sqlite3'
        with self._connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, scope TEXT NOT NULL,
                project_id TEXT NOT NULL, category TEXT NOT NULL, source_name TEXT NOT NULL,
                filename TEXT NOT NULL, text_content TEXT NOT NULL,
                truncated INTEGER NOT NULL, size_bytes INTEGER NOT NULL, added_at TEXT NOT NULL)''')

    def _connect(self):
        db = sqlite3.connect(str(self.db), timeout=15)
        db.row_factory = sqlite3.Row
        return db

    def add(self, src, scope='campaign', project_id='', category='Reference'):
        src = Path(src)
        if not src.is_file() or src.suffix.lower() not in EXTENSIONS:
            raise ValueError('Choose a PDF, DOCX, TXT, MD, image (PNG/JPG/WebP) or JSON file.')
        if src.stat().st_size > MAX_BYTES:
            raise ValueError('One file can be at most 75 MB in this release.')
        if scope not in ('shared','campaign'):
            raise ValueError('Archive scope must be Shared or Campaign.')
        if scope == 'campaign' and not project_id:
            raise ValueError('Campaign-scoped documents require a campaign project ID.')
        ident = uuid.uuid4().hex
        filename = ident + src.suffix.lower()
        dest = self.root / 'files' / filename
        try:
            shutil.copy2(src, dest)
            text, truncated = extract_readable_text(dest)
            with self._connect() as db:
                db.execute('''INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                           (ident, src.name, scope, project_id if scope == 'campaign' else '',
                            category, src.name, filename, text, int(truncated),
                            src.stat().st_size, datetime.now(timezone.utc).isoformat()))
        except Exception:
            dest.unlink(missing_ok=True)
            raise
        return ident

    def list(self, project_id=None):
        with self._connect() as db:
            if project_id:
                rows = db.execute('''SELECT id,name,scope,project_id,category,size_bytes,
                    added_at,truncated,LENGTH(text_content) AS text_length FROM documents
                    WHERE scope='shared' OR (scope='campaign' AND project_id=?)
                    ORDER BY added_at DESC''', (project_id,)).fetchall()
            else:
                rows = db.execute('''SELECT id,name,scope,project_id,category,size_bytes,
                    added_at,truncated,LENGTH(text_content) AS text_length FROM documents ORDER BY added_at DESC''').fetchall()
        return [dict(x) for x in rows]

    def get(self, ident, project_id=None):
        with self._connect() as db:
            row = db.execute('SELECT * FROM documents WHERE id=?', (ident,)).fetchone()
        if not row:
            raise KeyError('Document was not found in The Archives.')
        if project_id is not None and row['scope'] == 'campaign' and row['project_id'] != project_id:
            raise PermissionError('Document belongs to another campaign.')
        return dict(row)

    def source_path(self, ident, project_id=None):
        row = self.get(ident, project_id)
        return self.root / 'files' / row['filename']

    def delete(self, ident, project_id=None):
        row = self.get(ident, project_id)
        with self._connect() as db:
            db.execute('DELETE FROM documents WHERE id=?', (ident,))
        self.source_path_from_row(row).unlink(missing_ok=True)

    def source_path_from_row(self, row):
        return self.root / 'files' / Path(row['filename']).name

    def search(self, query, project_id, limit=8):
        """Simple offline keyword matching; excerpts are drawn from selected documents only."""
        tokens = [s.strip('.,:;!?()[]"\'').lower() for s in query.split() if s.strip('.,:;!?()[]"\'')][:20]
        records = []
        for summary in self.list(project_id):
            item = self.get(summary['id'], project_id)
            haystack = item['text_content'].lower()
            title = item['name'].lower()
            matches = [(haystack.find(t), t) for t in tokens if haystack.find(t) >= 0]
            title_hits = [t for t in tokens if t in title]
            # Image files have no indexed text; exact and partial filename searches must still match.
            score = 4 * len(title_hits) + len(matches)
            if not tokens or score:
                start = min((pos for pos, _ in matches), default=0)
                text = item['text_content']
                excerpt = text[max(0, start-180):start+1150].strip()
                records.append({**summary, 'excerpt':excerpt, 'score':score})
        records.sort(key=lambda r:(r['score'],r['added_at']),reverse=True)
        return records[:limit]

    def restore(self, path):
        """Restore a Campaign Forge Archives backup, retaining document IDs.

        File names from a ZIP are never used as destination paths. Limits guard
        against oversized or malicious archives.
        """
        path = Path(path)
        count = 0
        with zipfile.ZipFile(path, 'r') as z:
            if 'archive_manifest.json' not in z.namelist():
                raise ValueError('Not a Campaign Forge Archives backup.')
            manifest = json.loads(z.read('archive_manifest.json'))
            if manifest.get('format') != 'CampaignForgeArchives-1':
                raise ValueError('Unsupported Archives backup format.')
            records=manifest.get('documents',[])
            if len(records)>2000:
                raise ValueError('The backup exceeds 2,000 documents.')
            for record in records:
                if not isinstance(record,dict):continue
                ident=str(record.get('id',''))
                name=str(record.get('filename',''))
                if len(ident)!=32 or any(c not in '0123456789abcdef' for c in ident):continue
                if name != ident+Path(name).suffix.lower() or Path(name).suffix.lower() not in EXTENSIONS:continue
                location='files/'+name
                if location not in z.namelist():continue
                info=z.getinfo(location)
                if info.file_size>MAX_BYTES:continue
                with self._connect() as db:
                    if db.execute('SELECT id FROM documents WHERE id=?',(ident,)).fetchone():continue
                dest=self.root/'files'/name
                try:
                    with z.open(location) as src, dest.open('wb') as dst:
                        copied=0
                        while True:
                            chunk=src.read(1024*1024)
                            if not chunk:break
                            copied+=len(chunk)
                            if copied>MAX_BYTES:raise ValueError('Oversized document in archive.')
                            dst.write(chunk)
                    text,truncated=extract_readable_text(dest)
                    scope=record.get('scope','shared')
                    if scope not in ('campaign','shared'):scope='shared'
                    project_id=str(record.get('project_id','')) if scope=='campaign' else ''
                    if scope=='campaign' and not project_id:raise ValueError('Missing project ID.')
                    with self._connect() as db:
                        db.execute('INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                            (ident,str(record.get('name',name))[:400],scope,project_id,
                             str(record.get('category','Reference'))[:100],
                             str(record.get('source_name',name))[:400],name,text,
                             int(truncated),copied,str(record.get('added_at',''))))
                    count+=1
                except Exception:
                    dest.unlink(missing_ok=True)
                    raise
        return count

    def backup(self, path):
        """Copies only managed Archive contents and a JSON manifest, never absolute paths."""
        docs = self.list()
        path = Path(path)
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            manifest = []
            for item in docs:
                row = self.get(item['id'])
                src = self.source_path_from_row(row)
                if not src.is_file():
                    continue
                z.write(src, 'files/'+row['filename'])
                manifest.append({k:v for k,v in row.items() if k!='text_content'})
            z.writestr('archive_manifest.json',json.dumps({'format':'CampaignForgeArchives-1','documents':manifest},indent=2))
        return path
