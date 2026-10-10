"""Read simulation results from a run folder.

    list_signals(run, search)      which signals exist, with description and unit
    read_results(run, signals)     a table (pandas DataFrame) with time + chosen signals

`run` can be:
    "latest"                       the most recent successful run
    "latest:MBEV"                  the most recent successful run of a model (short or full name)
    "20261010-083117_MBEV"         a run id (folder name in results/runs/)
    a RunResult                    as returned by run_simulation()
"""

from __future__ import annotations

import difflib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from simcore import config


@dataclass
class Signal:
    """One variable stored in a results file."""

    name: str            # e.g. "batt1.SOC"
    description: str     # e.g. "State of charge"   (from the model, may be empty)
    unit: str            # e.g. "V", "m/s"; "" if the model doesn't declare one
    kind: str            # "state", "variable", "parameter" or "derivative"


# ── Finding the run ───────────────────────────────────────────────────────────

def find_run(run="latest") -> Path:
    """Return the folder of a run (see module docstring for accepted forms)."""
    if hasattr(run, "run_dir"):                       # a RunResult
        return Path(run.run_dir)
    run = str(run)
    if run.startswith("latest"):
        model = run.split(":", 1)[1] if ":" in run else None
        for folder in sorted(config.RUNS_DIR.glob("*"), reverse=True):   # newest first
            record = _read_record(folder)
            if not record or record.get("status") != "success":
                continue
            if model and model not in (record["model"], record["model"].split(".")[-1]):
                continue
            return folder
        raise FileNotFoundError(f"No successful run found{' for ' + model if model else ''} in {config.RUNS_DIR}")
    folder = Path(run) if Path(run).is_absolute() else config.RUNS_DIR / run
    if not folder.is_dir():
        raise FileNotFoundError(f"Run '{run}' not found in {config.RUNS_DIR}")
    return folder


def _read_record(folder: Path) -> dict | None:
    try:
        return json.loads((folder / "run.json").read_text())
    except (OSError, ValueError):
        return None


def _result_csv(folder: Path) -> Path:
    record = _read_record(folder)
    if record and record.get("result_file"):
        return folder / Path(record["result_file"]).name
    csvs = list(folder.glob("*_res.csv"))
    if not csvs:
        raise FileNotFoundError(f"No results file in {folder} (did the run fail?)")
    return csvs[0]


# ── Listing signals ───────────────────────────────────────────────────────────

def _signal_info(folder: Path) -> dict[str, tuple[str, str, str]]:
    """Descriptions, units and kinds from <Model>_init.xml, if the run kept it."""
    info = {}
    for xml_file in folder.glob("*_init.xml"):
        for var in ET.parse(xml_file).getroot().iter("ScalarVariable"):
            name = var.get("name", "")
            typ = var[0] if len(var) else None
            unit = (typ.get("unit") or "") if typ is not None else ""
            if var.get("variability") == "parameter":
                kind = "parameter"
            elif name.startswith("der("):
                kind = "derivative"
            elif var.get("classType", "").endswith("Sta"):
                kind = "state"
            else:
                kind = "variable"
            info[name] = (var.get("description", ""), unit, kind)
    return info


def list_signals(run="latest", search: str | None = None,
                 include_derivatives: bool = False) -> list[Signal]:
    """List the signals in a run's results, optionally filtered by a search text.

    The search matches name or description, ignoring case, e.g. "soc", "speed", "batt".
    """
    folder = find_run(run)
    names = pd.read_csv(_result_csv(folder), nrows=0).columns
    names = [n.strip().strip('"') for n in names if n.strip().strip('"') != "time"]
    info = _signal_info(folder)

    signals = []
    for name in names:
        description, unit, kind = info.get(name, ("", "", "derivative" if name.startswith("der(") else "variable"))
        if kind == "derivative" and not include_derivatives:
            continue
        if search and search.lower() not in name.lower() and search.lower() not in description.lower():
            continue
        signals.append(Signal(name, description, unit, kind))
    return signals


# ── Reading values ────────────────────────────────────────────────────────────

def _suggest(name: str, available: list[str]) -> str:
    """Helpful 'did you mean' text for an unknown signal name (best guesses first)."""
    low = name.lower()
    by_lower = {a.lower(): a for a in available}
    exact_case = [by_lower[low]] if low in by_lower else []                      # wrong capitals
    last_part = [a for a in available if a.lower().split(".")[-1] == low.split(".")[-1]]  # same ending
    close = [by_lower[m] for m in difflib.get_close_matches(low, list(by_lower), n=5, cutoff=0.5)]
    contains = [a for a in available if low.split(".")[-1] in a.lower()]
    options = list(dict.fromkeys(exact_case + last_part + close + contains))[:5]
    return f" Did you mean: {', '.join(options)}?" if options else ""


def read_results(run="latest", signals: list[str] | None = None) -> pd.DataFrame:
    """Return a table with 'time' plus the requested signals (all signals if None).

    Only the requested columns are read, so this is fast even for large result files.
    Rows with a repeated time (OpenModelica writes these at events) keep the last value.
    """
    csv = _result_csv(find_run(run))
    available = [c.strip().strip('"') for c in pd.read_csv(csv, nrows=0).columns]

    if signals is None:
        columns = available
    else:
        missing = [s for s in signals if s not in available]
        if missing:
            raise KeyError(f"Signal(s) not in results: {', '.join(missing)}.{_suggest(missing[0], available)}")
        columns = ["time"] + [s for s in signals if s != "time"]

    data = pd.read_csv(csv, usecols=columns)[columns]
    return data.drop_duplicates(subset="time", keep="last").reset_index(drop=True)
