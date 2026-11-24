"""Lexical search with BM25, written from scratch.

BM25 scores a chunk by the words it shares with the query:
  - rare words count more than common ones ("vo2" matters, "the" doesn't)
  - repeating a word helps, but with diminishing returns (k1)
  - long chunks are slightly penalised so they don't win just by size (b)

It finds exact terms like a workout code ("VO2-5x4") that semantic search can
miss, because an embedding captures meaning, not exact spelling.
"""

import math
import re
from collections import Counter

STOPWORDS = {"a", "an", "and", "are", "at", "be", "can", "do", "for", "how", "i", "in", "is",
             "it", "my", "of", "on", "or", "should", "the", "to", "what", "when", "with"}


def tokenize(text: str) -> list:
    # Keep codes like "vo2-5x4" or "z2-long" as one token.
    return [t for t in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower()) if t not in STOPWORDS]


class BM25Index:
    def __init__(self, chunks: list, k1: float = 1.5, b: float = 0.75):
        self.chunks, self.k1, self.b = chunks, k1, b
        self.docs = [Counter(tokenize(c["text"])) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_length = sum(self.lengths) / len(self.lengths)
        doc_freq = Counter(term for d in self.docs for term in d)
        n = len(chunks)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in doc_freq.items()}

    def score(self, query_terms: list, i: int) -> float:
        doc, length, total = self.docs[i], self.lengths[i], 0.0
        for term in query_terms:
            tf = doc.get(term, 0)
            if tf:
                norm = tf + self.k1 * (1 - self.b + self.b * length / self.avg_length)
                total += self.idf[term] * tf * (self.k1 + 1) / norm
        return total

    def search(self, query: str, k: int = 3) -> list:
        """Returns [(chunk, score)], best first. Chunks with no shared words are left out."""
        terms = tokenize(query)
        scored = [(self.chunks[i], self.score(terms, i)) for i in range(len(self.chunks))]
        scored = [s for s in scored if s[1] > 0]
        return sorted(scored, key=lambda s: s[1], reverse=True)[:k]
