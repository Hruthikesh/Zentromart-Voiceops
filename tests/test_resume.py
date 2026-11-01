import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from evaluate import evaluate_mode, restore_legacy
from src.agent import Agent, SYSTEM
from src.llm import LLM, DailyQuotaExceeded
from src.tools import ToolStore


class ScriptedLLM:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def complete(self, messages):
        self.calls += 1
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result


class Retrieval:
    def search(self, query):
        return [{'id': 'TEST', 'file': 'test.md', 'text': 'A test policy.'}]


def reply(text='A test answer.'):
    return {'action': 'reply', 'reply': text, 'decision': 'answer', 'sources': ['TEST']}


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.store = ToolStore(Path(os.environ['DATASET_DIR']), self.path / 'tickets.csv')

    def tearDown(self):
        self.temp.cleanup()

    def test_daily_limit_no_retry(self):
        response = Mock(status_code=429)
        response.json.return_value = {'error': {'message': 'Rate limit reached on tokens per day (TPD)'}}
        with patch.dict(os.environ, {'LLM_API_KEY': 'unit-test-only'}), patch('src.llm.requests.post', return_value=response) as post:
            with self.assertRaises(DailyQuotaExceeded):
                LLM().complete([])
            self.assertEqual(post.call_count, 1)

    def test_checkpoint_mid_turn_does_not_repeat_ticket(self):
        llm = ScriptedLLM([{'action': 'create_ticket', 'summary': 'Synthetic issue needs human policy review.'}, DailyQuotaExceeded()])
        agent = Agent(llm, Retrieval(), self.store)
        with self.assertRaises(DailyQuotaExceeded):
            agent.respond('Please get a person to help.')
        original = (self.path / 'tickets.csv').read_bytes()
        resumed = Agent(ScriptedLLM([reply('Your support request is recorded.')]), Retrieval(), self.store)
        resumed.restore(agent.snapshot())
        result = resumed.respond('Please get a person to help.')
        self.assertEqual((self.path / 'tickets.csv').read_bytes(), original)
        self.assertEqual(len(result['tool_calls']), 1)
        self.assertIsNone(resumed.pending)

    def test_pending_state_redacts_verification(self):
        agent = Agent(ScriptedLLM([DailyQuotaExceeded()]), Retrieval(), self.store)
        with self.assertRaises(DailyQuotaExceeded):
            agent.respond('My verification is 4533')
        self.assertNotIn('4533', json.dumps(agent.snapshot()))

    def test_stop_resume_append_and_skip_successes(self):
        rows = [{'conversation_id': 'C1', 'turn': str(i), 'customer_message': f'Question {i}',
                 'expected_decision': 'answer'} for i in (1, 2, 3)]
        llm = ScriptedLLM([reply(), DailyQuotaExceeded()])
        out = self.path / 'results'
        result = evaluate_mode('conversations', rows, (llm, Retrieval(), self.store), out)
        self.assertEqual(result['completed'], 1)
        self.assertEqual(llm.calls, 2)
        before = (out / 'conversations.jsonl').read_bytes()
        next_llm = ScriptedLLM([reply(), reply()])
        result = evaluate_mode('conversations', rows, (next_llm, Retrieval(), self.store), out, resume=True)
        self.assertEqual(result['completed'], 3)
        self.assertEqual(next_llm.calls, 2)
        self.assertTrue((out / 'conversations.jsonl').read_bytes().startswith(before))

    def test_existing_results_refuse_overwrite(self):
        out = self.path / 'results'
        out.mkdir()
        saved = out / 'rag.jsonl'
        saved.write_text('preserve me')
        with self.assertRaises(FileExistsError):
            evaluate_mode('rag', [], (None, None, None), out)
        self.assertEqual(saved.read_text(), 'preserve me')

    def test_legacy_restore_verification_and_ticket_no_calls(self):
        agent = Agent(ScriptedLLM([]), Retrieval(), self.store)
        record = {'answer': {'reply': 'Saved reply', 'tool_calls': [
            {'action': 'lookup_order', 'result': {'order_id': '12345678', 'verified': True, 'status': 'shipped'}},
            {'action': 'create_ticket', 'result': {'created': True, 'ticket_id': 'TEST'}}]}}
        restore_legacy(agent, 'Order 12345678', record)
        self.assertIn('12345678', agent.orders.verified)
        self.assertEqual(agent.last_ticket['ticket_id'], 'TEST')
        self.assertEqual(len(agent.history), 2)
        self.assertFalse((self.path / 'tickets.csv').exists())

    def test_plus_wording_prompt(self):
        self.assertIn('"initiated at pickup"', SYSTEM)

    def test_session_state_roundtrip(self):
        agent = Agent(ScriptedLLM([reply()]), Retrieval(), self.store)
        agent.respond('Test question')
        agent.orders.attempts['12345678'] = 2
        restored = Agent(None, None, self.store)
        restored.restore(agent.snapshot())
        self.assertEqual(restored.snapshot(), agent.snapshot())


if __name__ == '__main__':
    unittest.main()
