"""Step 1 of RAG: split a long document into chunks.

Retrieval works on chunks, not whole documents: we search for the few pieces
that answer a question and send only those to Claude.

Two strategies, so they can be compared:
  - by section: follow the document's own headings. Each chunk is one complete
    topic, which suits structured text like guides, manuals or laws.
  - by size: fixed-size pieces with some overlap. Works on any text, but a
    chunk can start or stop in the middle of an idea.
"""

import re
from pathlib import Path

DOCUMENT = Path(__file__).parent / "training_guide.md"


def chunk_by_section(text: str) -> list:
    """One chunk per '## ' heading. The heading stays in the chunk, so search
    and citations both know which section it came from."""
    chunks = []
    for part in re.split(r"(?m)^(?=## )", text):
        part = part.strip()
        if not part.startswith("## "):
            continue  # the title and intro before the first section
        title = part.splitlines()[0][3:].strip()
        chunks.append({"id": f"s{len(chunks) + 1}", "title": title, "text": part})
    return chunks


def chunk_by_size(text: str, size: int = 400, overlap: int = 80) -> list:
    """Fixed-size chunks of `size` characters; each one repeats the last
    `overlap` characters of the previous chunk so ideas aren't cut in half."""
    chunks, start = [], 0
    while start < len(text):
        piece = text[start:start + size].strip()
        if piece:
            chunks.append({"id": f"c{len(chunks) + 1}", "title": f"characters {start}-{start + len(piece)}",
                           "text": piece})
        start += size - overlap
    return chunks


def load_chunks() -> list:
    return chunk_by_section(DOCUMENT.read_text())


if __name__ == "__main__":
    text = DOCUMENT.read_text()
    by_section, by_size = chunk_by_section(text), chunk_by_size(text)
    print(f"By section: {len(by_section)} chunks")
    for c in by_section:
        print(f"  {c['id']}: {c['title']} ({len(c['text'])} chars)")
    print(f"\nBy size (400 chars, 80 overlap): {len(by_size)} chunks.")
    cut = next((c for c in by_size if not c["text"].endswith((".", ":"))), None)
    if cut:
        print(f"  {cut['id']} stops mid-sentence: ..." + cut["text"][-100:].replace("\n", " "))
