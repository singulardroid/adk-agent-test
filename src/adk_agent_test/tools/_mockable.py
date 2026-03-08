"""Decorator to swap real tool implementations with mocks when ADK_MOCK_TOOLS=1."""

import functools
import importlib
from typing import Any, Callable

from ..config import is_mock_tools
from ..logging_config import get_logger

logger = get_logger(__name__)


def mockable(real_func: Callable) -> Callable:
    """
    Decorator: when ADK_MOCK_TOOLS=1, use mock_{real_func.__name__} from the same module.
    Otherwise, return the real function unchanged.
    """
    logger.info("mockable() entry real_func=%s", real_func.__name__)
    mock_name = f"mock_{real_func.__name__}"
    logger.debug("mock_name=%s", mock_name)
    module = importlib.import_module(real_func.__module__)
    logger.debug("module=%s", module)
    use_mock = is_mock_tools() and hasattr(module, mock_name)
    logger.debug("use_mock=%s", use_mock)
    if use_mock:
        mock_func = getattr(module, mock_name)
        logger.debug("mock_func=%s", mock_func)

        @functools.wraps(real_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.info("wrapper() entry func=%s", real_func.__name__)
            logger.debug("args=%s kwargs=%s", args, kwargs)
            logger.debug("[MOCK] Calling %s", real_func.__name__)
            result = mock_func(*args, **kwargs)
            logger.debug("result=%s", str(result)[:100] if result else None)
            logger.info("wrapper() exit")
            return result

        logger.info("mockable() exit returning wrapper")
        return wrapper
    logger.info("mockable() exit returning real_func")
    return real_func
