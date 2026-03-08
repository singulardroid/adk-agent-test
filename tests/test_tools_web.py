"""Tests for web tools with mock and real backends."""

import importlib
import os
from unittest.mock import MagicMock, patch

import pytest

import adk_agent_test.tools.web as web_module
from adk_agent_test.tools.web import browse_page, execute_python, web_search


# ----- Mock result helpers -----

def _mock_browse_result(content: str = "Mock page content"):
    out = MagicMock()
    out.content = content
    return out


def _mock_search_result(title: str = "Example", url: str = "https://example.com", snippet: str = "A snippet"):
    r = MagicMock()
    r.title = title
    r.url = url
    r.snippet = snippet
    return r


def _mock_search_results(*results):
    out = MagicMock()
    out.results = list(results)
    return out


def _mock_code_execution_result(output: str = "2", error: str = ""):
    out = MagicMock()
    out.output = output
    out.error = error
    return out


# ----- ADK_MOCK_TOOLS=1: decorator uses mock_* implementations -----

@patch("adk_agent_test.tools.web.client")
def test_adk_mock_tools_browse_page_returns_mock_result(mock_client: MagicMock) -> None:
    """When ADK_MOCK_TOOLS=1, browse_page() uses mock_browse_page and does not call the API."""
    os.environ["ADK_MOCK_TOOLS"] = "1"
    try:
        importlib.reload(web_module)
        result = web_module.browse_page("https://example.com", "Get the title")
        assert "[MOCK]" in result
        assert "Content from https://example.com:" in result
        assert "dummy content" in result
        mock_client.beta.tools.browse.assert_not_called()
    finally:
        os.environ.pop("ADK_MOCK_TOOLS", None)
        importlib.reload(web_module)


@patch("adk_agent_test.tools.web.client")
def test_adk_mock_tools_web_search_returns_mock_result(mock_client: MagicMock) -> None:
    """When ADK_MOCK_TOOLS=1, web_search() uses mock_web_search and does not call the API."""
    os.environ["ADK_MOCK_TOOLS"] = "1"
    try:
        importlib.reload(web_module)
        result = web_module.web_search("test query", num_results=5)
        assert "[MOCK]" in result
        assert "Result for: test query" in result
        assert "Mock snippet" in result
        mock_client.beta.tools.search.assert_not_called()
    finally:
        os.environ.pop("ADK_MOCK_TOOLS", None)
        importlib.reload(web_module)


# ----- Mock mode: patched client (no ADK_MOCK_TOOLS) -----

@patch("adk_agent_test.tools.web.client")
def test_browse_page_mock(mock_client: MagicMock) -> None:
    """browse_page returns formatted content when client is mocked."""
    mock_client.beta.tools.browse.return_value = _mock_browse_result("Hello from the page")
    result = browse_page("https://example.com", "Get the title")
    assert "Content from https://example.com:" in result
    assert "Hello from the page" in result
    mock_client.beta.tools.browse.assert_called_once_with(
        url="https://example.com",
        instructions="Get the title",
    )


@patch("adk_agent_test.tools.web.client")
def test_web_search_mock(mock_client: MagicMock) -> None:
    """web_search returns numbered results when client is mocked."""
    mock_client.beta.tools.search.return_value = _mock_search_results(
        _mock_search_result("First", "https://a.com", "Snippet one"),
        _mock_search_result("Second", "https://b.com", "Snippet two"),
    )
    result = web_search("test query", num_results=2)
    assert "1." in result
    assert "First" in result
    assert "https://a.com" in result
    assert "Snippet one" in result
    assert "2." in result
    assert "Second" in result
    assert "https://b.com" in result
    mock_client.beta.tools.search.assert_called_once_with(query="test query", num_results=2)


@patch("adk_agent_test.tools.web.client")
def test_execute_python_mock(mock_client: MagicMock) -> None:
    """Execute_python returns execution output when client is mocked."""
    mock_client.beta.tools.code_execution.return_value = _mock_code_execution_result("42", "")
    result = execute_python("print(6*7)")
    assert "Code execution result" in result
    assert "42" in result
    mock_client.beta.tools.code_execution.assert_called_once_with(
        code="print(6*7)",
        globals_allowed=False,
    )


# ----- Real tools: require OPENAI_API_KEY; skip otherwise -----

def _has_api_key() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


@pytest.mark.integration
@pytest.mark.skipif(not _has_api_key(), reason="OPENAI_API_KEY not set")
def test_browse_page_real() -> None:
    """browse_page a real URL (integration)."""
    result = browse_page("https://example.com", "Extract the main heading.")
    assert "Content from https://example.com:" in result
    assert len(result) > 100


@pytest.mark.integration
@pytest.mark.skipif(not _has_api_key(), reason="OPENAI_API_KEY not set")
def test_web_search_real() -> None:
    """Web search (integration)."""
    result = web_search("Python 3.12 release", num_results=3)
    assert "1." in result
    assert "http" in result or "https" in result


@pytest.mark.integration
@pytest.mark.skipif(not _has_api_key(), reason="OPENAI_API_KEY not set")
def test_execute_python_real() -> None:
    """Execute Python in sandbox (integration)."""
    result = execute_python("print(1 + 1)")
    assert "Code execution result" in result
    assert "2" in result
