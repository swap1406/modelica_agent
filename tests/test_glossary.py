"""Tests for Milestone 2d: signal glossary, readable units, known harmless
messages, and the one-NEDC standard run for MBEV."""

import asyncio

from simcore import catalog, glossary, mcp_server, run_model, summarize_signals


def test_motor_torque_maps_to_actual_torque_not_the_request():
    hits = glossary.find("MBEV", "motor torque")
    assert hits[0]["signal"] == "eleDrive.tauElectrical"


def test_battery_current_has_a_sign_convention():
    hit = glossary.find("MBEV", "battery current")[0]
    assert hit["signal"] == "batt1.n.i"
    assert "positive = discharging" in hit["meaning"]


def test_short_signal_names_do_not_match_everything():
    # HelloEV's speed signal is just "v": a search for "distance" must not return it
    assert [g["signal"] for g in glossary.find("HelloEV", "distance")] == ["x"]


def test_every_glossary_file_is_complete_and_approved():
    from simcore import units
    for model in ("MBEV", "FirstEV", "HelloEV"):
        assert glossary.approved_by(model), model
        for g in glossary.entries(model):
            assert g["signal"] and g["unit"] and g["meaning"], (model, g["term"])
            if g["display_unit"]:      # every requested display unit must be convertible
                assert units.display_unit(g["unit"], g["display_unit"]) == g["display_unit"], g["term"]


def test_models_without_a_glossary_still_work():
    assert glossary.entries("SomeOtherModel") == []
    assert glossary.find("SomeOtherModel", "speed") == []


def test_default_display_units_work_for_any_model():
    from simcore import units
    assert units.display_unit("rad/s") == "rpm"
    assert units.display_unit("A") is None                  # amps are already readable
    assert units.display_unit("1") is None                  # a ratio isn't always a percentage...
    assert units.display_unit("1", preferred="%") == "%"    # ...unless a glossary says so
    assert abs(units.convert(300, "K", "°C") - 26.85) < 1e-9


def test_mbev_standard_run_is_one_nedc():
    assert catalog.get_model("MBEV")["default_stop_time_s"] == 1180


def test_known_harmless_message_is_separated():
    entry = catalog.get_model("MBEV")
    real, known = catalog.classify_messages(
        entry, ["Initialization problem is structural singular. Please, check the initial conditions.",
                "Something really broke"])
    assert real == ["Something really broke"]
    assert "harmless" in known[0]["explanation"]


def test_summary_shows_readable_units():
    result, _, _ = run_model("HelloEV", stop_time=300)
    sig = summarize_signals(result, ["v"])["signals"][0]
    assert sig["display"]["unit"] == "km/h"
    assert abs(sig["display"]["end"] - sig["end"] * 3.6) < 0.01


def test_list_signals_tool_recommends_glossary_signal():
    result, _, _ = run_model("HelloEV", stop_time=50)
    text = str(asyncio.run(mcp_server.mcp.call_tool("list_signals", {"run": result.run_id, "search": "speed"})))
    assert "recommended" in text and "vehicle speed" in text
