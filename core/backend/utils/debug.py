import os
import sys
import logging
import functools

# ===== Tạo logger chuẩn cho toàn hệ thống =====
logger = logging.getLogger("wpdocker")
logger.setLevel(logging.DEBUG if os.environ.get("DEBUG_MODE", "false").lower() == "true" else logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

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
    logger.error(f"❌ {msg}")

# ===== Decorator để tự log các lời gọi hàm =====
def log_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"🔍 CALL {func.__name__}()")
        result = func(*args, **kwargs)
        logger.debug(f"✅ DONE {func.__name__} → {result}")
        return result
    return wrapper

# ===== Hook để log các exception chưa được bắt =====
def enable_exception_hook():
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("❌ Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.excepthook = handle_exception