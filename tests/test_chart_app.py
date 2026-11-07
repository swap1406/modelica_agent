"""Tests for the in-chat interactive chart (MCP App): downsampling keeps peaks,
the data stays small, and plot_signals is linked to the chart page."""

import asyncio
import json

import numpy as np

from simcore import mcp_server, run_model
from simcore.plot_data import chart_data, downsample_indices


def test_downsampling_keeps_the_peak():
    y = np.sin(np.linspace(0, 20, 14000))
    y[7777] = 5.0                                   # a single sharp spike
    idx = downsample_indices([y], max_buckets=400)
    assert len(idx) <= 2 * 400 + 2
    assert 7777 in idx, "the spike must survive downsampling"


def test_chart_data_is_small_and_complete():
    result, _, _ = run_model("HelloEV", stop_time=300)
    d = chart_data(result.run_id, ["v_kph", "x"])
    assert d["run_id"] == result.run_id
    assert len(d["panels"]) == 2                    # km/h and m: different units, two panels
    assert len(d["t"]) == len(d["panels"][0]["series"][0]["y"])
    assert len(json.dumps(d)) < 100_000             # well under what the chat accepts


def test_plot_signals_is_linked_to_the_chart_page():
    tools = {t.name: t for t in asyncio.run(mcp_server.mcp.list_tools())}
    assert "ui://modelica_agent/plot.html" in str(tools["plot_signals"].meta)
    page = str(list(asyncio.run(mcp_server.mcp.read_resource("ui://modelica_agent/plot.html"))))
    assert "profile=mcp-app" in page and "uPlot" in page
