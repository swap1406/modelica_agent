"""Tests for the read-only tools added in Milestone 2c-1: catalogue, list_runs,
summarize_signals, and the matching MCP tools."""

import asyncio

import pytest

from simcore import get_model, list_runs, run_simulation, summarize_signals
from simcore import mcp_server


@pytest.fixture(scope="module")
def hello_run():
    run = run_simulation("HelloEV", stop_time=300)
    assert run.status == "success", run.summary()
    return run


def call(tool, args):
    """Call an MCP tool the way an AI app would, and return its JSON text."""
    result = asyncio.run(mcp_server.mcp.call_tool(tool, args))
    return str(result)


def test_catalogue_finds_short_and_full_names():
    assert get_model("mbev")["model"] == "EHPTexamples.EV.MBEV"
    assert get_model("EHPTexamples.EV.MBEV")["name"] == "MBEV"
    with pytest.raises(KeyError, match="Available models"):
        get_model("Tesla")


def test_list_runs_newest_first(hello_run):
    runs = list_runs(model="HelloEV", limit=3)
    assert runs[0]["run_id"] == hello_run.run_id
    assert runs[0]["status"] == "success"


def test_summary_has_end_value_and_value_at_time(hello_run):
    s = summarize_signals(hello_run, ["v_kph"], at_time=0)
    sig = s["signals"][0]
    assert s["run_id"] == hello_run.run_id
    assert sig["start"] == 0 and sig["value_at_time"] == 0
    assert 118 < sig["end"] < 121.5
    assert sig["max"] == sig["end"] and sig["time_of_max_s"] == 300


def test_summary_rejects_time_outside_run(hello_run):
    with pytest.raises(ValueError, match="outside this run"):
        summarize_signals(hello_run, ["v_kph"], at_time=9999)


def test_all_tools_are_listed():
    names = {t.name for t in asyncio.run(mcp_server.mcp.list_tools())}
    assert {"environment_info", "list_models", "list_runs", "list_signals", "read_results"} <= names


def test_list_models_tool_describes_mbev():
    text = call("list_models", {})
    assert "MBEV" in text and "NEDC" in text


def test_read_results_tool_gives_helpful_error(hello_run):
    # Depending on the MCP version, a tool error is raised or returned as an error result.
    try:
        message = call("read_results", {"signals": ["V_KPH"], "run": hello_run.run_id})
    except Exception as exc:
        message = str(exc)
    assert "Did you mean" in message and "v_kph" in message
