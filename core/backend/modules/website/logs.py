import time
import os
from core.backend.modules.website.website_utils import get_site_config
from core.backend.utils.debug import log_call, error
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

@log_call
def watch_logs_website(domain: str, log_type: str):


    site_config = get_site_config(domain)
    if not site_config or not site_config.logs:
        error(f"❌ Không tìm thấy logs của website {domain}.")
        return

    log_path = getattr(site_config.logs, log_type, None)
    if not log_path or not os.path.isfile(log_path):
        error(f"❌ Không tìm thấy log {log_type} tại {log_path}.")
        return

    countdown = 30
    with open(log_path, "r") as f:
        f.seek(0, os.SEEK_END)  # chỉ theo dõi log mới từ sau thời điểm này

        with Live(refresh_per_second=4) as live:
            buffer = []
            while countdown > 0:
                try:
                    new_lines = f.readlines()
                    if new_lines:
                        buffer.extend(new_lines)
                        buffer = buffer[-20:]  # giữ tối đa 20 dòng mới nhất
                    content = Text("".join(buffer), style="white")
                    header = Text(f"⏱️ Còn lại: {countdown}s", style="bold green")
                    panel = Panel.fit(
                        Align.center(content, vertical="top"),
                        title=f"📄 Log: {log_type} | {domain}",
                        subtitle=header,
                        border_style="cyan"
                    )
                    live.update(panel)

                    time.sleep(1)
                    countdown -= 1
                except KeyboardInterrupt:
                    break
    return True