"""Tests for list_signals() and read_results(). Run with:
    docker compose run --rm om python3 -m pytest -v
"""

import pytest

from simcore import list_signals, read_results, run_simulation


@pytest.fixture(scope="module")
def hello_run():
    """One fresh HelloEV run shared by the tests in this file."""
    run = run_simulation("HelloEV", stop_time=300)
    assert run.status == "success", run.summary()
    return run


def test_list_signals_has_descriptions(hello_run):
    signals = {s.name: s for s in list_signals(hello_run)}
    assert "v_kph" in signals
    assert signals["v_kph"].description == "Vehicle speed [km/h]"
    assert signals["v"].kind == "state"            # v has a derivative: der(v)
    assert "m" not in signals                        # parameters (fixed inputs) aren't in the results file
    assert not any(name.startswith("der(") for name in signals), "derivatives hidden by default"


def test_list_signals_search_matches_description(hello_run):
    names = [s.name for s in list_signals(hello_run, search="speed")]
    assert set(names) == {"v", "v_kph"}


def test_read_results_returns_only_requested_signals(hello_run):
    data = read_results(hello_run, ["v_kph", "x"])
    assert list(data.columns) == ["time", "v_kph", "x"]
    assert data["time"].is_monotonic_increasing
    assert 118 < data["v_kph"].iloc[-1] < 121.5


def test_latest_finds_this_run(hello_run):
    data = read_results("latest:HelloEV", ["v_kph"])
    assert len(data) > 100


def test_unknown_signal_suggests_the_right_one(hello_run):
    with pytest.raises(KeyError, match="v_kph"):
        read_results(hello_run, ["V_KPH"])
