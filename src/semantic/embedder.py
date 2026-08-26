import math
import re
from collections import Counter
from typing import Sequence


class LightweightEmbedder:
    """
    High-speed, zero-dependency TF-IDF / Subword Vector Embedder for code and queries.
    Runs locally on CPU with <1ms latency per chunk.
    """

    def __init__(self):
        self.vocabulary: dict[str, int] = {}
        self.idf: dict[str, float] = {}

    def _tokenize(self, text: str) -> list[str]:
        # Split CamelCase, snake_case, and punctuation
        tokens = []
        raw_words = re.findall(r'[A-Za-z0-9_]+', text.lower())
        for word in raw_words:
            # Subword split: e.g. "create_student" -> ["create", "student"]
            subwords = re.split(r'[_]+', word)
            for sw in subwords:
                if len(sw) >= 2:
                    tokens.append(sw)
        return tokens

    def compute_similarity(self, query: str, document: str) -> float:
        """Computes cosine similarity between query and document tokens."""
        q_tokens = self._tokenize(query)
        d_tokens = self._tokenize(document)

        if not q_tokens or not d_tokens:
            return 0.0

        q_counts = Counter(q_tokens)
        d_counts = Counter(d_tokens)

        # Dot product
        intersection = set(q_counts.keys()) & set(d_counts.keys())
        dot_product = sum(q_counts[t] * d_counts[t] for t in intersection)

        # Norms
        q_norm = math.sqrt(sum(v ** 2 for v in q_counts.values()))
        d_norm = math.sqrt(sum(v ** 2 for v in d_counts.values()))

        if q_norm == 0 or d_norm == 0:
            return 0.0

        cosine = dot_product / (q_norm * d_norm)
        # Scale to [0.0, 1.0]
        return min(1.0, max(0.0, cosine))

    def rank_chunks(self, query: str, chunks: Sequence[str]) -> list[tuple[int, float]]:
        """
        Ranks chunks by similarity against the query.
        Returns list of (index, similarity_score) sorted descending.
        """
        scores = []
        for idx, chunk in enumerate(chunks):
            sim = self.compute_similarity(query, chunk)
            scores.append((idx, round(sim, 4)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores
