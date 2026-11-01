"""Use the supplied tools; enforce retry limits outside the language model."""
import csv
import importlib.util
import re
from datetime import date, timedelta
from pathlib import Path

TODAY = date(2026, 10, 20)


def redact(text):
    # Hide standalone verification values, including spaced digits. Preserve 8-digit order IDs.
    return re.sub(r'(?<!\d)(?:\d[ -]?){3,5}\d(?![ -]?\d)', '[verification hidden]', str(text))


class ToolStore:
    def __init__(self, root, ticket_path='runs/tickets.csv'):
        spec = importlib.util.spec_from_file_location('supplied_tools', Path(root) / 'tools/tools.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        path = Path(ticket_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.module._TICKETS = str(path)
        with (Path(root) / 'data/holidays.csv').open(encoding='utf-8', newline='') as f:
            self.holidays = {date.fromisoformat(row['date']) for row in csv.DictReader(f)}

    def add_business_days(self, start, days):
        current = date.fromisoformat(start)
        if not 0 <= days <= 365:
            raise ValueError('Days must be between 0 and 365.')
        while days:
            current += timedelta(days=1)
            if current.weekday() != 6 and current not in self.holidays:
                days -= 1
        return current.isoformat()


class OrderSession:
    def __init__(self, store):
        self.store = store
        self.order_id = None
        self.verified = {}
        self.attempts = {}

    def lookup(self, order_id, proof=None):
        oid = re.sub(r'\D', '', str(order_id))
        if len(oid) != 8:
            return {'error': 'Ask for the eight-digit order ID.'}
        self.order_id = oid
        if oid in self.verified:
            return self.verified[oid]
        if self.attempts.get(oid, 0) >= 2:
            return {'verified': False, 'locked': True, 'message': 'No more attempts. Contact support from the registered phone.'}
        if proof:
            self.attempts[oid] = self.attempts.get(oid, 0) + 1
        result = self.store.module.lookup_order(oid, verification_value=proof)
        if result.get('verified'):
            result.pop('delivery_pincode', None)
            self.verified[oid] = result
        return result
