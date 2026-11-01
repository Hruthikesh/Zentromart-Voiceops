"""Section chunks, multilingual embeddings and a small cosine vector index."""
import csv
import hashlib
import json
import re
from pathlib import Path

PRIORITY = {'policy': 0, 'agent_guide': 1, 'help': 2, 'faq': 3, 'marketing': 4, 'meta': 0}


def load_chunks(root):
    chunks = []
    for file in sorted((Path(root) / 'kb').glob('*.md')):
        text = file.read_text(encoding='utf-8')
        header = text.split('---', 2)[1] if text.startswith('---') else ''
        meta = dict(re.findall(r'^([\w_]+):\s*(.*)$', header, re.M))
        sections = list(re.finditer(r'^## \[([^\]]+)\].*$', text, re.M))
        for i, match in enumerate(sections):
            body = text[match.start(): sections[i + 1].start() if i + 1 < len(sections) else len(text)]
            chunks.append({'id': match[1], 'file': file.name, 'text': body.strip(), **meta})
    with (Path(root) / 'data/products.csv').open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            chunks.append({'id': 'products.csv:' + row['sku'], 'file': 'products.csv',
                           'text': json.dumps(row, ensure_ascii=False), 'doc_type': 'catalog', 'status': 'current'})
    if not chunks:
        raise ValueError('No knowledge-base chunks found.')
    return chunks


class Retriever:
    def __init__(self, root, model_name, cache='.cache'):
        import numpy as np
        from sentence_transformers import SentenceTransformer
        self.np = np
        self.chunks = load_chunks(root)
        self.model = SentenceTransformer(model_name)
        digest = hashlib.sha256((model_name + json.dumps(self.chunks, sort_keys=True)).encode()).hexdigest()
        folder = Path(cache)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / (digest + '.npy')
        if path.exists():
            self.vectors = np.load(path, allow_pickle=False)
        else:
            self.vectors = self.model.encode([c['text'] for c in self.chunks], normalize_embeddings=True)
            np.save(path, self.vectors)

    def search(self, query, k=8):
        vector = self.model.encode([query], normalize_embeddings=True)[0]
        scores = self.vectors @ vector
        tokens = set(re.findall(r'\w+', query.lower()))
        ranked = []
        for i, c in enumerate(self.chunks):
            words = set(re.findall(r'\w+', c['text'].lower()))
            lexical = len(tokens & words) / max(1, len(tokens))
            score = float(scores[i]) + 0.12 * lexical
            if c.get('status') == 'superseded':
                score -= 0.2
            if c['id'].startswith('products.csv:') and c['id'].split(':')[1].lower() in query.lower():
                score += 1
            ranked.append((score, i))
        selected = [dict(self.chunks[i], score=round(s, 4)) for s, i in sorted(ranked, reverse=True)[:k]]
        # If an older policy is retrieved, always give the model its current successor too.
        old_ids = {c.get('doc_id') for c in selected if c.get('status') == 'superseded'}
        selected_files = {c['file'] for c in selected}
        for c in self.chunks:
            if c.get('status') == 'current' and (c.get('supersedes') in old_ids or
                any((old or '').startswith(c.get('doc_id', '!')) for old in old_ids)):
                if not any(s['file'] == c['file'] and s['id'] == c['id'] for s in selected):
                    selected.append(dict(c, score=None))
        return sorted(selected, key=lambda c: (c.get('status') != 'current', PRIORITY.get(c.get('doc_type'), 2)))
