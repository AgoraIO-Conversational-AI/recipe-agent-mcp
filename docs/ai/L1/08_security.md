# 08 · Security

> Trust boundaries, secret handling, and auth for the MCP recipe.

## Trust boundaries

| Hop                              | Auth                                                                                    |
| -------------------------------- | --------------------------------------------------------------------------------------- |
| Browser → agent backend          | None in local dev (the `/api/*` rewrite is same-origin).                                |
| Agent backend → Agora cloud      | Token007, generated from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.                      |
| Agora cloud → FastMCP at `/mcp`  | Streamable-HTTP; no auth on the mock. **Add auth before production use.**               |
| Agora cloud → OpenAI             | Agora-managed (keyless); `OPENAI_API_KEY` is optional if supplied by the developer.     |

## Secret handling

- **Server-only secrets:** `AGORA_APP_CERTIFICATE` lives only in `server/.env.local` and never reaches the browser. The browser receives a short-lived token, never the certificate.
- `OPENAI_API_KEY` is optional (Agora manages the key). If supplied, it stays in `server/.env.local` and is passed to the `OpenAI` vendor — it never leaves the server process.
- `server/.env.local` is gitignored; `server/.env.example` ships placeholders only.
- Tokens (`generate_convo_ai_token`) expire after 3600s and are minted per `get_config` call for a concrete non-zero UID.

## `/mcp` is co-public with the token endpoints

Because the FastMCP server is mounted in the same process as the FastAPI app on port 8000, making the backend publicly reachable (required for `MCP_ENDPOINT`) also exposes `/mcp` to the internet. For production use:

- Add request authentication to the FastMCP server, or
- Deploy behind a gateway/proxy that restricts access to `/mcp` by source IP (Agora cloud IP ranges).

## CORS

The backend sets `CORSMiddleware` with `allow_origins=["*"]` — open by design for a local/dev recipe. **Lock this down to known origins before any production deployment.**

## Validation

- `Agent.__init__()` raises `ValueError` for missing `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE`, or `MCP_ENDPOINT` — the server will not boot without them.
- `Agent.start()` rejects empty `channel_name` and non-positive `agent_uid`/`user_uid` before issuing tokens or starting a session.
- Route errors are sanitized: `_log_route_error` logs only non-`None` context; SDK exceptions map to 400/500 without leaking internals to the client.

## Deployment notes

- Set `AGENT_BACKEND_URL` only to a backend you control; the rewrite forwards browser requests there verbatim.
- The published Docker image is **backend-only** (`:8000`, serves both APIs and `/mcp`); it does not bundle secrets.
- `PORT` (default 8000) controls the listening port inside the container; expose it publicly and point `MCP_ENDPOINT` at `<public-url>/mcp`.

## Related Deep Dives

- None.
