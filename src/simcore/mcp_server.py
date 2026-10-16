"""MCP server: exposes simcore functions as tools for AI assistants.

How it runs: an AI app (e.g. Claude Desktop) starts this program inside our
Docker container and talks to it over stdio (standard input/output).

Important: stdout is the message channel to the AI app. Never print() to it,
or the app receives garbage. Use the logger below, which writes to stderr.

Start it with:  python3 -m simcore.mcp_server
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from simcore.environment import environment_info as _environment_info

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("simcore.mcp")

# The name AI apps show for this server.
mcp = FastMCP("modelica_agent")


# Each @mcp.tool() function becomes one "tool card" the AI sees:
#   name        = the function name
#   description = the docstring
#   inputs      = the function's parameters and their types
@mcp.tool()
def environment_info() -> dict:
    """Report the software versions the simulation environment is running:
    OpenModelica, Python, simcore, pandas and plotly. Use this when the user
    asks which versions are installed, or to check the setup is working."""
    log.info("tool called: environment_info")
    return _environment_info()


def main() -> None:
    log.info("modelica_agent MCP server starting (stdio)")
    mcp.run()  # default transport: stdio


if __name__ == "__main__":
    main()
