# 07 · Gotchas

> Non-obvious pitfalls specific to the MCP recipe. Read before changing the agent, MCP config, env, or verify scripts.

## `MCP_ENDPOINT` must be publicly reachable

Agora cloud — not the browser, not the backend — calls the MCP endpoint to invoke tools. `localhost` or RFC-1918 addresses will not work. For local development, use a tunnel (`ngrok http 8000`). `doctor:local` warns if `MCP_ENDPOINT` contains `localhost` or `127.0.0.1`.

`MCP_ENDPOINT` is validated in `Agent.__init__()` — the server will **not start** if it is unset (raises `ValueError` at boot, unlike the `OPENAI_API_KEY` check in the realtime recipe).

## Transport name mismatch between Agora SDK and FastMCP

- Agora's `mcp_servers` expects transport `"streamable_http"` (underscore).
- FastMCP's `streamable_http_app()` uses `"streamable-http"` (hyphen) internally.

Do **not** unify these — they are different SDK conventions. `test_mcp_config.py` asserts the correct Agora-side name.

## `/mcp` is co-public on the same port as the token endpoints

Because the FastMCP server is mounted in the same process as the FastAPI app, exposing port 8000 publicly also exposes `/mcp`. For production use, add authentication to the MCP endpoint or deploy behind a gateway that restricts `/mcp` access to Agora cloud IPs.

## No separate `mcp/` service or second port

Unlike some early versions of this recipe, the FastMCP server is mounted in-process. Do **not** reintroduce a standalone `mcp/` directory, a second Python service, or a separate tunnel for `/mcp`. One port, one tunnel, one container.

## `enable_tools: True` is required in `advanced_features`

MCP tool calling requires `advanced_features={"enable_rtm": True, "enable_tools": True}` on `AgoraAgent(...)`. Omitting `enable_tools` silently prevents tool calls from being routed to `MCP_ENDPOINT`.

## Do not put `PORT` in `server/.env.example`

`verify:local:fastapi` injects a random `PORT` and loads env with `load_dotenv(override=True)`. A `PORT` line in `.env.example` (copied to `.env.local`) would clobber the injected port and break the smoke test.

## Keep `/api/*` ownership in rewrites

Adding `web/app/api/**/route.ts` for agent/token logic breaks the boundary — `verify-api-contracts.ts` explicitly fails if a `route.ts` exists under `app/api`. Token logic belongs in `server/`.

## `mcp_server.py` must not import `agora-agents`

`mcp_server.py` is a standalone FastMCP module. Importing `agora-agents` there creates a dependency cycle and prevents isolated testing. Keep it import-clean; `mcp_config.py` is also free of `agora-agents` imports by design.

## camelCase request fields

`StartAgentRequest` uses `channelName`, `rtcUid`, `userUid` (camelCase) to match the browser client. Renaming one side without the other breaks the contract tests.

## Local calls under a global proxy

Global proxies (Clash, etc.) can break `localhost`/RFC-1918 traffic. Configure the proxy to send `127.0.0.1`, `localhost`, and private ranges DIRECT, or use `socksio` (in `requirements.txt`) plus `all_proxy` to route the backend through SOCKS.

## Related Deep Dives

- [mcp_tool_wiring](L2/mcp_tool_wiring.md) — correct MCP wiring and transport details.
