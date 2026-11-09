"""Fixes for the findings of the 8 Nov 2026 evaluation baseline (eval/results/)."""

import asyncio
import json
import shutil

from simcore import config, glossary, list_runs, mcp_server


def test_list_runs_does_not_count_known_harmless_message_as_error():
    # A fake MBEV run record with only the known start-up message
    folder = config.RUNS_DIR / "29991231-235959_MBEV"
    folder.mkdir(parents=True, exist_ok=True)
    try:
        (folder / "run.json").write_text(json.dumps({
            "run_id": folder.name, "model": "EHPTexamples.EV.MBEV", "status": "success",
            "errors": ["Initialization problem is structural singular. Please, check the initial conditions."],
        }))
        run = list_runs(model="MBEV", limit=1)[0]
        assert run["errors"] == 0
        assert run["known_harmless_messages"] == 1
    finally:
        shutil.rmtree(folder)


def test_power_limits_are_unambiguous():
    motor = glossary.find("MBEV", "motor power")[0]
    assert "22 kW" in motor["meaning"] and "electrical" in motor["meaning"]


def test_run_simulation_returns_warning_texts():
    text = str(asyncio.run(mcp_server.mcp.call_tool("run_simulation", {"model": "HelloEV", "stop_time": 10})))
    assert "'warnings'" in text or '"warnings"' in text
    assert "warnings_count" not in text
