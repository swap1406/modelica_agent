"""simcore: a small, generic library to run Modelica simulations in OpenModelica,
read their results and plot signals.

The same functions are used directly from Python and, later, exposed as MCP
tools for AI assistants.
"""

__version__ = "0.1.0"

from simcore.environment import environment_info  # noqa: E402,F401
from simcore.run import RunResult, run_simulation  # noqa: E402,F401
from simcore.results import Signal, find_run, list_signals, read_results  # noqa: E402,F401
from simcore.plotting import plot_signals  # noqa: E402,F401
