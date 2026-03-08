"""Research agent with streaming, tools, and cost tracking."""

import asyncio
import json
from typing import Optional

from agents import Agent, ItemHelpers, ModelSettings, Runner, function_tool
from openai import AsyncOpenAI

from .config import SETTINGS, async_client, is_mock_tools
from .cost_tracker import CostTracker
from .tools.powerpoint import create_powerpoint
from .tools.web import browse_page, execute_python, web_search


def _format_tool_call_reasoning(name: str, arguments: str) -> str:
    """Format a one-line human-readable summary of what the tool is doing."""
    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError:
        return f"[Tool: {name}]"
    if name == "web_search":
        q = args.get("query", "")
        n = args.get("num_results", 10)
        return f'[Tool: web_search] Searching: "{q[:60]}{"..." if len(q) > 60 else ""}" (up to {n} results)'
    if name == "browse_page":
        url = args.get("url", "")
        instr = (args.get("instructions") or "")[:50]
        return f"[Tool: browse_page] Browsing {url}" + (f" — {instr}..." if instr else "")
    if name == "execute_python":
        code = (args.get("code") or "").strip()
        preview = code.split("\n")[0][:50] if code else "(no code)"
        return f"[Tool: execute_python] Running: {preview}{'...' if len(code) > 50 else ''}"
    if name == "create_powerpoint":
        path = args.get("output_path", "output.pptx")
        content_len = len(args.get("content", ""))
        return f"[Tool: create_powerpoint] Saving to {path} ({content_len} chars)"
    return f"[Tool: {name}]"

def _model_supports_temperature(model_id: str) -> bool:
    """True if the model accepts the temperature parameter (o3/o4 family do not)."""
    normalized = model_id.strip().lower()
    return not (normalized.startswith("o3") or normalized.startswith("o4"))


class ResearchAgent:
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_turns: Optional[int] = None,
    ) -> None:
        self.model = model if model is not None else SETTINGS.AGENT_MODEL
        self.temperature = temperature if temperature is not None else SETTINGS.AGENT_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens is not None else SETTINGS.AGENT_MAX_TOKENS
        self.max_turns = max_turns if max_turns is not None else SETTINGS.AGENT_MAX_TURNS
        self.client: AsyncOpenAI = async_client
        self.tracker = CostTracker()
        self.tools = [
            function_tool(browse_page),
            function_tool(web_search),
            function_tool(execute_python),
            function_tool(create_powerpoint),
        ]
        if _model_supports_temperature(self.model):
            model_settings = ModelSettings(
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        else:
            model_settings = ModelSettings(max_tokens=self.max_tokens)
        instructions = (
            "You are an expert research assistant. "
            "For research questions you MUST use web_search first to find sources, then use browse_page to read specific URLs. "
            "Do not answer from memory alone—always call tools to get current, citable information. "
            "Use execute_python only when mathematical or data processing is explicitly required. "
            "When the user asks to save or export the result to PowerPoint, use the create_powerpoint tool with your summary. "
            "Cite every source with its full URL. Never hallucinate information."
        )
        self._agent = Agent(
            name="ResearchAssistant",
            model=self.model,
            model_settings=model_settings,
            instructions=instructions,
            tools=self.tools,
        )

    async def run(self, query: str) -> None:
        agent = self._agent
        result = Runner.run_streamed(agent, input=query, max_turns=self.max_turns)
        print(f"User query: {query}\n")
        print("Agent thinking...\n")
        mock_disclaimer_printed = False
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                continue
            if event.type == "run_item_stream_event":
                if event.name == "message_output_created":
                    if is_mock_tools() and not mock_disclaimer_printed:
                        print("This response was generated without real tool use (mock mode).\n", flush=True)
                        mock_disclaimer_printed = True
                    text = ItemHelpers.text_message_output(event.item)
                    if text:
                        print(text, end="", flush=True)
                elif event.name == "tool_called":
                    # SDK is about to run the tool (see tools/web.py: browse_page, web_search, execute_python)
                    raw = getattr(event.item, "raw_item", None)
                    name = getattr(raw, "name", None) if raw else None
                    args_str = getattr(raw, "arguments", None) if raw else None
                    if not name:
                        fn = getattr(event.item, "function", event.item)
                        name = getattr(fn, "name", "tool")
                    line = _format_tool_call_reasoning(name, args_str or "{}")
                    print(f"\n{line}")
                elif event.name == "tool_output":
                    pass  # result already fed back to the agent by the SDK
        await result.run_loop_task
        usage = getattr(
            getattr(result, "context_wrapper", None), "usage", None
        )
        if usage:
            self.tracker.add_usage(usage)
        self.tracker.report(model=self.model)


def run_research_agent(query: str) -> None:
    """Convenience synchronous wrapper for notebooks and CLI."""
    agent = ResearchAgent()
    asyncio.run(agent.run(query))
