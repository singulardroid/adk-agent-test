"""Application configuration loaded from environment variables."""

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from openai import AsyncOpenAI, OpenAI

from .logging_config import get_logger

logger = get_logger(__name__)


class Settings(BaseSettings):
    """Settings loaded from .env and environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # OpenAI
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_ORG_ID: str | None = Field(default=None, description="OpenAI organization ID")
    OPENAI_PROJECT_ID: str | None = Field(default=None, description="OpenAI project ID")

    # Agent (research agent model and generation settings)
    AGENT_MODEL: str = Field(default="o3-mini", description="Model name for the research agent")
    AGENT_TEMPERATURE: float = Field(default=0.2, ge=0, le=2, description="Model temperature (0–2); ignored for o3/o3-mini (not supported by API)")
    AGENT_MAX_TOKENS: int = Field(default=150_000, ge=1, description="Max tokens per response")
    AGENT_MAX_TURNS: int = Field(default=30, ge=1, description="Max agent turns per run")

    # Run limits
    MAX_TOKENS_PER_RUN: int = Field(default=4096, ge=1, description="Max tokens per run")
    MAX_DOLLARS_PER_RUN: float = Field(default=0.10, ge=0, description="Max dollars per run")
    MAX_LOOP_ITERATIONS: int = Field(default=50, ge=1, description="Max loop iterations")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR, or none to disable)")
    TRACEBACK: bool = Field(default=True, description="Enable traceback on errors")

    def build_client(self) -> OpenAI:
        """Build synchronous OpenAI client."""
        logger.info("build_client() entry")
        client = OpenAI(
            api_key=self.OPENAI_API_KEY,
            organization=self.OPENAI_ORG_ID,
            project=self.OPENAI_PROJECT_ID,
            max_retries=3,
            timeout=120.0,
        )
        logger.debug("client=%s", client)
        logger.info("build_client() exit")
        return client

    def build_async_client(self) -> AsyncOpenAI:
        """Build asynchronous OpenAI client."""
        logger.info("build_async_client() entry")
        client = AsyncOpenAI(
            api_key=self.OPENAI_API_KEY,
            organization=self.OPENAI_ORG_ID,
            project=self.OPENAI_PROJECT_ID,
            max_retries=3,
            timeout=120.0,
        )
        logger.debug("client=%s", client)
        logger.info("build_async_client() exit")
        return client


def is_mock_tools() -> bool:
    """True if ADK_MOCK_TOOLS=1 in the environment (use mock tool implementations)."""
    return os.environ.get("ADK_MOCK_TOOLS", "0") == "1"


logger.debug("Creating SETTINGS")
SETTINGS: Settings = Settings()
logger.debug("SETTINGS=%s", SETTINGS)
client: OpenAI = SETTINGS.build_client()
async_client: AsyncOpenAI = SETTINGS.build_async_client()
