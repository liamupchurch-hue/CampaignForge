import tempfile
import unittest
from pathlib import Path

from campaign_data import new_campaign, sample_campaign, new_entry, new_map, save_campaign, load_campaign
from map_tools import export_map
from pdf_book import export_book
from ai_assistant import make_context
from reference_import import import_reference

class CampaignTests(unittest.TestCase):
    def test_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"story.campaign.json"
            a = sample_campaign()
            save_campaign(a, p)
            self.assertEqual(load_campaign(p), a)

    def test_map_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "map.png"
            export_map(new_map("Test", 8, 6), path)
            from PIL import Image
            with Image.open(path) as img:
                self.assertEqual(img.size, (512, 384))

    def test_pdf_has_text(self):
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "campaign.pdf"
            export_book(sample_campaign(), path)
            pdf = PdfReader(str(path))
            body = "\n".join(p.extract_text() or "" for p in pdf.pages)
            self.assertIn("The Ashen Compass", body)
            self.assertIn("The Drowned Archive", body)
            self.assertIn("Map Appendix", body)
            self.assertGreaterEqual(len(pdf.pages), 3)

    def test_player_export_hides_secrets(self):
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "players.pdf"
            export_book(sample_campaign(), path, include_gm=False)
            body = "\n".join(p.extract_text() or "" for p in PdfReader(str(path)).pages)
            self.assertNotIn("The Keeper's Bargain", body)

    def test_import_reference_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "outline.md"
            path.write_text("# A pirate's clue", encoding="utf8")
            r = import_reference(path)
            self.assertIn("pirate", r["text"])

    def test_reference_opt_in(self):
        campaign = new_campaign()
        campaign["references"].append({"name":"secret.txt", "text":"SECRET-TEST-TOKEN"})
        self.assertNotIn("SECRET-TEST-TOKEN", make_context(campaign, False))
        self.assertIn("SECRET-TEST-TOKEN", make_context(campaign, True))

if __name__ == "__main__":
    unittest.main()
