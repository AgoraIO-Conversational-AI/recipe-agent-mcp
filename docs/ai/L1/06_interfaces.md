# 06 · Interfaces

> Boundary contracts: backend routes, the `/api/*` rewrite map, env vars, the response envelope, and the MCP server config.

## Backend routes (port 8000)

The browser calls the first three as `/api/<name>`; Next rewrites to the backend `/<name>`. Agora cloud calls `/mcp` directly at `MCP_ENDPOINT`.

### `GET /get_config`

- Query (optional): `channel?: string`, `uid?: int` (≤ 0 or missing → backend generates one).
- Returns `data`: `{ app_id, token, uid (string), channel_name, agent_uid (string) }`.
- Token is a Token007 RTC+RTM token, expiry 3600s, for a concrete non-zero UID.

### `POST /startAgent`

- Body: `{ channelName: string, rtcUid: int, userUid: int, parameters?: object }`.
  - `parameters.output_audio_codec?: string` is the only honored parameter field.
- Returns `data`: `{ agent_id, channel_name, status: "started" }`.
- 400 if `AGORA_APP_ID`/`AGORA_APP_CERTIFICATE`/`MCP_ENDPOINT` not set (server won't boot), or if `channelName`/`rtcUid`/`userUid` are invalid.

### `POST /stopAgent`

- Body: `{ agentId: string }`.
- Returns `{ code: 0, msg: "success" }` (no `data`).

### `POST /mcp` (streamable-HTTP)

- Called by Agora cloud, not the browser.
- Accepts MCP streamable-HTTP requests (tool calls, tool results).
- Served by the FastMCP session manager mounted in-process.

## Response envelope

```json
{ "code": 0, "msg": "success", "data": { } }
```

`data` omitted when the route has no payload. Non-zero `code` or missing `data` = error on the client side.

## Rewrite map (`web/next.config.ts`)

| Browser path        | Backend destination |
| ------------------- | ------------------- |
| `/api/get_config`   | `/get_config`       |
| `/api/startAgent`   | `/startAgent`       |
| `/api/stopAgent`    | `/stopAgent`        |

`rewrites()` returns `[]` when `AGENT_BACKEND_URL` is unset. The contract is asserted by `verify-api-contracts.ts` and exercised by `verify-local-proxy.ts`.

## Browser API client (`web/src/services/api.ts`)

- `getConfig({ channel?, uid? }) → GetConfigResponse`
- `startAgent(channelName, rtcUid, userUid) → agent_id`
- `stopAgent(agentId) → void`

## Environment variables

| Variable                | Scope              | Required | Default                    |
| ----------------------- | ------------------ | :------: | -------------------------- |
| `AGORA_APP_ID`          | backend            |    ✅    | —                          |
| `AGORA_APP_CERTIFICATE` | backend            |    ✅    | —                          |
| `MCP_ENDPOINT`          | backend            |    ✅    | — (must be public URL)     |
| `OPENAI_MODEL`          | backend            |          | `gpt-4o-mini`              |
| `OPENAI_API_KEY`        | backend            |          | — (Agora manages it)       |
| `AGENT_GREETING`        | backend            |          | `Hi! Ask me what time it is.` |
| `AGENT_BACKEND_URL`     | web (deploy)       |   ✅\*   | `http://localhost:8000` (dev) |
| `PORT`                  | backend (env only) |          | `8000` — do **not** put in `.env.example` |

\* Required wherever the web app is deployed; rewrites are empty without it.

## MCP server config (`mcp_config.py`)

`build_mcp_servers(endpoint, name="time") → List[Dict[str, str]]` produces:

```python
[{"name": name, "endpoint": endpoint, "transport": "streamable_http"}]
```

This list is passed as `mcp_servers=` to the `OpenAI` vendor in `Agent.start()`. Transport is `"streamable_http"` (underscore — Agora SDK convention; not to be confused with FastMCP's `"streamable-http"` with hyphen).

## `OpenAI` vendor config (`agent.py`)

`OpenAI(api_key, model, system_messages, mcp_servers, greeting_message)` produces a managed vendor whose effective config includes:

- Agora-managed keyless OpenAI LLM (`api_key` is optional).
- `mcp_servers` list pointing at `MCP_ENDPOINT`.
- `enable_tools: True` set in `AgoraAgent(advanced_features=...)`.

## Related Deep Dives

- [mcp_tool_wiring](L2/mcp_tool_wiring.md) — every field in `build_mcp_servers()` and the session options around it.
