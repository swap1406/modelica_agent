"""chart_data(): compact, downsampled chart data for the in-chat chart (MCP App).

A 1400 s MBEV run has about 14,000 rows. Sending all of them to the chat would be
slow and can exceed what the chat accepts (~150,000 characters). Instead the time
range is cut into buckets, and in each bucket the minimum and maximum of every
signal are kept, so peaks (e.g. top speed) are never lost.
"""

from __future__ import annotations

import numpy as np

from simcore.plotting import COLOURS, _panels
from simcore.results import _read_record, find_run, list_signals, read_results


def _r(x) -> float:
    return float(f"{float(x):.5g}")       # 5 significant digits keeps the data small


def downsample_indices(columns: list[np.ndarray], max_buckets: int) -> np.ndarray:
    """Row indices to keep: first, last, and the min and max of every column per bucket."""
    n = len(columns[0])
    if n <= 2 * max_buckets:
        return np.arange(n)
    keep = {0, n - 1}
    for bucket in np.array_split(np.arange(n), max_buckets):
        for y in columns:
            part = y[bucket]
            keep.add(int(bucket[np.argmin(part)]))
            keep.add(int(bucket[np.argmax(part)]))
    return np.array(sorted(keep))


def chart_data(run="latest", signals: list[str] | None = None, title: str | None = None,
               max_buckets: int = 400) -> dict:
    """Data for the in-chat chart: shared time axis, one panel per unit, colours per signal."""
    if not signals:
        raise ValueError("Give at least one signal to plot, e.g. ['velSens.v'].")
    if len(signals) > len(COLOURS):
        raise ValueError(f"At most {len(COLOURS)} signals per chart; split into several charts.")
    folder = find_run(run)
    data = read_results(str(folder), signals)
    info = {s.name: s for s in list_signals(str(folder), include_derivatives=True)}
    units = {s: info[s].unit if s in info else "" for s in signals}
    model = (_read_record(folder) or {}).get("model", "").split(".")[-1]

    idx = downsample_indices([data[s].to_numpy() for s in signals], max_buckets)
    panels = []
    for panel in _panels(signals, units):
        panels.append({
            "unit": units[panel[0]],
            "series": [{
                "name": s,
                "description": info[s].description if s in info else "",
                "color": COLOURS[signals.index(s)],
                "y": [_r(v) for v in data[s].to_numpy()[idx]],
            } for s in panel],
        })
    return {
        "run_id": folder.name,
        "model": model,
        "title": title or f"{model} — run {folder.name}",
        "t": [_r(v) for v in data["time"].to_numpy()[idx]],
        "panels": panels,
        "points": int(len(idx)),
        "original_points": int(len(data)),
    }
