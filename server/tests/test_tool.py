import asyncio
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import mcp_server as srv  # noqa: E402

def test_current_time_message():
    msg = srv.current_time_message()
    assert "current server time" in msg.lower()
    assert re.search(r"\d{2}:\d{2}:\d{2}", msg)


def test_current_time_message_supports_12_hour_format():
    msg = srv.current_time_message("12-hour")

    assert "current server time" in msg.lower()
    assert " AM." in msg or " PM." in msg


def test_get_time_exposes_enum_parameter_schema():
    tools = asyncio.run(srv.mcp.list_tools())
    get_time = next(tool for tool in tools if tool.name == "get_time")

    assert get_time.inputSchema["properties"]["time_format"]["enum"] == [
        "12-hour",
        "24-hour",
    ]
