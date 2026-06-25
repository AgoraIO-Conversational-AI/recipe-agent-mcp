# recipe-agent-mcp — Repo Card

> Next.js web client + Python FastAPI backend for an Agora Conversational AI agent that integrates MCP (Model Context Protocol) tool servers. The managed keyless OpenAI vendor emits a tool call; Agora cloud invokes the FastMCP server mounted at `/mcp` in the same backend process; the result flows back to the LLM, which speaks it.

## Identity

| Field          | Value                                                                              |
| -------------- | ---------------------------------------------------------------------------------- |
| Repo           | `AgoraIO-Conversational-AI/recipe-agent-mcp`                                       |
| Type           | `distributed-system` (single repo, two co-located processes)                       |
| Language       | Python 3.10+ (FastAPI + uvicorn + FastMCP) backend + Next.js / React / TypeScript  |
| Deploy Target  | `web/` as Next.js app, `server/` as a publicly reachable FastAPI service (port 8000 serves both token APIs and `/mcp`) |
| Owner          | Agora Conversational AI DevEx                                                      |
| Last Reviewed  | 2026-06-25                                                                         |
| Recipe Role    | `base`                                                                             |
| Recipe Version | `1.0.0`                                                                            |
| Recipe Status  | `experimental`                                                                     |

## L1 — Summaries

The Audience column helps agents prioritise: **Use** = consuming the recipe's behavior, **Maintain** = modifying internals.

| File                                     | Purpose                                                                                      | Audience       |
| ---------------------------------------- | -------------------------------------------------------------------------------------------- | -------------- |
| [01_setup](L1/01_setup.md)               | bun + venv + pip setup, env vars (incl. required `MCP_ENDPOINT`, optional `OPENAI_API_KEY`), commands | Use & Maintain |
| [02_architecture](L1/02_architecture.md) | Single-process topology, MCP tool call flow, `/api/*` rewrite proxy, request lifecycle       | Maintain       |
| [03_code_map](L1/03_code_map.md)         | `web/` and `server/` trees with key file responsibilities                                    | Maintain       |
| [04_conventions](L1/04_conventions.md)   | Python async + FastAPI patterns, Biome, JSON envelope, cascading STT/LLM/TTS, tool transport | Maintain       |
| [05_workflows](L1/05_workflows.md)       | Add a tool, change the LLM/STT/TTS config, add a route, verify, deploy                       | Use            |
| [06_interfaces](L1/06_interfaces.md)     | FastAPI route contracts, rewrites, env vars, MCP server config                               | Use & Maintain |
| [07_gotchas](L1/07_gotchas.md)           | `MCP_ENDPOINT` must be public, transport name mismatch, `PORT` in env, no separate mcp/ dir  | Maintain       |
| [08_security](L1/08_security.md)         | Token007, App Certificate server-only, `/mcp` co-public on same port, CORS                   | Maintain       |

## Recipe Profile

This repo declares `Recipe Role: base`. See [RECIPE.md](RECIPE.md) for extension points, invariants, and stable contracts before changing reusable surfaces.
