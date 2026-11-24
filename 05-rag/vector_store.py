"""Semantic search with embeddings.

An embedding is a list of numbers that represents the meaning of a text.
Texts with similar meaning get similar vectors, so "what should I eat during
a long ride?" finds the fuelling section even if it shares no exact words.

Claude doesn't make embeddings, so this uses Voyage AI (VOYAGE_API_KEY in
.env or .env.local). Embeddings are cached in .embeddings_cache.json, so each
chunk is only embedded once.
"""

import hashlib
import json
import math
import sys
import warnings
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# macOS's built-in Python uses LibreSSL, which makes urllib3 print a harmless warning.
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

import common.claude  # noqa: E402,F401  (loads the API keys from .env / .env.local)
import voyageai  # noqa: E402

EMBED_MODEL = "voyage-3.5"
CACHE_FILE = Path(__file__).parent / ".embeddings_cache.json"

_client = None


def voyage():
    global _client
    if _client is None:
        _client = voyageai.Client()  # reads VOYAGE_API_KEY
    return _client


def _key(text: str, input_type: str) -> str:
    return hashlib.sha256(f"{EMBED_MODEL}|{input_type}|{text}".encode()).hexdigest()


def embed(texts: list, input_type: str) -> list:
    """input_type is "document" for chunks and "query" for questions:
    Voyage embeds them slightly differently so they match better."""
    cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    missing = [t for t in texts if _key(t, input_type) not in cache]
    if missing:
        result = voyage().embed(missing, model=EMBED_MODEL, input_type=input_type)
        for text, vector in zip(missing, result.embeddings):
            cache[_key(text, input_type)] = vector
        CACHE_FILE.write_text(json.dumps(cache))
    return [cache[_key(t, input_type)] for t in texts]


def cosine(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


class VectorIndex:
    def __init__(self, chunks: list, text_key: str = "text"):
        self.chunks = chunks
        self.vectors = embed([c[text_key] for c in chunks], "document")

    def search(self, query: str, k: int = 3) -> list:
        """Returns [(chunk, similarity)], best first."""
        q = embed([query], "query")[0]
        scored = [(c, cosine(q, v)) for c, v in zip(self.chunks, self.vectors)]
        return sorted(scored, key=lambda s: s[1], reverse=True)[:k]
