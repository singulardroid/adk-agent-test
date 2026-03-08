"""adk-agent-test CLI entrypoint."""

import os

from dotenv import load_dotenv

load_dotenv()

from .config import SETTINGS
from .logging_config import get_logger, setup_logging

setup_logging(SETTINGS.LOG_LEVEL)
logger = get_logger(__name__)

import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def run(message: str = typer.Argument(..., help="Message to send to the agent")):
    """Run the agent with the given message."""
    logger.info("run() entry")
    from agents import Agent, Runner

    logger.debug("Agent, Runner imported")
    agent = Agent(name="Assistant", instructions="You are a helpful assistant.")
    logger.debug("agent=%s", agent)
    result = Runner.run_sync(agent, message)
    logger.debug("result.final_output=%s", result.final_output[:100] if result.final_output else None)
    console.print(result.final_output)
    logger.info("run() exit")


@app.command()
def research(
    query: str = typer.Argument(..., help="Question to research"),
    mock: bool = typer.Option(False, "--mock", "-m", help="Use mock tools (ADK_MOCK_TOOLS=1)"),
) -> None:
    """Run the research agent with the given question."""
    logger.info("research() entry query=%r mock=%s", query[:50], mock)
    if mock:
        os.environ["ADK_MOCK_TOOLS"] = "1"
        logger.info("ADK_MOCK_TOOLS=1 set (mock tools will be used)")
    else:
        os.environ["ADK_MOCK_TOOLS"] = "0"
    from .agent import run_research_agent

    logger.debug("run_research_agent imported")
    run_research_agent(query)
    logger.info("research() exit")


@app.command()
def hello():
    """Print a hello message (no API call)."""
    logger.info("hello() entry")
    console.print("[green]Hello from adk-agent-test![/green]")
    logger.debug("hello message printed")
    logger.info("hello() exit")


if __name__ == "__main__":
    logger.info("main entry")
    app()
    logger.info("main exit")
