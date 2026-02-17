"""Web and tool helpers using OpenAI beta tools."""

from typing import Annotated

from openai import OpenAI

from ..config import client
from ..logging_config import get_logger

logger = get_logger(__name__)


def browse(
    url: Annotated[str, "Exact URI to visit, including https://"],
    instructions: Annotated[
        str,
        "What the agent should extract or summarize. Be specific about sections, tables, dates.",
    ] = "Extract the main content and any recent updates.",
) -> str:
    """Browse a webpage using OpenAI's secure sandboxed browser."""
    logger.info("browse() entry url=%s instructions=%r", url, instructions[:80] if instructions else "")
    result = client.beta.tools.browse(url=url, instructions=instructions)
    content = result.content.strip()
    logger.debug("browse() result len=%d", len(content))
    logger.info("browse() exit")
    return f"Content from {url}:\n{content}"


def search_web(
    query: Annotated[str, "Natural language search query or exact phrase"],
    num_results: Annotated[int, "Number of results to return, max 20"] = 10,
) -> str:
    """Perform a web search and return titles, URLs, and short snippets."""
    logger.info("search_web() entry query=%r num_results=%d", query, num_results)
    results = client.beta.tools.search(query=query, num_results=num_results)
    formatted = []
    for i, r in enumerate(results.results, 1):
        formatted.append(f"{i}. {r.title}\n   {r.url}\n   {r.snippet}")
    out = "\n".join(formatted)
    logger.debug("search_web() got %d results", len(results.results))
    logger.info("search_web() exit")
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
