"""Professional printable book export with cover, contents, and map appendix."""
from html import escape
from pathlib import Path
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
    Image, KeepTogether,
)
from reportlab.platypus.tableofcontents import TableOfContents

from map_tools import render_map

INK = colors.HexColor("#344636")
GOLD = colors.HexColor("#9C7440")
MUTED = colors.HexColor("#75634A")


def fonts():
    # Use fonts that are already on the user's computer. Never distribute font files.
    candidates = [
        ("C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/georgiab.ttf"),
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    for regular, bold in candidates:
        if Path(regular).exists() and Path(bold).exists():
            try:
                pdfmetrics.registerFont(TTFont("ForgeBody", regular))
                pdfmetrics.registerFont(TTFont("ForgeBold", bold))
                return "ForgeBody", "ForgeBold"
            except Exception:
                continue
    return "Times-Roman", "Times-Bold"


class BookDoc(BaseDocTemplate):
    def __init__(self, file_name, title, **kwargs):
        super().__init__(file_name, pagesize=letter, leftMargin=0.85 * inch,
                         rightMargin=0.85 * inch, topMargin=0.85 * inch,
                         bottomMargin=0.72 * inch, title=title, **kwargs)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="book", frames=[frame], onPage=self.decorate))
        self.heading_index = 0

    def decorate(self, canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        canvas.setStrokeColor(GOLD)
        canvas.line(self.leftMargin, letter[1] - 0.63 * inch,
                    letter[0] - self.rightMargin, letter[1] - 0.63 * inch)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(self.leftMargin, 0.43 * inch, self.title[:76])
        canvas.drawRightString(letter[0] - self.rightMargin, 0.43 * inch, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and getattr(flowable, "_toc_level", None) is not None:
            self.notify("TOCEntry", (flowable._toc_level, flowable.getPlainText(), self.page))


def paragraph(text, style):
    text = escape(str(text or "")).replace("\n", "<br/>")
    return Paragraph(text or " ", style)


def export_book(campaign, path, include_gm=True, archive=None):
    body_font, head_font = fonts()
    title_style = ParagraphStyle("CoverTitle", fontName=head_font, fontSize=30,
                                 leading=38, alignment=TA_CENTER, textColor=INK, spaceAfter=16)
    subtitle = ParagraphStyle("CoverSub", fontName=body_font, fontSize=13, leading=19,
                              alignment=TA_CENTER, textColor=MUTED)
    heading = ParagraphStyle("ForgeHead", fontName=head_font, fontSize=18, leading=23,
                             textColor=INK, spaceBefore=22, spaceAfter=12, keepWithNext=True)
    subhead = ParagraphStyle("ForgeSub", fontName=head_font, fontSize=13, leading=17,
                             textColor=GOLD, spaceBefore=14, spaceAfter=7, keepWithNext=True)
    body = ParagraphStyle("ForgeBody", fontName=body_font, fontSize=10, leading=15,
                          textColor=INK, spaceAfter=8)
    small = ParagraphStyle("ForgeSmall", fontName=body_font, fontSize=8, leading=12,
                           textColor=MUTED, spaceAfter=7)
    contents_style = ParagraphStyle("Contents", fontName=body_font, fontSize=10,
                                    leading=14, leftIndent=10, spaceBefore=4)
    title = campaign.get("title", "Untitled Campaign")
    doc = BookDoc(str(path), title)
    story = []

    # Cover page
    story += [Spacer(1, 1.7 * inch), paragraph("CAMPAIGN FORGE", small),
              Spacer(1, 0.25 * inch), paragraph(title, title_style),
              paragraph(campaign.get("system", "System-neutral"), subtitle),
              paragraph('  |  '.join(x for x in (
                  ('Levels '+str(campaign.get('levels','')).strip()) if str(campaign.get('levels','')).strip() else '',
                  str(campaign.get('tone','')).strip()) if x), subtitle),
              Spacer(1, 0.7 * inch), paragraph(campaign.get("pitch", ""), subtitle),
              Spacer(1, 1.15 * inch), paragraph("Created by " + (campaign.get("author") or "The Dungeon Master"), subtitle),
              PageBreak()]

    story.append(paragraph("Contents", heading))
    toc = TableOfContents()
    toc.levelStyles = [contents_style,
                       ParagraphStyle("ContentsDetail", parent=contents_style, leftIndent=26,
                                      fontSize=9, textColor=MUTED)]
    story.append(toc)
    story.append(PageBreak())

    def add_heading(name, level=0):
        obj = paragraph(name, heading if level == 0 else subhead)
        obj._toc_level = level
        story.append(obj)

    if not campaign.get('book_outline'):
        add_heading("Campaign Overview")
        for label, key in (("Premise", "pitch"), ("Setting", "setting"), ("Story Arc", "story_arc")):
            if campaign.get(key, "").strip():
                add_heading(label, 1)
                for p in campaign[key].split("\n\n"):
                    story.append(paragraph(p, body))

    if campaign.get('book_outline'):
        from forge_publish import add_architect_content
        add_architect_content(campaign, story, add_heading, paragraph, body, small,
                              include_gm=include_gm, archive=archive)
    else:
        titles = {"Chapter": "Chapters & Story Arcs", "Quest": "Quests & Adventures",
                  "NPC": "Nonplayer Characters", "Location": "Locations & Geography",
                  "Encounter": "Encounters", "Faction": "Factions", "Item": "Items & Treasures",
                  "Lore": "World Lore", "Secret": "DM Secrets", "Session Notes": "Session Notes",
                  "Handout": "Handouts & Visual References"}
        for category, display_name in titles.items():
            entries = [x for x in campaign.get("entries", [])
                       if x.get("category") == category and (include_gm or not x.get("gm_only"))]
            if not entries:
                continue
            add_heading(display_name)
            for e in entries:
                add_heading(e.get("title", "Untitled"), 1)
                if e.get("gm_only"):
                    story.append(paragraph("DM ONLY — NOT FOR PLAYERS", small))
                for p in (e.get("content") or "").split("\n\n"):
                    story.append(paragraph(p, body))

        maps = campaign.get("maps", [])
        if maps:
            add_heading("Map Appendix")
            for m in maps:
                add_heading(m.get("title", "Map"), 1)
                img = render_map(m, size=40)
                mem = BytesIO()
                img.save(mem, format="PNG")
                mem.seek(0)
                max_w, max_h = 6.75 * inch, 6.4 * inch
                scale = min(max_w / img.width, max_h / img.height, 1.5)
                story.append(Image(mem, width=img.width * scale,
                                   height=img.height * scale))
                story.append(Spacer(1, 10))

    refs = campaign.get("references", [])
    if refs:
        add_heading("Reference Materials")
        story.append(paragraph("Reference names are listed for the DM; their original text is not reproduced.", small))
        for r in refs:
            story.append(paragraph(r.get("name", "Untitled Reference"), body))

    # Contents requires a multi-pass build to resolve correct page numbers.
    doc.multiBuild(story, maxPasses=4)
    return path
