# adk-agent-test

AI agent with web browsing and research tools (OpenAI Agents SDK).

## Quick start

```bash
uv sync
uv run python -m adk_agent_test.main research "What is Python 3.12?" --mock
```

## Docker development (auto-restart on save)

Requires Docker Compose 2.22+.

1. Create `.env` from `.env.example` and set `OPENAI_API_KEY`.

2. Start dev with auto-restart on file save (use `watch` with the dev profile):

   ```bash
   docker compose --profile dev watch
   ```

3. Edit code in `src/` and save. Docker Compose restarts the container and runs the research agent.

4. Customize via env:

   ```bash
   DEV_QUERY="Your question here" docker compose --profile dev watch
   ```

5. For real tools (no mock), set `DEV_MOCK=0`.

## Docker one-off run

```bash
# With mock (fast, no API calls for browse)
docker compose --profile dev run --rm agent-dev uv run python -m adk_agent_test.main research "Your question" --mock

# With real tools
docker compose --profile dev run --rm agent-dev uv run python -m adk_agent_test.main research "Your question"
```

## Commands

| Command | Description |
|---------|-------------|
| `research "..." --mock` | Run research agent (mock tools) |
| `research "..."` | Run research agent (real tools) |
| `run "message"` | Simple chat with assistant |
| `hello` | Print hello |
