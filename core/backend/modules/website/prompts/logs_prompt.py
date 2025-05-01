from core.backend.modules.website.website_utils import website_list
from core.backend.utils.debug import log_call, info, warn, error, debug
from core.backend.modules.website.logs import watch_logs_website
from questionary import select

@log_call
def prompt_watch_logs():
    websites = website_list()
    debug(f"Websites: {websites}")
    if not websites:
        warn("Không tìm thấy website nào để xem log.")
        return

    domain = select("Chọn website cần xem log:", choices=websites).ask()
    if domain is None:
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