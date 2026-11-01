import csv
import os
import tempfile
import unittest
from pathlib import Path
from src.tools import ToolStore, OrderSession, redact
from src.retrieval import load_chunks
from src.agent import Agent


class FakeLLM:
    def __init__(self, answers):
        self.answers = iter(answers)
    def complete(self, messages):
        return next(self.answers)


class FakeRetrieval:
    def search(self, text):
        return [{'id': 'TEST-1', 'text': 'Test policy', 'file': 'test.md'}]


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(os.environ['DATASET_DIR'])
        cls.temp = tempfile.TemporaryDirectory()
        cls.store = ToolStore(cls.root, Path(cls.temp.name) / 'tickets.csv')
        with (cls.root / 'data/orders.csv').open(encoding='utf-8', newline='') as f:
            cls.order = next(csv.DictReader(f))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_lookup_hides_order_until_verified(self):
        s = OrderSession(self.store)
        result = s.lookup(self.order['order_id'])
        self.assertTrue(result['verification_required'])
        self.assertNotIn('status', result)

    def test_valid_verification_hides_pincode(self):
        s = OrderSession(self.store)
        result = s.lookup(self.order['order_id'], self.order['delivery_pincode'])
        self.assertTrue(result['verified'])
        self.assertNotIn('delivery_pincode', result)

    def test_two_failures_lock_even_correct_third_attempt(self):
        s = OrderSession(self.store)
        s.lookup(self.order['order_id'], '000000')
        s.lookup(self.order['order_id'], '000000')
        self.assertTrue(s.lookup(self.order['order_id'], self.order['delivery_pincode'])['locked'])

    def test_sessions_do_not_share_verification(self):
        a, b = OrderSession(self.store), OrderSession(self.store)
        a.lookup(self.order['order_id'], self.order['delivery_pincode'])
        self.assertNotIn('status', b.lookup(self.order['order_id']))

    def test_business_days_skip_sunday_and_holiday(self):
        self.assertEqual(self.store.add_business_days('2026-10-17', 1), '2026-10-20')
        self.assertEqual(self.store.add_business_days('2026-10-16', 1), '2026-10-17')

    def test_chunks_keep_current_and_historical_metadata(self):
        chunks = load_chunks(self.root)
        self.assertTrue(any(c['id'] == 'RET-2' and c['status'] == 'current' for c in chunks))
        self.assertTrue(any(c.get('status') == 'superseded' for c in chunks))
        self.assertEqual(sum(c['id'].startswith('products.csv:') for c in chunks), 70)

    def test_redaction(self):
        self.assertNotIn('4533', redact('My code is 4533'))
        self.assertNotIn('500001', redact('pincode 500001'))
        self.assertIn('89782837', redact('order 89782837'))

    def test_ticket_actually_written(self):
        result = self.store.module.create_ticket('Customer requests a review of a synthetic test issue.')
        self.assertTrue(result['created'])
        self.assertIn(result['ticket_id'], Path(self.store.module._TICKETS).read_text())

    def test_unknown_citation_filtered_and_ai_disclosed(self):
        agent = Agent(FakeLLM([{'action': 'reply', 'reply': 'Please give the order ID.',
                               'decision': 'clarify', 'sources': ['INVENTED']}]), FakeRetrieval(), self.store)
        result = agent.respond('Where is my order?')
        self.assertIn('AI assistant', result['reply'])
        self.assertEqual(result['sources'], [])

    def test_empty_audio_text_recovery(self):
        agent = Agent(FakeLLM([]), FakeRetrieval(), self.store)
        self.assertIn('say it again', agent.respond('')['reply'])


if __name__ == '__main__':
    unittest.main()
