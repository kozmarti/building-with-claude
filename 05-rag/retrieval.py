"""Steps 2 and 3 of RAG: find the best chunks for a question.

  - hybrid search: run BM25 and vector search, then merge the two rankings
    with reciprocal rank fusion (RRF). Exact terms and meaning both count.
  - reranking: Claude reads the candidates and puts them in order of how well
    they answer the question. Slower, but it understands the question.
  - contextual retrieval: before indexing, Claude writes a short sentence that
    places each chunk within the whole document. A chunk saying "keep a few
    short efforts" means more once it's labelled "part of the pre-race taper".
"""

import hashlib
import json
import sys
from pathlib import Path

from pydantic import BaseModel

sys.path.append(str(Path(__file__).resolve().parents[1]))

from bm25 import BM25Index  # noqa: E402
from common.claude import chat, structured  # noqa: E402
from vector_store import VectorIndex  # noqa: E402

CONTEXT_CACHE = Path(__file__).parent / ".context_cache.json"


# --- Hybrid search ------------------------------------------------------------

def reciprocal_rank_fusion(rankings: list, k: int = 60) -> list:
    """Merge several ranked lists of chunks. A chunk scores 1 / (k + rank) in
    each list it appears in; scores add up. Only the rank matters, so BM25
    scores and cosine similarities never have to be compared directly."""
    scores, by_id = {}, {}
    for ranking in rankings:
        for rank, chunk in enumerate(ranking, start=1):
            scores[chunk["id"]] = scores.get(chunk["id"], 0) + 1 / (k + rank)
            by_id[chunk["id"]] = chunk
    return [by_id[i] for i in sorted(scores, key=scores.get, reverse=True)]


class HybridRetriever:
    def __init__(self, chunks: list, text_key: str = "text"):
        self.chunks = chunks
        self.bm25 = BM25Index([{**c, "text": c[text_key]} for c in chunks])
        self.vectors = VectorIndex(chunks, text_key=text_key)

    def search(self, query: str, k: int = 3, candidates: int = 6) -> list:
        lexical = [c for c, _ in self.bm25.search(query, candidates)]
        semantic = [c for c, _ in self.vectors.search(query, candidates)]
        originals = {c["id"]: c for c in self.chunks}
        return [originals[c["id"]] for c in reciprocal_rank_fusion([lexical, semantic])][:k]


# --- Reranking with Claude ----------------------------------------------------

class Reranked(BaseModel):
    ids: list[str]


def rerank(query: str, chunks: list, k: int = 3) -> list:
    """Ask Claude to order the candidate chunks by relevance (structured output)."""
    docs = "\n".join(f'<doc id="{c["id"]}">\n{c["text"]}\n</doc>' for c in chunks)
    prompt = (f"<question>{query}</question>\n\n<documents>\n{docs}\n</documents>\n\n"
              f"Return the ids of the {k} documents most useful for answering the question, "
              "most relevant first. Leave out documents that don't help.")
    result = structured(prompt, Reranked, effort="low")
    by_id = {c["id"]: c for c in chunks}
    return [by_id[i] for i in result.ids if i in by_id][:k]


# --- Contextual retrieval -----------------------------------------------------

def add_context(chunks: list, document: str) -> list:
    """Return copies of the chunks with a "context" sentence written by Claude
    and a "contextual_text" (context + chunk) to index. Cached on disk."""
    cache = json.loads(CONTEXT_CACHE.read_text()) if CONTEXT_CACHE.exists() else {}
    out = []
    for c in chunks:
        key = hashlib.sha256((document + c["text"]).encode()).hexdigest()
        if key not in cache:
            cache[key] = chat([{"role": "user", "content": (
                f"<document>\n{document}\n</document>\n\n<chunk>\n{c['text']}\n</chunk>\n\n"
                "Write one or two sentences that place this chunk within the whole document, "
                "to improve search retrieval of the chunk. Answer with only those sentences.")}],
                effort="low").strip()
            CONTEXT_CACHE.write_text(json.dumps(cache, indent=2))
        out.append({**c, "context": cache[key], "contextual_text": f"{cache[key]}\n\n{c['text']}"})
    return out
