"""plot_signals_png(): a static PNG chart of chosen signals from a run.

Same layout as the interactive HTML chart (plotting.py): one panel per unit,
shared time axis, a fixed colour per signal. A PNG can be shown directly inside
an AI chat (MCP image content), and the AI can look at it too. For zooming and
hovering, use the HTML chart.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")            # draw to files only: no screen inside Docker
import matplotlib.pyplot as plt  # noqa: E402

from simcore.plotting import COLOURS, _panels  # noqa: E402
from simcore.results import _read_record, find_run, list_signals, read_results  # noqa: E402


def plot_signals_png(run="latest", signals: list[str] | None = None, title: str | None = None,
                     output: str | Path | None = None) -> Path:
    """Plot signals from a run as a PNG and return its path (default: <run>/plots/<time>_<signals>.png)."""
    if not signals:
        raise ValueError("Give at least one signal to plot, e.g. ['velSens.v'].")
    if len(signals) > len(COLOURS):
        raise ValueError(f"At most {len(COLOURS)} signals per chart; split into several charts.")

    folder = find_run(run)
    data = read_results(str(folder), signals)
    info = {s.name: s for s in list_signals(str(folder), include_derivatives=True)}
    units = {s: info[s].unit if s in info else "" for s in signals}
    panels = _panels(signals, units)
    model = (_read_record(folder) or {}).get("model", "").split(".")[-1]

    fig, axes = plt.subplots(len(panels), 1, sharex=True, squeeze=False,
                             figsize=(10, 2.4 * len(panels) + 0.8), dpi=80)
    for ax, panel in zip(axes[:, 0], panels):
        for s in panel:
            ax.plot(data["time"], data[s], color=COLOURS[signals.index(s)], linewidth=1.4, label=s)
        ax.set_ylabel(units[panel[0]] or "(no unit)")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper left", fontsize=8, frameon=False)
    axes[-1, 0].set_xlabel("time (s)")
    fig.suptitle(title or f"{model} — run {folder.name}", x=0.01, ha="left", fontsize=11)
    fig.tight_layout()

    if output is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        short = "_".join(s.split(".")[-1] for s in signals)[:60]
        output = folder / "plots" / f"{stamp}_{short}.png"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)
    return output
