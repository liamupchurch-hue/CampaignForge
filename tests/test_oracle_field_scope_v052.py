import unittest
from unittest.mock import patch
from types import SimpleNamespace
import sys
from oracle_field import (DEFAULT_FIELD_REQUEST, InvalidFieldRevision,
                          clean_field_revision, field_request_messages, validate_field_scope)
from oracle_providers import consult_local
from ai_assistant import consult_ai


class FieldEditingTests(unittest.TestCase):
    def setUp(self):
        self.premise = ('A corrupt guard captain uses Hollowford’s port to finance a conspiracy. '
                        'The party follows the money, unaware that ancient magic lies beneath the city.')
        self.data = dict(title='The Ashen Compass', system='Pathfinder 2e',
                         tone='Mystery', setting='A coastal city divided by wealth.',
                         story_arc='BIG STORY ARC: The entire hidden history of the Order and three Houses.',
                         entries=[{'title':'Captain Rowan', 'category':'NPC',
                                   'content':'ENTIRE NPC BIOGRAPHY: secret information and plot twists.'}])
        self.target = dict(kind='overview', key='pitch', label='Premise / elevator pitch',
                           baseline=self.premise, project_epoch=1)

    def test_prompt_only_marks_selected_field_for_revision(self):
        messages = field_request_messages(self.data, DEFAULT_FIELD_REQUEST, self.target)
        prompt = messages[1]['content']
        self.assertIn(self.premise, prompt)
        self.assertIn('ONLY TEXT YOU MAY EDIT', prompt)
        self.assertIn('background only', prompt)
        self.assertNotIn('BIG STORY ARC', prompt)
        self.assertNotIn('ENTIRE NPC BIOGRAPHY', prompt)
        self.assertIn('ONLY the complete replacement for this selected field', prompt)
        self.assertIn('Rewrite ONLY that field', messages[0]['content'])

    def test_leaked_prompt_metadata_removed_when_revision_delimited(self):
        raw = ('FIELD: Lore: Public History\nOriginal Text:\n' + self.premise +
               '\n\nNEW VERSION:\nThe harbor keeps its secrets beneath cold cobblestones.')
        self.assertEqual(clean_field_revision(raw), 'The harbor keeps its secrets beneath cold cobblestones.')
        self.assertEqual(clean_field_revision('FIELD: Premise\nRevised Version:\n## Into the Night\n\n**Captain Rowan** has fallen.'),
                         'Into the Night\n\nCaptain Rowan has fallen.')

    def test_rejects_unseparated_echo_of_original(self):
        raw = 'FIELD: Lore: Public History\nORIGINAL TEXT:\n'+self.premise
        with self.assertRaises(InvalidFieldRevision):
            clean_field_revision(raw)

    def test_json_wrapped_edits_and_prose_are_supported(self):
        self.assertEqual(clean_field_revision('{"revision": "Hollowford waits for midnight."}'),
                         'Hollowford waits for midnight.')
        self.assertEqual(clean_field_revision('The captain watches the docks.'),
                         'The captain watches the docks.')

    def test_overly_broad_answer_rejected_unless_expansion_requested(self):
        huge = 'Much more campaign information and unrelated plotting. ' * 80
        with self.assertRaises(InvalidFieldRevision):
            validate_field_scope(huge, self.target, DEFAULT_FIELD_REQUEST)
        self.assertEqual(validate_field_scope(huge, self.target, 'Expand with much more detail'), huge)

    def test_local_provider_only_sends_field_and_retries_metadata(self):
        with patch('oracle_providers.ollama_chat', side_effect=[
              'FIELD: Premise\nOriginal Text:\n'+self.premise,
              'The captain controls Hollowford’s docks, but the party finds evidence of an older plot.']) as mock:
            revised = consult_local(self.data, DEFAULT_FIELD_REQUEST, model='gemma3:12b', field_target=self.target)
        self.assertTrue(revised.startswith('The captain controls'))
        self.assertEqual(mock.call_count, 2)
        messages = mock.call_args.args[0]
        self.assertNotIn('BIG STORY ARC', messages[1]['content'])

    def test_general_consultation_still_uses_full_context(self):
        with patch('oracle_providers.ollama_chat', return_value='General campaign advice.') as mock:
            consult_local(self.data, 'Suggest a new scene', model='gemma3:4b')
        self.assertIn('BIG STORY ARC', mock.call_args.args[0][1]['content'])

    def test_cloud_provider_field_mode(self):
        calls = []
        class FakeResponses:
            def create(self, **kwargs):
                calls.append(kwargs)
                return SimpleNamespace(output_text='Revised Version:\nHollowford is not what it seems.')
        fake = SimpleNamespace(OpenAI=lambda **kwargs: SimpleNamespace(responses=FakeResponses()))
        with patch.dict(sys.modules, {'openai':fake}):
            result = consult_ai(self.data, DEFAULT_FIELD_REQUEST, 'test-key', field_target=self.target)
        self.assertEqual(result,'Hollowford is not what it seems.')
        self.assertNotIn('BIG STORY ARC', calls[0]['input'])
        self.assertIn('Rewrite ONLY that field', calls[0]['instructions'])


if __name__ == '__main__': unittest.main()
