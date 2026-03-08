"""Web and tool helpers using OpenAI beta tools."""

import os
import sys
from typing import Annotated

from openai import OpenAI

from ..config import client, is_mock_tools
from ..logging_config import get_logger
from ._mockable import mockable

logger = get_logger(__name__)

# NOTE: Use distinct names (browse_page, web_search) so the Responses API runs our
# Python tools client-side instead of built-in server-side browse/search_web.


def mock_browse_page(
    url: Annotated[str, "Exact URI to visit, including https://"],
    instructions: Annotated[
        str,
        "What the agent should extract or summarize. Be specific about sections, tables, dates.",
    ] = "Extract the main content and any recent updates.",
) -> str:
    """Mock browse_page: no API call."""
    logger.info("[MOCK] mock_browse_page called url=%s instructions=%r", url, (instructions or "")[:80])
    print("[MOCK] mock_browse_page called", flush=True)
    return f"Content from {url}:\n[MOCK] dummy content"


def mock_web_search(
    query: Annotated[str, "Natural language search query or exact phrase"],
    num_results: Annotated[int, "Number of results to return, max 20"] = 10,
) -> str:
    """Mock web_search: no API call."""
    logger.info("[MOCK] mock_web_search called query=%r num_results=%d", query, num_results)
    print("[MOCK] mock_web_search called", flush=True)
    return f"1.\n   [MOCK] Result for: {query}\n   https://mock.example/1\n   Mock snippet (num_results=0)"


@mockable
def browse_page(
    url: Annotated[str, "Exact URI to visit, including https://"],
    instructions: Annotated[
        str,
        "What the agent should extract or summarize. Be specific about sections, tables, dates.",
    ] = "Extract the main content and any recent updates.",
) -> str:
    """Fetch a webpage using OpenAI's secure sandboxed browser (client-side tool)."""
    if is_mock_tools():
        msg = "ADK_MOCK_TOOLS=1 but real browse_page() was invoked; mock path should have been used."
        logger.error("%s", msg)
        print(msg, file=sys.stderr, flush=True)
        os._exit(1)
    logger.info("[REAL] browse_page() called url=%s", url)
    logger.info("browse_page() entry url=%s instructions=%r", url, instructions[:80] if instructions else "")
    result = client.beta.tools.browse(url=url, instructions=instructions)
    content = result.content.strip()
    logger.debug("browse_page() result len=%d", len(content))
    logger.info("browse_page() exit")
    return f"Content from {url}:\n{content}"


@mockable
def web_search(
    query: Annotated[str, "Natural language search query or exact phrase"],
    num_results: Annotated[int, "Number of results to return, max 20"] = 10,
) -> str:
    """Perform a web search and return titles, URLs, and short snippets (client-side tool)."""
    if is_mock_tools():
        msg = "ADK_MOCK_TOOLS=1 but real web_search() was invoked; mock path should have been used."
        logger.error("%s", msg)
        print(msg, file=sys.stderr, flush=True)
        os._exit(1)
    logger.info("[REAL] web_search() called query=%r", query)
    logger.info("web_search() entry query=%r num_results=%d", query, num_results)
    results = client.beta.tools.search(query=query, num_results=num_results)
    formatted = []
    for i, r in enumerate(results.results, 1):
        formatted.append(f"{i}. {r.title}\n   {r.url}\n   {r.snippet}")
    out = "\n".join(formatted)
    logger.debug("web_search() got %d results", len(results.results))
    logger.info("web_search() exit")
    return out


def execute_python(
    code: Annotated[str, "Complete, valid Python code to execute"],
    globals_allowed: Annotated[bool, "Allow modification of global scope"] = False,
) -> str:
    """Execute Python code in a restricted REPL with common data science packages."""
    logger.info("execute_python() entry code_len=%d globals_allowed=%s", len(code), globals_allowed)
    exec_result = client.beta.tools.code_execution(
        code=code,
        globals_allowed=globals_allowed,
    )
    stdout = exec_result.output.strip()
    error = exec_result.error.strip() if exec_result.error else ""
    result = f"Code execution result:\n{stdout}\n{error}".strip()
    logger.debug("execute_python() stdout len=%d has_error=%s", len(stdout), bool(exec_result.error))
    logger.info("execute_python() exit")
    return result
