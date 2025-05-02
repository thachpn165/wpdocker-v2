from core.backend.modules.website.website_utils import select_website
from core.backend.utils.debug import log_call, info, warn, error, debug
from core.backend.modules.website.logs import watch_logs_website
from questionary import select

@log_call
def prompt_watch_logs():
    domain = select_website("Chọn website cần xem log:")
    if not domain:
        info("Đã huỷ thao tác xem log.")
        return

    log_choices = {
        "📝 Log truy cập (access.log)": "access",
        "❌ Lỗi NGINX (error.log)": "error",
        "🐌 PHP chạy chậm (php_slow.log)": "php_slow",
        "🐞 Lỗi PHP (php_error.log)": "php_error"
    }

    label = select("Chọn loại log cần xem:", choices=list(log_choices.keys())).ask()
    if label is None:
        info("Đã huỷ thao tác xem log.")
        return  

    log_type = log_choices[label]
    watch_logs_website(domain, log_type)