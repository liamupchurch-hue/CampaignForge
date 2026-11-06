import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch
from project_files import title_to_stem, suggest_save_name, last_project_directory, remember_project_directory
from campaign_data import new_campaign, load_campaign

class ProjectNamesTests(unittest.TestCase):
    def test_title_used_in_filename_and_illegal_chars_removed(self):
        self.assertEqual(title_to_stem('The Ashen Compass'), 'The Ashen Compass')
        self.assertEqual(title_to_stem('Midnight: Hollowford / Act 1'), 'Midnight Hollowford Act 1')
        self.assertEqual(title_to_stem('CON'), 'Campaign - CON')
    def test_existing_project_is_never_default_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            self.assertEqual(suggest_save_name('The Ashen Compass',folder), 'The Ashen Compass.campaign.json')
            (folder/'The Ashen Compass.campaign.json').touch()
            self.assertEqual(suggest_save_name('The Ashen Compass',folder),'The Ashen Compass v2.campaign.json')
            (folder/'The Ashen Compass v2.campaign.json').touch()
            self.assertEqual(suggest_save_name('The Ashen Compass',folder),'The Ashen Compass v3.campaign.json')
            self.assertEqual(suggest_save_name('ignored',folder,folder/'Custom Filename.campaign.json'),'Custom Filename v2.campaign.json')
    def test_recent_directory_persists(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.dict('os.environ', {'LOCALAPPDATA':td}):
                remember_project_directory(Path(td)/'Hollowford.campaign.json')
                self.assertEqual(last_project_directory(),Path(td))
                self.assertFalse('Hollowford' in json.loads((Path(td)/'CampaignForge'/'recent-project.json').read_text())['directory'])

if __name__=='__main__': unittest.main()
