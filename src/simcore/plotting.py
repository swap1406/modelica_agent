"""plot_signals(): interactive chart of chosen signals from a run.

The chart is saved as a self-contained HTML file in the run folder (plots/...) and
opens in any browser: hover for exact values, drag a box to zoom, double-click to reset.

Signals with the same unit share a panel; all panels share one time axis, so zooming
one zooms them all. Each signal keeps its own colour across the whole chart.

Linked cursor: hovering at time t in any panel shows a vertical line and the values at t
in ALL panels (like the cursor in CANape / MDA / Simulink Data Inspector).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from plotly.subplots import make_subplots

from simcore.results import find_run, list_signals, read_results, _read_record

# Hovering one panel triggers the hover at the same time in every panel.
# {plot_id} is filled in by Plotly; SUBPLOTS is filled in by plot_signals().
_LINKED_CURSOR_JS = """
var gd = document.getElementById('{plot_id}');
var SUBPLOTS = %s;
var busy = false;
// One vertical cursor line drawn over ALL panels (Plotly's own spike lines only
// appear in the panel under the mouse).
var cursor = document.createElement('div');
cursor.style.cssText = 'position:absolute;width:0;border-left:1px dashed #444;' +
                       'pointer-events:none;display:none;z-index:1000;';
gd.style.position = 'relative';
gd.appendChild(cursor);
function showCursor(x) {
  var fl = gd._fullLayout, xa = fl.xaxis;
  var first = fl.yaxis, last = fl['yaxis' + (SUBPLOTS.length > 1 ? SUBPLOTS.length : '')];
  var top = first._offset, bottom = last._offset + last._length;
  cursor.style.left = (xa._offset + xa.l2p(x)) + 'px';
  cursor.style.top = top + 'px';
  cursor.style.height = (bottom - top) + 'px';
  cursor.style.display = 'block';
}
gd.on('plotly_hover', function (ev) {
  if (busy || !ev.points || !ev.points.length) { return; }
  busy = true;
  var x = ev.points[0].x;
  Plotly.Fx.hover(gd, { xval: x }, SUBPLOTS);   // values at time x in every panel
  showCursor(x);                                 // one line through every panel
  busy = false;
});
gd.on('plotly_unhover', function () { if (!busy) { cursor.style.display = 'none'; } });
"""

# Fixed colour order: a signal's colour depends only on its position in the request,
# never on how many panels there are. (Colourblind-checked categorical palette.)
COLOURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]


def _panels(signals: list[str], units: dict[str, str]) -> list[list[str]]:
    """Group signals into panels by unit, keeping the order in which they were requested.
    Signals without a declared unit each get their own panel (we can't know they match)."""
    panels: dict[str, list[str]] = {}
    for s in signals:
        key = units.get(s) or f"__no_unit__{s}"
        panels.setdefault(key, []).append(s)
    return list(panels.values())


def plot_signals(run="latest", signals: list[str] | None = None, title: str | None = None,
                 output: str | Path | None = None) -> Path:
    """Plot signals from a run and return the path of the saved HTML chart.

    run      run id, "latest", "latest:<Model>" or a RunResult
    signals  signal names, e.g. ["velSens.v", "batt1.SOC"]
    title    chart title (default: model name and run id)
    output   where to save the HTML file (default: <run folder>/plots/<time>_<signals>.html)
    """
    if not signals:
        raise ValueError("Give at least one signal to plot, e.g. ['velSens.v'].")
    if len(signals) > len(COLOURS):
        raise ValueError(f"At most {len(COLOURS)} signals per chart; split into several charts.")

    folder = find_run(run)
    data = read_results(str(folder), signals)
    info = {s.name: s for s in list_signals(str(folder), include_derivatives=True)}
    units = {s: info[s].unit if s in info else "" for s in signals}
    panels = _panels(signals, units)

    record = _read_record(folder) or {}
    model = record.get("model", "")

    def label(s: str) -> str:
        description = info[s].description if s in info else ""
        return f"{s} — {description}" if description else s

    fig = make_subplots(rows=len(panels), cols=1, shared_xaxes=True, vertical_spacing=0.07,
                        subplot_titles=[" · ".join(p) for p in panels])
    for row, panel in enumerate(panels, start=1):
        for s in panel:
            unit = units[s]
            fig.add_scatter(
                x=data["time"], y=data[s], mode="lines", name=s, row=row, col=1,
                line={"color": COLOURS[signals.index(s)], "width": 2},
                hovertemplate=f"{label(s)}<br>%{{y:.4g}} {unit}<extra></extra>",
            )
        unit = units[panel[0]]
        fig.update_yaxes(title_text=unit or "(no unit)", row=row, col=1)
    fig.update_xaxes(title_text="time (s)", row=len(panels), col=1)

    fig.update_layout(
        title={"text": title or f"{model} — run {folder.name}", "x": 0.01},
        template="plotly_white",
        height=230 * len(panels) + 140,
        hovermode="x",                  # each panel labels its signals at the hovered time
        legend={"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0.01},
        margin={"l": 70, "r": 30, "t": 110, "b": 50},
    )

    if output is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        short = "_".join(s.split(".")[-1] for s in signals)[:60]
        output = folder / "plots" / f"{stamp}_{short}.html"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # include_plotlyjs=True embeds the chart library, so the file works offline.
    subplots = ["xy" if i == 1 else f"x{i}y{i}" for i in range(1, len(panels) + 1)]
    fig.write_html(output, include_plotlyjs=True, config={"displaylogo": False},
                   post_script=_LINKED_CURSOR_JS % json.dumps(subplots))
    return output
