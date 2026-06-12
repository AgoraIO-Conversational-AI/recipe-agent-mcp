"""MCP server (streamable-HTTP) exposing one mock tool. Agora cloud calls this
when the LLM emits a tool call. Replace get_time with your own tools.

This module is mounted in-process by server.py at /mcp — it is not run
standalone. Add your tools here; each @mcp.tool()-decorated function is
automatically registered with the FastMCP instance."""
import datetime

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("recipe-agent-mcp")


def current_time_message() -> str:
    """Pure, testable helper: the message the get_time tool returns."""
    now = datetime.datetime.now().strftime("%H:%M:%S")
    return f"The current server time is {now}."


@mcp.tool()
def get_time() -> str:
    """Return the current server time. Call this when the user asks what time it is."""
    msg = current_time_message()
    print(f"[MCP TOOL CALLED] get_time -> {msg}", flush=True)
    return msg
