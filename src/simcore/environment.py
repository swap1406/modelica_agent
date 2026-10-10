"""Report what simcore is running on: useful for debugging and for every run record."""

import platform
import subprocess


def _omc_version() -> str:
    """Ask the OpenModelica compiler for its version, e.g. 'OpenModelica 1.27.1'."""
    try:
        out = subprocess.run(["omc", "--version"], capture_output=True, text=True, timeout=30)
        return out.stdout.strip() or out.stderr.strip()
    except FileNotFoundError:
        return "not found (are you running inside the Docker container?)"


def environment_info() -> dict:
    """Return the versions of everything simcore depends on."""
    import pandas
    import plotly

    from simcore import __version__

    return {
        "simcore": __version__,
        "python": platform.python_version(),
        "openmodelica": _omc_version(),
        "pandas": pandas.__version__,
        "plotly": plotly.__version__,
        "machine": platform.machine(),
    }
