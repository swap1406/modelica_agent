"""Tests for plot_signals(). Run with:
    docker compose run --rm om python3 -m pytest -v
"""

import pytest

from simcore import plot_signals, run_simulation
from simcore.plotting import _panels


@pytest.fixture(scope="module")
def hello_run():
    run = run_simulation("HelloEV", stop_time=300)
    assert run.status == "success", run.summary()
    return run


def test_plot_creates_html_in_run_folder(hello_run):
    path = plot_signals(hello_run, ["v_kph", "F_aero", "F_roll"])
    assert path.exists() and path.suffix == ".html"
    assert path.parent.name == "plots"
    html = path.read_text()
    assert "plotly" in html.lower()
    assert "v_kph" in html and "F_aero" in html
    assert "Plotly.Fx.hover" in html, "linked cursor script should be embedded"


def test_signals_with_same_unit_share_a_panel():
    units = {"a.v": "m/s", "b.f": "N", "c.f": "N", "soc": ""}
    assert _panels(["a.v", "b.f", "c.f", "soc"], units) == [["a.v"], ["b.f", "c.f"], ["soc"]]


def test_unknown_signal_gives_helpful_error(hello_run):
    with pytest.raises(KeyError, match="v_kph"):
        plot_signals(hello_run, ["V_kph"])
