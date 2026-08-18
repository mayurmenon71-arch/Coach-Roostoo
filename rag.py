"""RAG retrieval over the Coach Roostoo knowledge cards.

This is a plain library module (no web server). server.py imports it and calls
`retrieve()` to fetch the facts relevant to a user's question, which it then
injects into the system prompt.

Two functions:
  - build_index()  : reads coach_compiler/cards/*.md, embeds them, stores vectors
                     in a local Chroma DB. Run once (python rag.py) before serving,
                     or as a build step when deploying.
  - retrieve(q)    : returns the k most relevant card chunks for question `q`.

Config via env vars (sensible defaults):
  RAG_EMBED_MODEL  - sentence-transformers model name (default all-MiniLM-L6-v2)
  RAG_DB_PATH      - where the Chroma index lives      (default ./chroma_db)
  RAG_CARDS_DIR    - folder of source .md cards        (default coach_compiler/cards)
"""

import os
import glob
import chromadb
from sentence_transformers import SentenceTransformer

_EMBED_MODEL = os.environ.get("RAG_EMBED_MODEL", "all-MiniLM-L6-v2")
_DB_PATH     = os.environ.get("RAG_DB_PATH", "./chroma_db")
_CARDS_DIR   = os.environ.get("RAG_CARDS_DIR", "coach_compiler/cards")
_COLLECTION  = "roostoo"

# Loaded once when this module is first imported.
_embedder = SentenceTransformer(_EMBED_MODEL)
_client   = chromadb.PersistentClient(path=_DB_PATH)


def build_index():
    """Read every .md card, chunk it, embed it, and store it in Chroma.
    Returns the number of chunks indexed. Re-running is safe (upsert)."""
    col = _client.get_or_create_collection(_COLLECTION)
    ids, texts, metas = [], [], []
    for path in sorted(glob.glob(f"{_CARDS_DIR}/**/*.md", recursive=True)):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        # ~1000-char chunks with 150-char overlap so context isn't cut mid-idea.
        for start in range(0, len(text), 850):
            chunk = text[start:start + 1000]
            if chunk.strip():
                ids.append(f"{path}::{start}")
                texts.append(chunk)
                metas.append({"source": path})
    if not texts:
        raise SystemExit(f"No .md cards found in {_CARDS_DIR} — nothing to index.")
    embeddings = _embedder.encode(texts, show_progress_bar=True).tolist()
    col.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metas)
    return len(texts)


def retrieve(question, k=3):
    """Return the k most relevant card chunks for `question`, joined into one
    string. Returns "" if the index doesn't exist yet or anything goes wrong,
    so callers can safely fall back."""
    if not question:
        return ""
    try:
        col = _client.get_collection(_COLLECTION)
        q_emb = _embedder.encode([question]).tolist()
        res = col.query(query_embeddings=q_emb, n_results=k)
        docs = (res.get("documents") or [[]])[0]
        return "\n\n---\n\n".join(docs)
    except Exception:
        return ""


if __name__ == "__main__":
    n = build_index()
    print(f"Indexed {n} chunks from {_CARDS_DIR} into {_DB_PATH}")
