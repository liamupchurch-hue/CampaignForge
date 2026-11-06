"""Real-world regression for the 6 The Ashen Compass 'handout' warnings."""
import tempfile
import unittest
from pathlib import Path
from campaign_data import CATEGORIES, new_campaign, save_campaign, load_campaign
from campaign_import import (
    normalize_ai_fragment, combine_ai_passages, apply_proposal, organization_instructions,
    extract_document, build_local_proposal,
)
from pdf_book import export_book
from pypdf import PdfReader

CAPTIONS = [
    "Hollowford", "Stone Market", "Highfield", "Southgate with gates to Northfield",
    "Map with Insignias", "Pirates cove in Blackreef isle",
]

class HandoutRegressionTests(unittest.TestCase):
    def test_exact_six_reported_handouts_remain_handouts(self):
        payload = {'values':{}, 'entries':[
            {'category':'handout', 'title':name, 'content':f'Illustration: {name}', 'gm_only':False}
            for name in CAPTIONS
        ]}
        frag, warnings, adjusted = normalize_ai_fragment(payload)
        self.assertEqual(warnings, [])
        self.assertEqual([e['category'] for e in frag['entries']], ['Handout']*6)
        self.assertIn('Handout', CATEGORIES)
        self.assertIn('Handout', organization_instructions())
        doc={'name':'sample-campaign.docx','text':'Some manuscript text', 'chars':20, 'warnings':[]}
        proposal=combine_ai_passages(doc, [{'values':{},'entries':[]}, frag])
        included={f'entry:{i}' for i,e in enumerate(proposal['entries']) if e['category']=='Handout'}
        result, stats=apply_proposal(new_campaign('The Ashen Compass'), proposal, included, keep_reference=False)
        self.assertEqual(stats['entries'], 6)
        with tempfile.TemporaryDirectory() as td:
            project=Path(td)/'Midnight.campaign.json'; save_campaign(result,project)
            loaded=load_campaign(project)
            self.assertEqual([e['category'] for e in loaded['entries']],['Handout']*6)
            dest=Path(td)/'book.pdf'; export_book(loaded,dest)
            contents='\n'.join(page.extract_text() or '' for page in PdfReader(str(dest)).pages)
            self.assertIn('Handouts & Visual References', contents)
            self.assertIn('Stone Market', contents)

    def test_handout_variants_accepted(self):
        for category in ('Handout','handouts','player handout','visual reference','map image','illustration','artwork'):
            with self.subTest(category=category):
                frag, warnings, _=normalize_ai_fragment({'values':{}, 'entries':[
                    {'category': category, 'title':'Handout', 'content':'Caption in the source'}
                ]})
                self.assertEqual(frag['entries'][0]['category'], 'Handout')
                self.assertFalse(any('unknown category' in w for w in warnings))


if __name__ == '__main__': unittest.main()
