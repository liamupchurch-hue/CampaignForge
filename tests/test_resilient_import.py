"""Regression tests for Hollowford's passage-5 malformed AI reply."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from campaign_import import parse_ai_fragment, normalize_ai_fragment, apply_proposal
from campaign_data import new_campaign
from oracle_providers import organize_local


class RecoveryTests(unittest.TestCase):
    def test_fenced_json_and_alias_normalization(self):
        blob = '```json\n' + json.dumps({"values":{"title":"The Ashen Compass"},
            "entries":[{"category":"NPCs","title":"Captain Rowan","description":"He disappears."}]}) + '\n```'
        proposal, warnings, adjusted = normalize_ai_fragment(parse_ai_fragment(blob))
        self.assertEqual(proposal['values']['title']['value'], 'The Ashen Compass')
        self.assertEqual(proposal['entries'][0]['category'], 'NPC')
        self.assertTrue(adjusted)

    def test_invalid_final_passage_retains_earlier_and_creates_needs_review(self):
        contents = 'C' * 9700 * 4 + 'FINAL_PASSAGE_MATERIAL' * 100
        doc = {"name":"sample-campaign.docx", "text":contents,
               "chars":len(contents), "warnings":[]}
        requested = []
        def fake_response(messages, **kw):
            prompt = messages[-1]['content']
            passage_id = int(prompt.split('Passage ')[1].split(' of ')[0])
            requested.append(passage_id)
            if passage_id == 5:
                return '{"values":{}, "entries":[{"category": "NPC", "title":"Oops", "content": [1, 2]}]}'
            return json.dumps({"values":{}, "entries":[{
                "category":"Chapter","title":f"Chapter {passage_id}","content":f"Page {passage_id}",
            }]})
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'LOCALAPPDATA':folder}), \
             patch('oracle_providers.ollama_chat',side_effect=fake_response):
            result = organize_local(doc)
            self.assertEqual(len(requested), 6)  # first four plus two attempts on passage 5
            self.assertEqual(len([e for e in result['entries'] if e['category']=='Chapter']),4)
            failed = [e for e in result['entries'] if e['confidence']=='needs-review']
            self.assertEqual(len(failed),1)
            self.assertIn('FINAL_PASSAGE_MATERIAL', failed[0]['content'])
            self.assertTrue(any('Passage 5' in x for x in result['warnings']))
            logs = list(Path(folder).rglob('import-passage-5-*.txt'))
            self.assertGreater(len(logs), 0)
            self.assertEqual(result['entries'][-1]['content'], contents)
            included = {'entry:'+str(i) for i,e in enumerate(result['entries'])
                        if e['confidence'] not in ('archive', 'needs-review')}
            campaign, stats = apply_proposal(new_campaign(),result,included,keep_reference=True)
            self.assertEqual(stats['entries'], 4)
            self.assertEqual(len(campaign['references']),1)

    def test_broken_first_response_retry_can_succeed(self):
        doc = {"name":"small.docx", "text":"Chapter 1: The Gate\nA gate stands open.", "warnings":[]}
        calls=[]
        def fake(messages, **kw):
            calls.append(True)
            if len(calls)==1:
                return '{"entries":"bad", "values":{}}'
            return json.dumps({'values':{},'entries':[{"category":"Chapter","title":"The Gate","content":"A gate stands open."}]})
        with patch('oracle_providers.ollama_chat',side_effect=fake):
            result=organize_local(doc)
        self.assertEqual(len(calls),2)
        self.assertEqual(result['entries'][0]['title'],'The Gate')
        self.assertFalse(any('Needs review' in e['title'] for e in result['entries']))


if __name__ == '__main__':
    unittest.main()
