import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import mcp_config as cfg  # noqa: E402

def test_build_mcp_servers():
    s = cfg.build_mcp_servers("https://x.ngrok-free.dev/mcp")
    assert s == [{"name": "time", "endpoint": "https://x.ngrok-free.dev/mcp", "transport": "streamable_http"}]
