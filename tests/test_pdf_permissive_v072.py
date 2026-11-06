"""Regression checks for the no-PyMuPDF PDF pipeline."""
from pathlib import Path
import sys,io,base64
from PIL import Image
from reportlab.pdfgen import canvas
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from character_sheets import extract_text_file, image_payload, parse_sheet_text
from pdf_book import export_book
from campaign_data import new_campaign

def _make_pdf(path):
    pdf=canvas.Canvas(str(path))
    pdf.drawString(72,720,'AC: 21')
    pdf.drawString(72,700,'HP: 47')
    pdf.showPage()
    pdf.drawString(72,720,'Level: 5')
    pdf.save()

def test_pdf_text_extraction_without_pymupdf(tmp_path):
    pdf=tmp_path/'npc.pdf';_make_pdf(pdf)
    text=extract_text_file(pdf)
    assert parse_sheet_text(text)['AC']=='21'
    assert parse_sheet_text(text)['HP']=='47'
    assert parse_sheet_text(text)['Level']=='5'

def test_pdf_first_page_as_image_without_pymupdf(tmp_path):
    pdf=tmp_path/'npc.pdf';_make_pdf(pdf)
    image_bytes=base64.b64decode(image_payload(pdf))
    img=Image.open(io.BytesIO(image_bytes))
    assert img.width>500 and img.height>500

def test_full_book_rendering_with_pdfium(tmp_path):
    import pypdfium2 as pdfium
    path=tmp_path/'campaign.pdf'
    export_book(new_campaign('The Ashen Compass'),path)
    doc=pdfium.PdfDocument(str(path))
    try:
        assert len(doc)>=1
        page=doc[0]
        try:
            bitmap=page.render(scale=1.0)
            try:
                img=bitmap.to_pil()
                assert img.width>=500 and img.height>=600
            finally: bitmap.close()
        finally: page.close()
    finally: doc.close()

def test_no_pymupdf_imports_or_required_dependency():
    root=Path(__file__).resolve().parents[1]
    for name in ('forge_preview.py','character_sheets.py','requirements.txt'):
        text=(root/name).read_text(encoding='utf-8')
        assert 'import fitz' not in text
        assert 'PyMuPDF>=' not in text
    assert 'pypdfium2' in (root/'requirements.txt').read_text()
