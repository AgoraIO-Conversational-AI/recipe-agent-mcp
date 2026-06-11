"""Pure builder — no agora_agent import."""
from typing import Dict, List


def build_mcp_servers(endpoint: str, name: str = "time") -> List[Dict[str, str]]:
    return [{"name": name, "endpoint": endpoint, "transport": "streamable_http"}]
