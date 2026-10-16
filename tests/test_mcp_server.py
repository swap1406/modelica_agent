"""Checks the MCP server offers the expected tools, without needing an AI app."""

import asyncio

from simcore import mcp_server


def test_environment_info_tool_is_listed_with_a_description():
    tools = asyncio.run(mcp_server.mcp.list_tools())
    names = [t.name for t in tools]
    assert "environment_info" in names
    card = next(t for t in tools if t.name == "environment_info")
    assert "OpenModelica" in card.description


def test_environment_info_tool_returns_versions():
    result = asyncio.run(mcp_server.mcp.call_tool("environment_info", {}))
    assert "OpenModelica" in str(result)
