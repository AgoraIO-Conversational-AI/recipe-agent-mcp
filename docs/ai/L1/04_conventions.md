# 04 · Conventions

> Coding patterns shared across `server/` and `web/`. Follow these to keep local and deployed modes aligned.

## Boundary ownership

- Browser code calls only `/api/*`. Backend placement is hidden behind Next rewrites (`web/next.config.ts`).
- **Never** add `web/app/api/**/route.ts` for agent/token logic — `verify-api-contracts.ts` fails the build if a `route.ts` appears under `app/api`.
- Token generation and the App Certificate stay in `server/`.
- MCP tool logic lives in `server/src/mcp_server.py`. Keep it free of `agora-agents` imports — it is a standalone FastMCP module mounted by `server.py`.

## Backend (Python / FastAPI)

- Async throughout: route handlers are `async def`; the agent uses `AsyncAgora` and `create_async_session`.
- Request bodies are Pydantic models (`StartAgentRequest`, `StopAgentRequest`). Field names are **camelCase** (`channelName`, `rtcUid`, `userUid`) to match the browser client.
- Error mapping is centralized: `_to_http_error()` maps `ValueError → 400`, `RuntimeError → 500`, else 500. `_log_route_error()` logs with safe context + traceback. Raise plain `ValueError`/`RuntimeError`; let the route convert.
- Logging via `logging.getLogger("uvicorn.error")`.
- Env read with `os.getenv`; `.env.local` then `.env` loaded with `override=True`.

## Response envelope

All backend JSON responses use:

```json
{ "code": 0, "msg": "success", "data": { } }
```

`data` is present only when the route returns a payload. The browser client treats `code !== 0` (or missing `data`) as an error.

## MCP tool registration

- Define tools in `server/src/mcp_server.py` by decorating functions with `@mcp.tool()`.
- Each decorated function is automatically registered with the FastMCP instance — no manual registration list.
- `mcp_server.py` must not import `agora-agents`; it is an independent module.

## Vendor configuration

The cascading vendor pipeline is built in `Agent.start()` (`agent.py`):

- **STT:** `DeepgramSTT(model="nova-3", language="en")` — Agora-managed.
- **LLM:** `OpenAI(api_key=..., model=..., system_messages=..., mcp_servers=..., greeting_message=...)` — Agora-managed; keyless by default.
- **TTS:** `MiniMaxTTS(model="speech_2_6_turbo", voice_id="English_captivating_female1")` — Agora-managed.

The `mcp_servers` list is built by `build_mcp_servers()` in `mcp_config.py` and passed to the `OpenAI` vendor. Transport is `streamable_http` (underscore — Agora SDK convention).

## Transport name convention

- **Agora SDK** (`mcp_servers` list): uses `"streamable_http"` (underscore).
- **FastMCP** (`streamable_http_app()`): internally uses `"streamable-http"` (hyphen).
- These are different SDK conventions. Do **not** unify them. See [07_gotchas](07_gotchas.md).

## Turn detection

`turn_detection` is set on `AgoraAgent(...)` directly (not on a vendor):

```python
turn_detection={
    "config": {
        "speech_threshold": 0.5,
        "start_of_speech": {"mode": "vad", "vad_config": {"interrupt_duration_ms": 160, "prefix_padding_ms": 300}},
        "end_of_speech": {"mode": "vad", "vad_config": {"silence_duration_ms": 480}},
    }
}
```

`enable_tools: True` must be set in `advanced_features` for MCP tool calling to work.

## Web (TypeScript / Next.js)

- Lint/format with Biome (`bun run lint`, `bun run lint:fix` in `web/`).
- RTC client creation must be StrictMode-safe (strict mode is on).
- Transcript speaker mapping uses real UIDs (`normalizeTranscript` maps `uid === '0'` to the local UID).
- API client lives in `src/services/api.ts`; UI never calls `fetch` to the backend directly.

## Testing approach

- Backend: `pytest` in `server/`, standalone — `conftest.py` fakes env and SDK session, so no cloud or real creds are needed.
- Web: contract/proxy scripts under `web/scripts/` run without live Agora calls.
- Run the **narrowest** relevant verify command before finishing (see [05_workflows](05_workflows.md)).

## Doc upkeep

When you change request/response contracts, env vars, or workflow, update the web client, backend, contract checks, README, **and** the matching `docs/ai/L1/` file together, then bump `Last Reviewed` in [L0](../L0_repo_card.md).

## Related Deep Dives

- [mcp_tool_wiring](L2/mcp_tool_wiring.md) — `build_mcp_servers()`, transport conventions, tool registration, and adding tools.
