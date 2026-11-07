"""Shared test settings: tests write their simulation runs to results/test_runs/,
so they don't clutter the real run history that list_runs shows to users and AI."""

from simcore import config

config.RUNS_DIR = config.PROJECT_ROOT / "results" / "test_runs"
