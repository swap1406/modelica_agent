"""Tests for run_simulation(). Run with:
    docker compose run --rm om python3 -m pytest -v
"""

import json
from pathlib import Path

import pandas as pd

from simcore import run_simulation
from simcore.run import _sort_messages


def test_hello_ev_runs_and_reaches_expected_speed():
    """HelloEV: constant drive force vs drag. Speed must approach the hand-calculated 121 km/h."""
    run = run_simulation("HelloEV", stop_time=300)

    assert run.status == "success", run.summary()
    assert run.errors == []

    run_dir = Path(run.run_dir)
    for name in ("run.mos", "console.txt", "run.json", "HelloEV_res.csv", "HelloEV.log"):
        assert (run_dir / name).exists(), f"missing {name}"
    assert not (run_dir / "build").exists(), "build folder should be cleaned up after success"
    assert run.build_dir is None

    record = json.loads((run_dir / "run.json").read_text())
    assert record["model"] == "HelloEV" and record["status"] == "success"

    final_speed_kph = pd.read_csv(run.result_file)["v_kph"].iloc[-1]
    assert 118 < final_speed_kph < 121.5   # 119.6 km/h measured on 6 Oct 2026


def test_keep_build_keeps_generated_files():
    """With keep_build=True the generated C code stays in build/ for debugging."""
    run = run_simulation("HelloEV", stop_time=10, keep_build=True)
    assert run.status == "success", run.summary()
    build = Path(run.build_dir)
    assert build.is_dir()
    assert list(build.glob("*.c")), "expected generated C files in build/"


def test_unknown_model_fails_cleanly():
    """A model that doesn't exist must give status 'failed' with an error, not crash.
    Build files are kept automatically on failure."""
    run = run_simulation("NoSuchModel", stop_time=1)
    assert run.status == "failed"
    assert run.result_file is None
    assert run.errors, "expected at least one error message"
    assert run.build_dir is not None and Path(run.build_dir).is_dir()


def test_messages_are_sorted_and_deduplicated():
    output = '\n'.join([
        '"Warning: The initial conditions are over specified.',
        '         mass.v = $START.mass.v.',
        'Error: Initialization problem is structural singular.',
        'Warning: The initial conditions are over specified.',
        '         mass.v = $START.mass.v.',
        '"Notification: Modelica 4.1.0 is used instead"',
    ])
    errors, warnings, notes = _sort_messages(output)
    assert len(errors) == 1 and "structural singular" in errors[0]
    assert len(warnings) == 1 and "mass.v" in warnings[0]
    assert len(notes) == 1
