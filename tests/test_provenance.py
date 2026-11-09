"""Provenance: runs record whether the model sources were the approved ones."""

import json

from simcore import config, provenance, run_simulation


def test_current_model_sources_match_the_manifest():
    # Fails if a model file was edited without deliberately updating the manifest.
    result = provenance.check()
    assert result["status"] == "approved", result


def test_runs_record_provenance():
    run = run_simulation("HelloEV", stop_time=10)
    record = json.loads((config.RUNS_DIR / run.run_id / "run.json").read_text())
    assert record["provenance"]["model_modified"] is False


def test_an_edited_model_file_is_detected(tmp_path, monkeypatch):
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "Car.mo").write_text("model Car parameter Real ratio = 6; end Car;")
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(provenance, "SOURCE_DIRS", ["models"])
    provenance.write_manifest()
    assert provenance.check()["model_modified"] is False
    (tmp_path / "models" / "Car.mo").write_text("model Car parameter Real ratio = 9; end Car;")
    result = provenance.check()
    assert result["model_modified"] is True
    assert result["changed"] == ["models/Car.mo"]
