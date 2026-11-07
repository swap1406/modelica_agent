"""MCP server: exposes simcore functions as tools for AI assistants.

How it runs: an AI app (e.g. Claude Desktop) starts this program inside our
Docker container and talks to it over stdio (standard input/output).

Important: stdout is the message channel to the AI app. Never print() to it,
or the app receives garbage. Use the logger below, which writes to stderr.

Start it with:  python3 -m simcore.mcp_server

Tool design rules (see the Milestone 2 plan):
  - few tools, each with a clear name and a description written for the AI
  - every result names the run it came from (run_id), so answers are traceable
  - results are short summaries, never full time series
  - errors say what to do next (e.g. "Did you mean batt1.SOC?")
"""

import json
import logging
import sys

import base64
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, ImageContent, TextContent

from simcore import catalog, config, plotting, results
from simcore.plot_data import chart_data
from simcore.plot_png import plot_signals_png
from simcore.environment import environment_info as _environment_info

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("simcore.mcp")

# Read once by the AI when it connects: how to use the tools together.
INSTRUCTIONS = """\
Tools for running and analysing OpenModelica simulation models (modelica_agent).
- Start with list_models to see which models exist and what they represent.
- To answer questions about results, find a run with list_runs, find exact signal
  names with list_signals, then get values with read_results.
- Use run ids like "latest:MBEV" rather than "latest", so you read the right model.
- Only start a new simulation (run_simulation) when the user asks for one or no
  suitable run exists; otherwise read existing runs. run_simulation already
  returns a summary of the key signals, so you often don't need read_results.
- plot_signals shows an interactive chart in the chat (where supported) and
  gives you an image of it to look at; describe what it shows if helpful.
- Report numbers only from tool results, convert units when the user asks
  (m/s x 3.6 = km/h; SOC fraction x 100 = %), and always mention the run id.
- If a request is ambiguous (which model? which signal?), say what you assumed or ask.
"""

mcp = FastMCP("modelica_agent", instructions=INSTRUCTIONS)

MAX_SIGNALS_LISTED = 30


def _clean_error(exc: Exception) -> ValueError:
    """Turn library errors into plain messages the AI can act on."""
    message = exc.args[0] if exc.args else str(exc)
    return ValueError(str(message))


# Each @mcp.tool() function becomes one "tool card" the AI sees:
#   name = function name, description = docstring, inputs = parameters.

@mcp.tool()
def environment_info() -> dict:
    """Report the software versions the simulation environment is running:
    OpenModelica, Python, simcore, pandas and plotly. Use this when the user
    asks which versions are installed, or to check the setup is working."""
    log.info("tool: environment_info")
    return _environment_info()


@mcp.tool()
def list_models() -> list[dict]:
    """List the simulation models available, with what each one represents
    (vehicle type, drive cycle, standard run length), its most useful signals,
    known quirks, and its most recent successful run. Use this first to pick the
    right model for a request, e.g. 'the EV on NEDC' is MBEV."""
    log.info("tool: list_models")
    out = []
    for name, entry in catalog.MODELS.items():
        latest = results.list_runs(model=name, limit=20)
        latest_ok = next((r["run_id"] for r in latest if r["status"] == "success"), None)
        out.append({
            "name": name,
            "description": entry["description"],
            "drive_cycle": entry["drive_cycle"],
            "standard_run_length_s": entry["default_stop_time_s"],
            "key_signals": entry["key_signals"],
            "notes": entry["notes"],
            "latest_successful_run": latest_ok,
        })
    return out


@mcp.tool()
def list_runs(model: str | None = None, limit: int = 10) -> list[dict]:
    """List recent simulation runs, newest first: run id, model, status
    (success/failed), start time and duration. Optionally only one model
    (e.g. "MBEV"). Use this to find a run to read, or to compare the latest run
    with the one before it."""
    log.info("tool: list_runs model=%s limit=%s", model, limit)
    return results.list_runs(model=model, limit=max(1, min(limit, 50)))


@mcp.tool()
def list_signals(run: str = "latest", search: str | None = None) -> dict:
    """Find signals (variables) stored in a run's results, with description and
    unit. Use a keyword to narrow the list, e.g. search="SOC", "speed", "torque",
    "batt". run can be a run id from list_runs, or "latest:<model>" such as
    "latest:MBEV". Use this to get the exact signal name before read_results."""
    log.info("tool: list_signals run=%s search=%s", run, search)
    try:
        folder = results.find_run(run)
        found = results.list_signals(run, search=search)
    except (KeyError, FileNotFoundError) as exc:
        raise _clean_error(exc)
    out = {
        "run_id": folder.name,
        "matches": len(found),
        "signals": [{"name": s.name, "description": s.description, "unit": s.unit}
                    for s in found[:MAX_SIGNALS_LISTED]],
    }
    if len(found) > MAX_SIGNALS_LISTED:
        out["note"] = f"Showing the first {MAX_SIGNALS_LISTED}; use a more specific search."
    return out


@mcp.tool()
def read_results(signals: list[str], run: str = "latest", at_time: float | None = None) -> dict:
    """Summarise signals from a run: start, end, min and max values (with the
    times of min and max) and the unit. Optionally the value at a given time
    in seconds (at_time). Use exact signal names from list_signals, e.g.
    ["batt1.SOC", "velSens.v"]. run can be a run id or "latest:<model>".
    Returns a compact summary, not the full time series."""
    log.info("tool: read_results run=%s signals=%s at_time=%s", run, signals, at_time)
    try:
        return results.summarize_signals(run, signals, at_time=at_time)
    except (KeyError, FileNotFoundError, ValueError) as exc:
        raise _clean_error(exc)


@mcp.tool()
def run_simulation(model: str, stop_time: float | None = None) -> dict:
    """Run a simulation of a catalogue model (see list_models), e.g. model="MBEV".
    Uses the model's standard run length unless stop_time (seconds) is given.
    Takes from a few seconds to about a minute. Returns the new run id, status,
    any errors, model notes (e.g. known harmless messages) and a summary of the
    model's key signals (start, end, min, max), such as final battery SOC and
    top speed. Creates a new run each time; only use it when a new run is wanted."""
    log.info("tool: run_simulation model=%s stop_time=%s", model, stop_time)
    try:
        result, summary, entry = catalog.run_model(model, stop_time=stop_time)
    except (KeyError, ValueError) as exc:
        raise _clean_error(exc)
    out = {
        "run_id": result.run_id,
        "model": entry["name"],
        "status": result.status,
        "stop_time_s": result.stop_time,
        "duration_s": result.duration_s,
        "errors": [e.splitlines()[0][:200] for e in result.errors[:5]],
        "warnings_count": len(result.warnings),
        "model_notes": entry["notes"],
    }
    if summary:
        out["key_signal_summary"] = summary["signals"]
    if result.status != "success":
        out["next_step"] = "The run failed. Report the errors; console.txt in the run folder has details."
    return out


# ── In-chat interactive chart (MCP App) ───────────────────────────────────────
# An MCP App is a ui:// resource holding an HTML page, linked to a tool through
# _meta.ui.resourceUri. Hosts that support MCP Apps (e.g. Claude Desktop) show the
# page as a panel in the chat and send it the tool result's structuredContent.
APP_MIME = "text/html;profile=mcp-app"
PLOT_UI = "ui://modelica_agent/plot.html"
PLOT_HTML = (Path(__file__).parent / "ui" / "plot_view.html").read_text()


@mcp.resource(PLOT_UI, name="plot_view", mime_type=APP_MIME,
              meta={"ui": {"csp": {"resourceDomains": ["https://unpkg.com"]}}})
def plot_view() -> str:
    """Interactive chart page used by plot_signals."""
    return PLOT_HTML


@mcp.tool(meta={"ui": {"resourceUri": PLOT_UI}, "ui/resourceUri": PLOT_UI})
def plot_signals(signals: list[str], run: str = "latest", title: str | None = None) -> CallToolResult:
    """Plot one or more signals from a run, e.g. signals=["velSens.v", "batt1.SOC"],
    run="latest:MBEV". Shows an interactive chart in the chat (zoom, hover, linked
    cursor across panels) and returns an image you can look at to describe
    trends, plus the path of an interactive HTML file in the project folder.
    Signals with the same unit share a panel; up to 8 signals. Use exact names
    from list_signals."""
    log.info("tool: plot_signals run=%s signals=%s", run, signals)
    try:
        folder = results.find_run(run)
        data = chart_data(str(folder), signals, title=title)
        png = plot_signals_png(str(folder), signals, title=title)
        html = plotting.plot_signals(str(folder), signals, title=title)
    except (KeyError, FileNotFoundError, ValueError) as exc:
        raise _clean_error(exc)
    info = {
        "run_id": folder.name,
        "signals": signals,
        "image": str(png.relative_to(config.PROJECT_ROOT)),
        "interactive_chart": str(html.relative_to(config.PROJECT_ROOT)),
        "note": "An interactive chart is shown in the chat where supported; the HTML file "
                "can also be opened from the project folder in a web browser.",
    }
    return CallToolResult(
        content=[
            ImageContent(type="image", mimeType="image/png",
                         data=base64.b64encode(png.read_bytes()).decode()),
            TextContent(type="text", text=json.dumps(info)),
        ],
        structuredContent=data,
    )


def main() -> None:
    log.info("modelica_agent MCP server starting (stdio)")
    mcp.run()  # default transport: stdio


if __name__ == "__main__":
    main()
