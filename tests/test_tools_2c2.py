"""Tests for the action tools added in Milestone 2c-2: run_model, run_simulation
and plot_signals. Uses the fast HelloEV model."""

import asyncio

import pytest

from simcore import config, run_model
from simcore import mcp_server


def call(tool, args):
    """Call an MCP tool the way an AI app would, and return its text."""
    return str(asyncio.run(mcp_server.mcp.call_tool(tool, args)))


def error_text(tool, args):
    """Call a tool expected to fail and return the error message."""
    try:
        return call(tool, args)            # some MCP versions return the error...
    except Exception as exc:               # ...others raise it
        return str(exc)


def test_run_model_uses_catalogue_settings():
    result, summary, entry = run_model("helloev", stop_time=50)
    assert result.status == "success", result.summary()
    assert result.stop_time == 50
    assert entry["name"] == "HelloEV"
    names = [s["name"] for s in summary["signals"]]
    assert "v_kph" in names


def test_run_model_rejects_unknown_model_and_silly_stop_time():
    with pytest.raises(KeyError, match="Available models"):
        run_model("Tesla")
    with pytest.raises(ValueError, match="stop_time must be between"):
        run_model("HelloEV", stop_time=-5)


def test_run_simulation_tool_returns_run_id_and_summary():
    text = call("run_simulation", {"model": "HelloEV", "stop_time": 50})
    assert "success" in text and "run_id" in text and "v_kph" in text


def test_run_simulation_tool_explains_unknown_model():
    message = error_text("run_simulation", {"model": "Tesla"})
    assert "Available models" in message and "MBEV" in message


def test_plot_signals_tool_returns_project_relative_path():
    result, _, _ = run_model("HelloEV", stop_time=50)
    text = call("plot_signals", {"signals": ["v_kph", "x"], "run": result.run_id})
    assert "results/test_runs/" in text and "/work/" not in text
    plots = config.RUNS_DIR / result.run_id / "plots"
    assert list(plots.glob("*.html")), "the interactive chart should exist"
    assert list(plots.glob("*.png")), "the image should exist"
    assert "image/png" in text, "the image should be returned to the chat"


def test_plot_signals_tool_suggests_signal_names():
    result, _, _ = run_model("HelloEV", stop_time=50)
    message = error_text("plot_signals", {"signals": ["V_KPH"], "run": result.run_id})
    assert "Did you mean" in message


def test_png_chart_is_a_reasonable_size():
    from simcore.plot_png import plot_signals_png
    result, _, _ = run_model("HelloEV", stop_time=50)
    png = plot_signals_png(result.run_id, ["v_kph", "x"])
    assert png.suffix == ".png"
    assert 5_000 < png.stat().st_size < 500_000   # small enough to send to a chat
