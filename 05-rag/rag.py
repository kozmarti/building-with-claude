"""Ask a question about the training guide, answered with RAG.

The full pipeline:
  1. chunk the guide by section                    (chunking.py)
  2. optional: add Claude-written context to each chunk  (--contextual)
  3. hybrid search: BM25 + embeddings, merged with RRF (retrieval.py)
  4. rerank the candidates with Claude
  5. Claude answers using only those chunks, and cites them

Run:  python 05-rag/rag.py "How hard should my long run be?"
      python 05-rag/rag.py "What is VO2-5x4?" --contextual
      python 05-rag/rag.py "What is VO2-5x4?" --compare   (search methods side by side)
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from chunking import DOCUMENT, load_chunks  # noqa: E402
from common.claude import chat  # noqa: E402
from retrieval import HybridRetriever, add_context, rerank  # noqa: E402

SYSTEM = """You answer questions about a running and cycling club's training guide.
Use only the sources provided. After each fact, cite its section like [2. Workout library].
If the sources don't contain the answer, say so plainly instead of guessing."""


def answer(question: str, chunks: list) -> str:
    sources = "\n".join(f'<source section="{c["title"]}">\n{c["text"]}\n</source>' for c in chunks)
    return chat([{"role": "user", "content": f"<sources>\n{sources}\n</sources>\n\n{question}"}],
                system=SYSTEM, effort="low")


def compare(question: str, retriever: HybridRetriever) -> None:
    print("Top 3 by search method:")
    print("  BM25:   ", [c["title"] for c, _ in retriever.bm25.search(question, 3)])
    print("  Vector: ", [c["title"] for c, _ in retriever.vectors.search(question, 3)])
    print("  Hybrid: ", [c["title"] for c in retriever.search(question, 3)])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="?", default="How hard should my weekly long run be?")
    parser.add_argument("--contextual", action="store_true", help="index chunks with Claude-written context")
    parser.add_argument("--no-rerank", action="store_true", help="skip the Claude reranking step")
    parser.add_argument("--compare", action="store_true", help="only show BM25 vs vector vs hybrid results")
    args = parser.parse_args()

    chunks = load_chunks()
    text_key = "text"
    if args.contextual:
        chunks = add_context(chunks, DOCUMENT.read_text())
        text_key = "contextual_text"
    retriever = HybridRetriever(chunks, text_key=text_key)

    print(f"Question: {args.question}\n")
    if args.compare:
        compare(args.question, retriever)
        return

    candidates = retriever.search(args.question, k=6)
    best = candidates[:3] if args.no_rerank else rerank(args.question, candidates, k=3)
    print("Retrieved:", ", ".join(c["title"] for c in best), "\n")
    print(answer(args.question, best))


if __name__ == "__main__":
    main()
