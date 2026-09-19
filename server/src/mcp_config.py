"""Typed MCP server configuration builder."""
from typing import List

from agora_agent.agentkit import McpServerConfig


def build_mcp_servers(endpoint: str, name: str = "time") -> List[McpServerConfig]:
    # The SDK supplies streamable_http when transport is omitted.
    return [McpServerConfig(name=name, endpoint=endpoint)]
