"""Extract portable, read-only reference text; retain no uploaded file bytes."""
from pathlib import Path
import uuid

MAX_BYTES = 15 * 1024 * 1024
MAX_TEXT = 50000


def import_reference(path):
    p = Path(path)
    if p.stat().st_size > MAX_BYTES:
        raise ValueError("Reference must be 15 MB or smaller in this prototype.")
    suffix = p.suffix.lower()
    if suffix in (".txt", ".md"):
        text = p.read_text(encoding="utf-8-sig", errors="replace")
    elif suffix == ".docx":
        from docx import Document
        doc = Document(str(p))
        text = "\n".join(x.text for x in doc.paragraphs)
        for table in doc.tables:
            text += "\n" + "\n".join(" | ".join(cell.text for cell in row.cells) for row in table.rows)
    elif suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(p))
        text = "\n".join(page.extract_text() or "" for page in reader.pages[:150])
        if not text.strip():
            raise ValueError("This PDF does not contain extractable text (scanned PDFs aren't supported yet).")
    else:
        raise ValueError("Supported references: .txt, .md, .docx, and text-based .pdf")
    was_trimmed = len(text) > MAX_TEXT
    return {"id": str(uuid.uuid4()), "name": p.name, "source_path": str(p),
            "text": text[:MAX_TEXT], "truncated": was_trimmed}
