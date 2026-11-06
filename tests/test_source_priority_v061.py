import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path

from oracle_grounding import (gather_sources, verify_grounded_draft, UnsupportedLore,
    is_attribution_question, history_messages)
from oracle_field import field_request_messages, InvalidFieldRevision
from oracle_providers import consult_local


class SourceFirstTests(unittest.TestCase):
    def setUp(self):
        self.source=('The Ashen Compass is a fantasy adventure beginning in a busy port. '
                     'The players discover a corrupt Guard Captain, Captain Garrick Vale, '
                     'and follow his illegal shipping records to Sable Island. '
                     'Their investigation uncovers a conspiracy spanning the continent. ')*8
        self.data={'title':'The Ashen Compass','system':'Pathfinder 2e',
                   'pitch':'','setting':'Hollowford is a coastal town.',
                   'entries':[{'category':'Lore','title':'AI Notes',
                               'content':'Master Pelius started a dream-plague (NOT REAL CANON).'}],
                   'references':[{'name':'sample-campaign.docx','text':self.source}]}
        self.target={'kind':'overview','key':'pitch','label':'Premise','baseline':'','project_epoch':1}

    def test_manuscript_is_retrieved_without_campaign_lore_as_source(self):
        result=gather_sources(self.data,None,'id','Draft premise from manuscript',self.target,
                              use_archive=False)
        self.assertEqual(result.names,['sample-campaign.docx'])
        self.assertIn('Captain Garrick Vale',result.text)
        self.assertNotIn('Master Pelius',result.text)

    def test_blank_field_refuses_to_invent_without_document(self):
        with self.assertRaises(InvalidFieldRevision):
            field_request_messages(self.data,'Create premise',self.target,
                                   source_context='',source_grounded=True)

    def test_prompt_prioritizes_source_before_derived_lore(self):
        messages=field_request_messages(self.data,'Draft a premise',self.target,
                        source_context=self.source,source_grounded=True)
        self.assertIn('higher authority',messages[0]['content'])
        self.assertIn('Captain Garrick Vale',messages[1]['content'])
        self.assertNotIn('Master Pelius',messages[1]['content'])

    def test_blank_field_needs_actual_verifiable_quote(self):
        good=('{'+'"draft": "A corrupt Guard Captain, Captain Garrick Vale, controls the docks.", '
             '"evidence": ["The players discover a corrupt Guard Captain, Captain Garrick Vale"]}')
        self.assertIn('Captain Garrick Vale',verify_grounded_draft(good,self.source))
        bad=('{'+'"draft": "Master Pelius starts a dream plague", '
             '"evidence": ["The players discover a corrupt Guard Captain, Captain Garrick Vale"]}')
        with self.assertRaisesRegex(UnsupportedLore,'unsupported proper name'):
            verify_grounded_draft(bad,self.source)
        with self.assertRaises(UnsupportedLore):
            verify_grounded_draft('{"draft":"The Veiled Hand rules Hollowford", "evidence":["Invented source"]}',self.source)

    def test_local_draft_retries_when_evidence_missing(self):
        responses=[
            '{"draft":"Master Pelius haunts the town", "evidence":["The players discover a corrupt Guard Captain, Captain Garrick Vale"]}',
            '{"draft":"Captain Garrick Vale is at the center of a smuggling conspiracy.", "evidence":["The players discover a corrupt Guard Captain, Captain Garrick Vale"]}'
        ]
        with patch('oracle_providers.ollama_chat',side_effect=responses) as mock:
            result=consult_local(self.data,'Write a premise',model='gemma3:12b',
              field_target=self.target,source_context=self.source,
              source_text=self.source,source_grounded=True)
        self.assertEqual(mock.call_count,2)
        self.assertIn('Garrick Vale',result)

    def test_followup_question_uses_previous_answer_not_field_edit(self):
        turns=[{'question':'Improve premise','answer':'Master Pelius causes a dream-plague.'}]
        with patch('oracle_providers.ollama_chat',return_value='I invented Master Pelius; he is not supported by the source.') as mock:
            result=consult_local(self.data,'How did you get that from the source document?',
                model='gemma3:12b',field_target=self.target,discussion=True,
                source_context=self.source,source_grounded=True,history=turns)
        messages=mock.call_args.args[0]
        self.assertEqual(messages[-1]['role'],'user')
        self.assertIn('Master Pelius',messages[-2]['content'])
        self.assertIn('source',messages[0]['content'].lower())
        self.assertIn('invented',result)
        self.assertTrue(is_attribution_question('How did you get that from the source document?'))

    def test_archive_document_source_scoping(self):
        from forge_library import Archive
        with tempfile.TemporaryDirectory() as temp:
            archive=Archive(Path(temp)/'arc')
            manuscript=Path(temp)/'notes.txt'
            manuscript.write_text(self.source)
            archive.add(manuscript,scope='campaign',project_id='one')
            data=dict(self.data,references=[])
            refs=gather_sources(data,archive,'one','premise Captain',self.target)
            self.assertIn('notes.txt',refs.names)
            self.assertEqual(gather_sources(data,archive,'two','Captain',self.target).names,[])

if __name__=='__main__': unittest.main()
