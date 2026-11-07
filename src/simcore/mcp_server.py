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

import logging
import sys

from mcp.server.fastmcp import FastMCP

from simcore import catalog, results
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


def main() -> None:
    log.info("modelica_agent MCP server starting (stdio)")
    mcp.run()  # default transport: stdio


if __name__ == "__main__":
    main()
