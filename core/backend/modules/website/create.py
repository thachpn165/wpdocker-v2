from core.backend.modules.website.website_utils import _is_website_exists
from core.backend.utils.debug import log_call, info, warn, error, success, debug
from core.backend.modules.website.website_actions import WEBSITE_SETUP_ACTIONS
import inspect

@log_call
def create_website(domain: str, php_version: str):
    if _is_website_exists(domain):
        warn(f"⚠️ Website {domain} đã tồn tại.")
        return

    completed_steps = []
    try:
        for setup_func, cleanup_func in WEBSITE_SETUP_ACTIONS:
            sig = inspect.signature(setup_func)
            if len(sig.parameters) == 2:
                setup_func(domain, php_version)
            elif len(sig.parameters) == 1:
                setup_func(domain)
            else:
                raise ValueError(f"Unexpected number of parameters for {setup_func.__name__}")
            completed_steps.append((setup_func, cleanup_func))
        success(f"✅ Website {domain} đã được khởi tạo.")
    except (KeyboardInterrupt, EOFError):
        error("❌ Đã huỷ thao tác tạo website (Ctrl+C hoặc Ctrl+Z).")
        cleanup_website(domain, completed_steps)
    except Exception as e:
        error(f"❌ Lỗi khi tạo website: {e}")
        cleanup_website(domain, completed_steps)

def cleanup_website(domain, completed_steps):
    warn(f"⚠️ Đang rollback các bước đã thực hiện cho website {domain}...")
    for setup_func, cleanup_func in reversed(completed_steps):
        if cleanup_func is not None:
            try:
                cleanup_func(domain)
                info(f"↩️ Đã rollback bước {cleanup_func.__name__} cho website {domain}.")
            except Exception as e:
                error(f"❌ Lỗi khi rollback bước {cleanup_func.__name__}: {e}")
