"""Signal glossary: engineering terms → the exact signal that answers them.

A single MBEV run stores 267 signals, mostly internal connector values such as
batt1.C1.n.i. Engineers (and AI assistants) ask for "motor torque" or "battery
current", not for signal names. A glossary says which signal answers each term,
its sign convention, and the unit to show it in.

Glossaries are data files, one per model: glossaries/<Model>.json (see the README
there for the format). Any model works without one; a glossary improves accuracy.
Each file should be checked against real data and approved by a domain expert.
"""

from __future__ import annotations

import json
from pathlib import Path

from simcore import config


def _load(model: str) -> dict:
    short = model.split(".")[-1]
    path = Path(config.GLOSSARY_DIR) / f"{short}.json"
    if not short or not path.exists():
        return {}
    return json.loads(path.read_text())


def entries(model: str) -> list[dict]:
    """Glossary entries for a model (short or full name); empty if it has no glossary."""
    return _load(model).get("entries", [])


def approved_by(model: str) -> str | None:
    return _load(model).get("approved_by")


def find(model: str, search: str) -> list[dict]:
    """Glossary entries whose term, synonyms or signal match the search text."""
    s = search.lower().strip()
    hits = []
    for e in entries(model):
        words = [e["term"], *e["synonyms"]]
        if (any(s in w.lower() for w in words + [e["signal"]])            # "torque" finds "motor torque"
                or any(len(w) >= 3 and w.lower() in s for w in words)):   # "what is the SOC" finds "SOC"
            hits.append(e)
    return hits


def for_signal(model: str, signal: str) -> dict | None:
    """The glossary entry for a signal, if there is one."""
    return next((e for e in entries(model) if e["signal"] == signal), None)
