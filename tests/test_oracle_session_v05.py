import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from oracle_session import clean_markdown, apply_suggestion, transcript_text, load_preferences, save_preferences

class OracleSessionTests(unittest.TestCase):
    def test_clean_markdown(self):
        raw = '## Nightfall\n\n**Captain Rowan** has *doubts*.\n\n- Ask the innkeeper\n* Question the guards\n\n[More](https://example.org)'
        cleaned=clean_markdown(raw)
        self.assertIn('Nightfall', cleaned)
        self.assertIn('Captain Rowan has doubts.', cleaned)
        self.assertIn('• Ask the innkeeper', cleaned)
        self.assertIn('• Question the guards', cleaned)
        self.assertNotIn('##', cleaned)
        self.assertNotIn('**', cleaned)
        self.assertIn('https://example.org', cleaned)

    def test_apply_append_replace(self):
        self.assertEqual(apply_suggestion('My premise.', '**Their** suggestion.', 'append'),
                         'My premise.\n\nTheir suggestion.')
        self.assertEqual(apply_suggestion('Original', '## Better\nNew lore', 'replace'), 'Better\nNew lore')
        with self.assertRaises(ValueError):
            apply_suggestion('Old', 'new', 'silently_merge')

    def test_transcript_is_clean_and_preserves_turns(self):
        t=[{'question':'Explain the clue', 'answer':'## Clue\n**Secret** passage',
            'mode':'local', 'target_label':'Premise'},
           {'question':'Improve it', 'answer':'* Clue one\n* Clue two', 'mode':'local'}]
        result=transcript_text(t)
        self.assertIn('Inquiry 1',result)
        self.assertIn('Inquiry 2',result)
        self.assertIn('Secret passage',result)
        self.assertNotIn('## Clue',result)
        self.assertNotIn('* Clue',result)

    def test_preferences_are_not_campaign_data(self):
        with tempfile.TemporaryDirectory() as t, patch.dict(os.environ, {'LOCALAPPDATA':t}):
            save_preferences({'hide_local_notice':True})
            prefs=load_preferences()
            self.assertTrue(prefs['hide_local_notice'])
            self.assertFalse(prefs['hide_cloud_notice'])
            self.assertTrue((Path(t)/'CampaignForge'/'settings.json').exists())

if __name__=='__main__': unittest.main()
