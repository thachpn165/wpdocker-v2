"""
Logging utilities for consistent log formatting and management.

This module provides standardized logging functionality including:
- Colored and formatted logging
- Convenience functions for different log levels
- Function call logging decorator
- Module-specific logging via the Debug class
- Uncaught exception handling
"""

import os
import sys
import logging
import functools
import inspect
from typing import Any, Callable, List, Optional, TypeVar, Union, cast

from src.common.utils.environment import env_required, env

# Required environment variables
env_required(["DEBUG_MODE"])

# Create standard logger for the entire system
logger = logging.getLogger("wpdocker")
logger.setLevel(
    logging.DEBUG if env["DEBUG_MODE"].lower() == "true" else logging.INFO)

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
WHITE = "\033[37m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
DIM = "\033[2m"


class ColorFormatter(logging.Formatter):
    """Custom formatter that adds color based on log level."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with appropriate color.

        Args:
            record: The log record to format

        Returns:
            Formatted and colored log message
        """
        prefix = ""
        msg = record.getMessage()
        if record.levelno == logging.DEBUG:
            prefix = f"{WHITE}"
        elif record.levelno == logging.INFO:
            prefix = f"{BOLD}{WHITE}"
        elif record.levelno == logging.WARNING:
            prefix = f"{BOLD}{YELLOW}"
        elif record.levelno == logging.ERROR:
            prefix = f"{BOLD}{RED}"
        return f"{prefix}{self.formatTime(record, '%H:%M:%S')} [{record.levelname}] {msg}{RESET}"


formatter = ColorFormatter()

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def debug(msg: str) -> None:
    """
    Log a debug message.

    Args:
        msg: The message to log
    """
    logger.debug(f"🐞 {msg}")


def info(msg: str) -> None:
    """
    Log an info message.

    Args:
        msg: The message to log
    """
    logger.info(f"ℹ️  {msg}")


def warn(msg: str) -> None:
    """
    Log a warning message.

    Args:
        msg: The message to log
    """
    logger.warning(f"⚠️  {msg}")


def error(msg: str) -> None:
    """
    Log an error message.

    Args:
        msg: The message to log
    """
    logger.error(f"❌  {msg}")


def success(msg: str) -> None:
    """
    Log a success message.

    Args:
        msg: The message to log
    """
    print(f"{GREEN}{BOLD}✅ {msg}{RESET}")


# Type variables for decorator
F = TypeVar('F', bound=Callable[..., Any])


def log_call(_func: Optional[F] = None, *, log_vars: Optional[List[str]] = None) -> Union[F, Callable[[F], F]]:
    """
    Decorator to automatically log function calls.

    Args:
        _func: The function to decorate (used internally)
        log_vars: List of result dictionary keys to log

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            frame = inspect.currentframe()
            if frame and frame.f_back:
                caller_file = os.path.basename(frame.f_back.f_code.co_filename)
                logger.debug(
                    f"{DIM}CALL {func.__name__}() [{caller_file}]{RESET}")

            result = func(*args, **kwargs)

            # Log specific variables if specified
            if log_vars and isinstance(result, dict):
                for var_name in log_vars:
                    value = result.get(var_name, "❓ not found")
                    logger.debug(f"{DIM}  ↳ {var_name} = {value}{RESET}")

            if frame and frame.f_back:
                logger.debug(
                    f"{DIM}DONE {func.__name__} → {result} [{caller_file}]{RESET}")
            return result
        return cast(F, wrapper)

    # If called directly with @log_call
    if callable(_func):
        return decorator(_func)

    return decorator


def enable_exception_hook() -> None:
    """Enable global exception hook to log uncaught exceptions."""

    def handle_exception(exc_type: type, exc_value: BaseException, exc_traceback: Any) -> None:
        """
        Handle uncaught exceptions by logging them.

        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("Uncaught exception", exc_info=(
            exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception


class Debug:
    """Helper class for module-specific debugging."""

    def __init__(self, module_name: str):
        """
        Initialize with module name for logging context.

        Args:
            module_name: Name of the module for log context
        """
        self.module_name = module_name

    def debug(self, message: str) -> None:
        """
        Log a debug message.

        Args:
            message: The message to log
        """
        if env["DEBUG_MODE"].lower() == "true":
            logger.debug(f"[{self.module_name}] 🐞 {message}")

    def info(self, message: str) -> None:
        """
        Log an info message.

        Args:
            message: The message to log
        """
        logger.info(f"[{self.module_name}] ℹ️  {message}")

    def warn(self, message: str) -> None:
        """
        Log a warning message.

        Args:
            message: The message to log
        """
        logger.warning(f"[{self.module_name}] ⚠️  {message}")

    def error(self, message: str) -> None:
        """
        Log an error message.

        Args:
            message: The message to log
        """
        logger.error(f"[{self.module_name}] ❌  {message}")

    def success(self, message: str) -> None:
        """
        Log a success message.

        Args:
            message: The message to log
        """
        print(f"{GREEN}{BOLD}✅ [{self.module_name}] {message}{RESET}")
