from core.backend.utils.env_utils import env_required, env
import os
import sys
import logging
import functools
import inspect

# ===== Lấy biến môi trường bắt buộc =====
env_required(["DEBUG_MODE"])

# ===== Tạo logger chuẩn cho toàn hệ thống =====
logger = logging.getLogger("wpdocker")
logger.setLevel(
    logging.DEBUG if env["DEBUG_MODE"].lower() == "true" else logging.INFO)

# ===== ANSI màu =====
RESET = "\033[0m"
BOLD = "\033[1m"
WHITE = "\033[37m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
DIM = "\033[2m"
# ===== Format màu theo cấp độ =====


class ColorFormatter(logging.Formatter):
    def format(self, record):
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

# ===== Hàm tiện dụng để log nhanh =====


def debug(msg):
    logger.debug(f"🐞 {msg}")


def info(msg):
    logger.info(f"ℹ️  {msg}")


def warn(msg):
    logger.warning(f"⚠️  {msg}")


def error(msg):
    logger.error(f"❌  {msg}")


def success(msg):
    print(f"{GREEN}{BOLD}✅ {msg}{RESET}")

# ===== Decorator để tự log các lời gọi hàm =====


def log_call(_func=None, *, log_vars=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            frame = inspect.currentframe()
            caller_file = os.path.basename(frame.f_back.f_code.co_filename)
            logger.debug(f"{DIM}CALL {func.__name__}() [{caller_file}]{RESET}")

            result = func(*args, **kwargs)

            # Log thêm các biến cụ thể nếu được chỉ định
            if log_vars and isinstance(result, dict):
                for var_name in log_vars:
                    value = result.get(var_name, "❓ not found")
                    logger.debug(f"{DIM}  ↳ {var_name} = {value}{RESET}")

            logger.debug(f"{DIM}DONE {func.__name__} → {result} [{caller_file}]{RESET}")
            return result
        return wrapper

    # Nếu gọi trực tiếp @log_call không đối số
    if callable(_func):
        return decorator(_func)

    return decorator

# ===== Hook để log các exception chưa được bắt =====


def enable_exception_hook():
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.excepthook = handle_exception


class Debug:
    """Helper class for module-specific debugging."""
    
    def __init__(self, module_name):
        """Initialize with module name for logging context.
        
        Args:
            module_name: Name of the module for log context
        """
        self.module_name = module_name
    
    def debug(self, message):
        """Log a debug message.
        
        Args:
            message: The message to log
        """
        if env["DEBUG_MODE"].lower() == "true":
            logger.debug(f"[{self.module_name}] 🐞 {message}")
    
    def info(self, message):
        """Log an info message.
        
        Args:
            message: The message to log
        """
        logger.info(f"[{self.module_name}] ℹ️  {message}")
    
    def warn(self, message):
        """Log a warning message.
        
        Args:
            message: The message to log
        """
        logger.warning(f"[{self.module_name}] ⚠️  {message}")
    
    def error(self, message):
        """Log an error message.
        
        Args:
            message: The message to log
        """
        logger.error(f"[{self.module_name}] ❌  {message}")
    
    def success(self, message):
        """Log a success message.
        
        Args:
            message: The message to log
        """
        print(f"{GREEN}{BOLD}✅ [{self.module_name}] {message}{RESET}")