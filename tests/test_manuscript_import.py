"""Round trip proofs for importing authored manuscripts without overwriting the DM's work."""
import tempfile
import unittest
from pathlib import Path
from docx import Document
from pypdf import PdfReader
from campaign_data import new_campaign, new_entry, save_campaign, load_campaign
from campaign_import import extract_document, build_local_proposal, apply_proposal
from pdf_book import export_book

class ManuscriptTests(unittest.TestCase):
    def create_docx(self, filename):
        doc = Document()
        doc.add_paragraph('The Ashen Compass', style='Title')
        doc.add_paragraph('Author: The Dungeon Master')
        doc.add_paragraph('Tone: Gothic mystery')
        doc.add_heading('Chapter 1: The Bells of Hollowford', level=1)
        doc.add_paragraph('At midnight the bells ring, although the cathedral has no bell tower.')
        doc.add_heading('NPC: Sister Elowen', level=2)
        doc.add_paragraph('She knows the name of the vanished prince but will not speak it.')
        doc.add_heading('Secret: The Empty Throne', level=2)
        doc.add_paragraph('The prince is alive beneath the city.')
        doc.save(str(filename))

    def test_auto_passage_boundaries_preserve_every_character(self):
        from campaign_import import split_manuscript_for_ai
        source = "Chapter 1: Hollowford\n\n" + ("Secret characters inhabit the city.\n" * 2700)
        chunks = split_manuscript_for_ai(source)
        self.assertGreater(len(chunks), 4)
        self.assertTrue(all(1 <= len(chunk) <= 10000 for chunk in chunks))
        self.assertEqual("".join(chunks), source)
        self.assertEqual(split_manuscript_for_ai(""), [])

    def test_multi_passage_merge_preserves_split_chapter_and_only_one_archive(self):
        from campaign_import import combine_ai_passages
        content = "Hollowford " * 5000
        doc = {"name":"Hollowford.docx", "text":content, "chars":len(content), "warnings":[]}
        fragments = [
            {"values":{"title":{"value":"The Ashen Compass"}},
             "entries":[{"category":"Chapter","title":"Chapter 1 — Welcome to Hollowford","content":"First half","gm_only":False}]},
            {"values":{},
             "entries":[{"category":"Chapter","title":"Chapter 1 — Welcome to Hollowford","content":"Second half","gm_only":False}]},
        ]
        proposed=combine_ai_passages(doc, fragments)
        chapter=next(e for e in proposed["entries"] if e["category"]=="Chapter")
        self.assertIn("First half", chapter["content"])
        self.assertIn("Second half", chapter["content"])
        self.assertEqual(proposed["entries"][-1]["content"], content)
        self.assertEqual(len(proposed["entries"]), 2)
        self.assertEqual(proposed["values"]["title"]["value"], "The Ashen Compass")

    def test_docx_recovers_sections_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Hollowford.docx'
            self.create_docx(path)
            proposal = build_local_proposal(extract_document(path))
            self.assertEqual(proposal['values']['title']['value'], 'The Ashen Compass')
            self.assertEqual(proposal['values']['tone']['value'], 'Gothic mystery')
            self.assertTrue(any(x['category']=='NPC' and 'Elowen' in x['title'] for x in proposal['entries']))
            self.assertTrue(any(x['gm_only'] and 'prince is alive' in x['content'] for x in proposal['entries']))
            self.assertTrue(any('bells ring' in x['content'] for x in proposal['entries']))

    def test_existing_campaign_can_only_be_filled_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Hollowford.docx'; self.create_docx(path)
            proposal = build_local_proposal(extract_document(path))
            campaign = new_campaign('My Sacred Title')
            campaign['tone'] = 'Hopeful story'
            campaign['entries'] = [new_entry('NPC','NPC: Sister Elowen','My version is different.')]
            out, stats = apply_proposal(campaign, proposal)
            self.assertEqual(out['title'], 'My Sacred Title')
            self.assertEqual(out['tone'], 'Hopeful story')
            self.assertEqual(out['author'], 'The Dungeon Master')
            self.assertEqual(next(e for e in out['entries'] if e['category']=='NPC')['content'], 'My version is different.')
            self.assertGreater(stats['entries'], 0)
            self.assertTrue(stats['skipped_duplicate_entries'])
            self.assertEqual(campaign['entries'][0]['content'], 'My version is different.')

    def test_selected_fields_and_entries_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Hollowford.docx'; self.create_docx(path)
            proposal = build_local_proposal(extract_document(path))
            out, stats = apply_proposal(new_campaign(),proposal,selections={'field:title','entry:0'},keep_reference=False)
            self.assertEqual(stats['fields'],1)
            self.assertEqual(stats['entries'],1)
            self.assertEqual(len(out['references']),0)
            self.assertEqual(out['title'],'The Ashen Compass')
            self.assertEqual(len(out['entries']),1)

    def test_pdf_standalone_book_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            from campaign_data import sample_campaign
            path = Path(tmp)/'story.pdf'
            export_book(sample_campaign(),path)
            proposal = build_local_proposal(extract_document(path))
            self.assertEqual(proposal['values']['title']['value'],'The Ashen Compass')
            self.assertEqual(proposal['values']['setting']['value'],sample_campaign()['setting'])
            self.assertTrue(any(e['category']=='Chapter' and 'Unlit Lighthouse' in e['title'] for e in proposal['entries']))
            self.assertTrue(any(e['category']=='Encounter' and 'Drowned Archive' in e['title'] for e in proposal['entries']))
            self.assertTrue(any(e['category']=='Secret' and 'Keeper' in e['title'] for e in proposal['entries']))
            out,_=apply_proposal(new_campaign(),proposal)
            project=Path(tmp)/'saved.campaign.json'
            save_campaign(out,project)
            self.assertEqual(load_campaign(project),out)
            exported=Path(tmp)/'recovered.pdf'
            export_book(out,exported)
            text='\n'.join(page.extract_text() or '' for page in PdfReader(str(exported)).pages)
            self.assertIn('The Ashen Compass',text)
            self.assertIn('The Drowned Archive',text)
            self.assertIn('The Keeper',text)

    def test_unreadable_scanned_pdf_is_rejected(self):
        from reportlab.pdfgen.canvas import Canvas
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'empty.pdf'; c=Canvas(str(f)); c.showPage(); c.save()
            with self.assertRaisesRegex(ValueError,'No readable text'):
                extract_document(f)

if __name__=='__main__': unittest.main()
