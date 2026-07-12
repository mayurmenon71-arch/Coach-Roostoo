"""
CLI demo:  python3 -m coach_compiler [intent]

No API key:   renders the three Section 7.5 worked examples through the real
              validator + gene-card renderer — a deterministic look at the
              output with zero model calls.
With API_KEY: pass an intent string and it runs the live Create loop
              (classify -> elicit -> emit -> validate -> gene card).

    python3 -m coach_compiler
    API_KEY=... python3 -m coach_compiler "buy dips on SOL but never blow up"
"""

import os
import sys

from . import exemplars as E
from .genecard import build_gene_card, render_text
from .orchestrator import run_create
from .validator import validate_config


def _demo_offline():
    print("No API_KEY set — showing the three worked examples compiled offline "
          "(validator + gene card, no model calls).\n")
    for tag, intent, arch, cfg, rat, sig in E.WORKED_EXAMPLES:
        v = validate_config(cfg)
        if not v["valid"]:
            print("Exemplar %s FAILED validation: %s" % (tag, v["errors"]))
            continue
        card = build_gene_card(v["config"], rat,
                               {"archetype": arch, "confidence": 0.9,
                                "signals_heard": sig},
                               v["warnings"])
        print('USER: "%s"' % intent)
        print(render_text(card))
        print()


def _live(intent):
    out = run_create([{"role": "user", "content": intent}])
    if out["type"] == "gene_card":
        print(render_text(out["card"]))
        print("\nCoach: " + out["text"])
    else:
        print("[%s] %s" % (out["type"], out["text"]))


def main():
    intent = " ".join(sys.argv[1:]).strip()
    if os.environ.get("API_KEY") and intent:
        _live(intent)
    elif intent and not os.environ.get("API_KEY"):
        print("Set API_KEY to compile a live intent. Showing offline demo instead.\n")
        _demo_offline()
    else:
        _demo_offline()


if __name__ == "__main__":
    main()
