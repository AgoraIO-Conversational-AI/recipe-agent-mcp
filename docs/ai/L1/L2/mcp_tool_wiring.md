# Deep Dive — MCP Tool Wiring

**When to Read This:** You are adding or changing a tool in the MCP server, debugging why tool calls never reach `/mcp`, changing `MCP_ENDPOINT`, or trying to understand the transport chain between the managed OpenAI LLM, Agora cloud, and the FastMCP server. For the high-level picture, start at [02_architecture](../02_architecture.md).

This recipe connects an Agora-managed keyless OpenAI LLM to a FastMCP tool server mounted in the same backend process. When the LLM emits a tool call, Agora cloud — not the backend process — issues a streamable-HTTP POST to `MCP_ENDPOINT`. The FastMCP server handles it and returns the result.

## The builder

`build_mcp_servers(endpoint, name="time") → List[Dict[str, str]]` in `server/src/mcp_config.py`:

```python
return [{"name": name, "endpoint": endpoint, "transport": "streamable_http"}]
```

This list is passed as `mcp_servers=` to the `OpenAI` vendor in `Agent.start()`:

```python
llm = OpenAI(
    api_key=self.openai_api_key,        # optional (Agora manages it)
    model=self.openai_model,             # OPENAI_MODEL, default gpt-4o-mini
    system_messages=[{"role": "system", "content": "..."}],
    mcp_servers=build_mcp_servers(self.mcp_endpoint),
    greeting_message=self.greeting,
)
```

`mcp_config.py` has no `agora-agents` import — it is a pure builder and independently testable.

## Transport name convention

| SDK side | Transport string | Why |
| --- | --- | --- |
| Agora `mcp_servers` list | `"streamable_http"` (underscore) | Agora SDK convention |
| FastMCP `streamable_http_app()` | `"streamable-http"` (hyphen) | MCP SDK convention |

**Do not unify them.** They operate at different layers. `test_mcp_config.py` asserts the correct Agora-side string.

## FastMCP server (in-process)

`server/src/mcp_server.py`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("recipe-agent-mcp")

@mcp.tool()
def get_time() -> str:
    """Return the current server time. Call this when the user asks what time it is."""
    msg = current_time_message()
    return msg
```

Every `@mcp.tool()`-decorated function is automatically registered. The module must not import `agora-agents`.

## How the MCP server is mounted

In `server/src/server.py`:

```python
_mcp_asgi = mcp_server.mcp.streamable_http_app()

@asynccontextmanager
async def _lifespan(_app):
    async with mcp_server.mcp.session_manager.run():
        yield

app = FastAPI(lifespan=_lifespan)
# ... routes ...
app.mount("/", _mcp_asgi)   # FastMCP's /mcp path lands at /mcp on the server
```

The `mount("/", ...)` at the end means FastMCP's own `/mcp` path is exposed at `/mcp` on the server (no double-slash). Agora cloud reaches it at `<public-url>/mcp`.

## `enable_tools` requirement

MCP tool calling requires `enable_tools: True` in `AgoraAgent(advanced_features=...)`:

```python
agora_agent = AgoraAgent(
    ...
    advanced_features={"enable_rtm": True, "enable_tools": True},
    ...
)
```

Omitting `enable_tools` silently prevents tool calls from being dispatched to `MCP_ENDPOINT`.

## Adding a tool

1. Define the function in `server/src/mcp_server.py` and decorate it with `@mcp.tool()`.
2. Put testable logic in a pure helper function (see `current_time_message()` as example).
3. Add a test in `server/tests/test_tool.py` for the helper.
4. Verify: `cd server && pytest tests -v`.

No change to `mcp_config.py`, `agent.py`, or `server.py` is needed — all tools served at the same `MCP_ENDPOINT` are automatically available to the LLM.

## Adding a second MCP server

`build_mcp_servers()` returns a list. To add a second server:

```python
return [
    {"name": "time", "endpoint": endpoint, "transport": "streamable_http"},
    {"name": "weather", "endpoint": other_endpoint, "transport": "streamable_http"},
]
```

Update `mcp_config.py` and extend `test_mcp_config.py` accordingly.

## Debugging tool call routing

If the agent starts but never responds to tool-triggering queries:

1. `MCP_ENDPOINT` is not public — check with `bun run doctor:local`.
2. `enable_tools: True` is missing from `advanced_features` — check `agent.py`.
3. The LLM system prompt does not instruct the model to call the tool — check `system_messages` in `Agent.start()`.
4. The FastMCP server failed to mount — check server logs at startup.

## Related L1

- [02_architecture](../02_architecture.md) · [04_conventions](../04_conventions.md) · [06_interfaces](../06_interfaces.md) · [07_gotchas](../07_gotchas.md)
