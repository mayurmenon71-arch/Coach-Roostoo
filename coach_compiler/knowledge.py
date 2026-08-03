"""
Step 2 — retrieve(cards): RAG over the versioned knowledge cards.

Retrieval here is not for coverage — the base model already knows what RSI
is. It is for CONTROL: platform truths (fees, signal families, competition rules,
reward terms) that must be exactly right and traceable when a user — or a
regulator — asks why Coach said what it said. Web-scale RAG would actively
hurt (confident garbage + a prompt-injection surface + unauditable answers).

The corpus is hand-written markdown cards in coach_compiler/cards/, owned by
the quant team and versioned with the platform. Scoring is a deliberately
simple, deterministic keyword match (stdlib only) — the corpus is a few
hundred cards at most, and auditability beats cleverness here.
"""

import os
import re

CARDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cards")

_WORD_RE = re.compile(r"[a-z0-9]+")
_FRONT_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)

_STOP = frozenset(
    "the a an and or of to in on for with is are it its this that what how "
    "why do does my i me your you agent agents want should can".split()
)


def _tokens(text):
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOP]


def _parse_card(raw):
    meta = {"id": "", "title": "", "tags": ""}
    m = _FRONT_RE.match(raw)
    body = raw
    if m:
        body = raw[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta, body.strip()


def load_cards():
    """Load every card. Cached after first call."""
    if hasattr(load_cards, "_cache"):
        return load_cards._cache
    cards = []
    for fname in sorted(os.listdir(CARDS_DIR)):
        if not fname.endswith(".md"):
            continue
        with open(os.path.join(CARDS_DIR, fname), "r", encoding="utf-8") as f:
            meta, body = _parse_card(f.read())
        cards.append({
            "id": meta["id"] or fname[:-3],
            "title": meta["title"],
            "tags": set(_tokens(meta["tags"])),
            "title_tokens": set(_tokens(meta["title"])),
            "body": body,
            "body_tokens": set(_tokens(body)),
        })
    load_cards._cache = cards
    return cards


def retrieve(query, k=3):
    """Return the top-k cards for a query. Deterministic keyword scoring:
    tag hit = 3, title hit = 2, body hit = 1 per query token."""
    q = _tokens(query or "")
    if not q:
        return []
    scored = []
    for card in load_cards():
        score = sum(
            (3 if w in card["tags"] else 0)
            + (2 if w in card["title_tokens"] else 0)
            + (1 if w in card["body_tokens"] else 0)
            for w in q
        )
        if score > 0:
            scored.append((score, card))
    scored.sort(key=lambda t: (-t[0], t[1]["id"]))
    return [
        {"id": c["id"], "title": c["title"], "content": c["body"]}
        for _, c in scored[: max(1, min(int(k or 3), 5))]
    ]
