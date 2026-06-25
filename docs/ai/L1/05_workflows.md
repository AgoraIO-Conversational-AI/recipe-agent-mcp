# 05 · Workflows

> Step-by-step guides for the common changes in this recipe. Each ends with the narrowest verify command to run.

## Add a new MCP tool

1. Open `server/src/mcp_server.py`.
2. Decorate a new function with `@mcp.tool()`. The FastMCP instance registers it automatically.
3. Add a test in `server/tests/test_tool.py` for the pure helper logic (keep tool functions thin; put business logic in a testable helper like `current_time_message()`).
4. Verify: `cd server && pytest tests -v`.

> No change to `mcp_config.py`, `agent.py`, or `server.py` is needed — all tools in `mcp_server.py` are served at the same `MCP_ENDPOINT`.

## Change the LLM model or greeting

1. Model: set `OPENAI_MODEL` (default `gpt-4o-mini`) in `server/.env.local`.
2. Greeting: set `AGENT_GREETING` in `server/.env.local` or edit the default `AGENT_GREETING` constant in `server/src/agent.py`.
3. System prompt: edit `system_messages` in `Agent.start()` (`agent.py`).
4. Verify: `bun run verify:backend` (compile) + `cd server && pytest tests -v`.

## Change STT or TTS vendors

1. Edit the `stt =` or `tts =` lines in `Agent.start()` (`agent.py`). All vendors are Agora-managed.
2. Verify: `bun run verify:backend` + `cd server && pytest tests -v`.

## Add or change a browser-facing route

1. Add the FastAPI handler in `server/src/server.py` (return the `{ code, msg, data }` envelope).
2. Add the `/api/<name>` → `/<name>` mapping in `web/next.config.ts` `rewrites()`.
3. Add a client helper in `web/src/services/api.ts`.
4. Extend `web/scripts/verify-api-contracts.ts` with the new path + envelope assertions.
5. Verify: `bun run verify:web` (and `bun run verify:web:proxy` for proxy boundary).

## Add your own OpenAI API key

By default Agora manages the OpenAI key (keyless). To supply your own:

1. Set `OPENAI_API_KEY=sk-...` in `server/.env.local`.
2. The `Agent.__init__()` picks it up via `os.getenv("OPENAI_API_KEY")` and passes it to the `OpenAI` vendor.
3. No code change required.

## Run / debug locally

```bash
ngrok http 8000                    # expose backend + MCP server publicly first
# set MCP_ENDPOINT in server/.env.local
bun run dev                        # both processes
bun run doctor:local               # check creds + .env.local + MCP_ENDPOINT
```

## Verify before finishing

| Change touches…              | Run                                                              |
| ---------------------------- | ---------------------------------------------------------------- |
| Web only                     | `bun run verify:web`                                             |
| Backend logic / vendors      | `bun run verify:backend` + `cd server && pytest tests -v`        |
| Route/proxy boundary         | `bun run verify:web:proxy`                                       |
| Anything end-to-end (local)  | `bun run verify:local`                                           |

## Deploy

1. Deploy `web/` as a Next.js app.
2. Deploy `server/` as a single publicly reachable FastAPI process (serves both token APIs and `/mcp` on port 8000). The published image is `ghcr.io/AgoraIO-Conversational-AI/recipe-agent-mcp` on `v*` tags.
3. Set `MCP_ENDPOINT=<public-url>/mcp` in the backend environment so Agora cloud can call the tool endpoint.
4. Set `AGENT_BACKEND_URL` in the web deployment so rewrites reach the backend.
5. Review the co-public caveat in [08_security](08_security.md) — `/mcp` is exposed on the same port.

## Related Deep Dives

- [mcp_tool_wiring](L2/mcp_tool_wiring.md) — `build_mcp_servers()` details, transport, adding tools.
- [session_lifecycle](L2/session_lifecycle.md) — client-side join/renewal/teardown.
