"""Track token usage and compute cost for OpenAI API calls."""

import time
from typing import Any, Optional

from .logging_config import get_logger

logger = get_logger(__name__)


class CostTracker:
    """Tracks input/output/cached tokens and computes USD cost."""

    def __init__(self) -> None:
        logger.info("CostTracker.__init__() entry")
        self.start_time = time.time()
        logger.debug("self.start_time=%s", self.start_time)
        self.input_tokens = 0
        self.output_tokens = 0
        self.cached_tokens = 0
        logger.debug("tokens initialized to 0")
        logger.info("CostTracker.__init__() exit")

    def add_usage(self, usage: Optional[Any]) -> None:
        """Add usage from an API response.

        Accepts OpenAI CompletionUsage (prompt_tokens, completion_tokens) or
        openai-agents Usage (input_tokens, output_tokens).
        """
        logger.info("add_usage() entry usage=%s", usage)
        if usage:
            inp = getattr(usage, "input_tokens", None) or getattr(usage, "prompt_tokens", 0)
            out = getattr(usage, "output_tokens", None) or getattr(usage, "completion_tokens", 0)
            self.input_tokens += inp
            logger.debug("input_tokens+=%d -> %d", inp, self.input_tokens)
            self.output_tokens += out or 0
            logger.debug("output_tokens+=%d -> %d", out or 0, self.output_tokens)
            details = getattr(usage, "input_tokens_details", None) or getattr(
                usage, "prompt_tokens_details", None
            )
            logger.debug("details=%s", details)
            if details:
                cached = getattr(details, "cached_tokens", 0) or 0
                if cached:
                    self.cached_tokens += cached
                    logger.debug("cached_tokens+=%d -> %d", cached, self.cached_tokens)
        logger.info("add_usage() exit")

    def total_cost_usd(self, model: str = "o3-mini") -> float:
        """Compute total cost in USD based on model pricing (per token)."""
        logger.info("total_cost_usd() entry model=%s", model)
        rates: dict[str, dict[str, float]] = {
            "o3-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
            "o3": {"input": 3.00 / 1_000_000, "output": 12.00 / 1_000_000},
            "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
        }
        logger.debug("rates=%s", list(rates.keys()))
        r = rates.get(model, rates["o3-mini"])
        logger.debug("r=%s", r)
        non_cached_input = self.input_tokens - self.cached_tokens
        logger.debug("non_cached_input=%d", non_cached_input)
        cost = (
            non_cached_input * r["input"]
            + self.cached_tokens * r["input"] * 0.5
            + self.output_tokens * r["output"]
        )
        logger.debug("cost=%s", cost)
        logger.info("total_cost_usd() exit")
        return cost

    def report(self, model: str = "o3-mini") -> None:
        """Print run summary: duration, token counts, cost."""
        logger.info("report() entry model=%s", model)
        elapsed = time.time() - self.start_time
        logger.debug("elapsed=%s", elapsed)
        cost = self.total_cost_usd(model)
        logger.debug("cost=%s", cost)
        print("\n=== Run Complete ===")
        print(f"Duration: {elapsed:.1f}s")
        print(f"Input tokens: {self.input_tokens:,}")
        print(f"Output tokens: {self.output_tokens:,}")
        print(f"Cached tokens: {self.cached_tokens:,}")
        print(f"Cost: ${cost:.4f}")
        logger.debug("report printed")
        logger.info("report() exit")
