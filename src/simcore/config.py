"""Project settings for simcore. Paths are as seen inside the Docker container,
where the project folder is mounted at /work (see docker-compose.yml)."""

from pathlib import Path

# The project folder (the container's working directory).
PROJECT_ROOT = Path("/work")

# Every simulation gets its own dated folder in here.
RUNS_DIR = PROJECT_ROOT / "results" / "runs"

# Modelica Standard Library version requested by our models.
# OpenModelica may use a compatible newer one (currently 4.1.0).
MSL_VERSION = "4.0.0"

# Modelica files/libraries loaded before every simulation, in this order.
# Add a line here to make a new library available to run_simulation().
LIBRARY_FILES = [
    PROJECT_ROOT / "third_party" / "EHPTlib" / "EHPTlib" / "package.mo",
    PROJECT_ROOT / "third_party" / "EHPTexamples" / "EHPTexamples" / "package.mo",
]

# Our own models: every .mo file in this folder is loaded too (e.g. HelloEV).
MODELS_DIR = PROJECT_ROOT / "models"
