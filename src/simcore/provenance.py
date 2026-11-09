"""Provenance: was a run made from the approved, unmodified model sources?

A manifest (models/source_manifest.json) stores a SHA-256 fingerprint of every model
source file the simulations use: our own models, the EHPT libraries and their data files
(drive cycles, efficiency maps). Every run compares the current files with the manifest
and records the result in its run.json. A run made from edited files is flagged, so it
can never look like a normal result.

Changing a model on purpose is a deliberate step: edit the files, then update the
manifest and commit both:
    docker compose run --rm om python3 -m simcore.provenance --update
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from simcore import config

# Folders whose files can change simulation results.
SOURCE_DIRS = ["models", "third_party/EHPTlib", "third_party/EHPTexamples"]
SUFFIXES = {".mo", ".txt", ".csv", ".mat"}
MANIFEST = "models/source_manifest.json"
MAX_LISTED = 10


def _root() -> Path:
    return Path(config.PROJECT_ROOT)


def current_fingerprints() -> dict[str, str]:
    """SHA-256 of every model source file, keyed by its path inside the project."""
    root = _root()
    out = {}
    for d in SOURCE_DIRS:
        for f in sorted((root / d).rglob("*")):
            if f.is_file() and f.suffix.lower() in SUFFIXES and ".git" not in f.parts:
                rel = str(f.relative_to(root))
                if rel != MANIFEST:
                    out[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def check() -> dict:
    """Compare the current model sources with the manifest."""
    path = _root() / MANIFEST
    if not path.exists():
        return {"status": "unknown", "model_modified": None,
                "note": f"No manifest at {MANIFEST}; run: python3 -m simcore.provenance --update"}
    approved = json.loads(path.read_text())["files"]
    now = current_fingerprints()
    changed = sorted(f for f in approved if f in now and now[f] != approved[f])
    missing = sorted(f for f in approved if f not in now)
    added = sorted(f for f in now if f not in approved)
    modified = bool(changed or missing or added)
    result = {"status": "modified" if modified else "approved", "model_modified": modified}
    if modified:
        result.update({"changed": changed[:MAX_LISTED], "missing": missing[:MAX_LISTED],
                       "added": added[:MAX_LISTED]})
    return result


def write_manifest() -> int:
    files = current_fingerprints()
    path = _root() / MANIFEST
    path.write_text(json.dumps({"description": "Approved model sources (SHA-256). Update only on purpose.",
                                "files": files}, indent=1) + "\n")
    return len(files)


if __name__ == "__main__":
    if "--update" in sys.argv:
        print(f"Manifest updated: {write_manifest()} files")
    else:
        print(json.dumps(check(), indent=2))
