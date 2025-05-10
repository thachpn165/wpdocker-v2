from src.common.logging import debug, info, error, success
from src.features.wordpress.utils import run_wpcli_in_wpcli_container
from src.features.website.utils import get_site_config, set_site_config
from src.features.website.models.site_config import WordPressConfig

class WordPressAutoUpdateManager:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def toggle_theme_auto_update(self, domain: str) -> bool:
        site_config = get_site_config(domain)
        if not site_config:
            error(f"[AutoUpdate] Không tìm thấy cấu hình cho {domain}")
            return False
        # Ensure wordpress config exists
        if not hasattr(site_config, 'wordpress') or site_config.wordpress is None:
            site_config.wordpress = WordPressConfig()
        wpconf = site_config.wordpress
        # Determine current state
        enabled = wpconf.auto_update_theme
        # Toggle state
        new_state = not enabled
        # Run WP CLI
        result = run_wpcli_in_wpcli_container(domain, ["theme", "auto-updates", "enable" if new_state else "disable", "--all"])
        if result is None:
            error(f"[AutoUpdate] Không thể {'bật' if new_state else 'tắt'} auto update cho theme trên {domain}")
            return False
        wpconf.auto_update_theme = new_state
        set_site_config(domain, site_config)
        success(f"[AutoUpdate] Đã {'bật' if new_state else 'tắt'} auto update cho theme trên {domain}")
        return True

    def toggle_plugin_auto_update(self, domain: str) -> bool:
        site_config = get_site_config(domain)
        if not site_config:
            error(f"[AutoUpdate] Không tìm thấy cấu hình cho {domain}")
            return False
        # Ensure wordpress config exists
        if not hasattr(site_config, 'wordpress') or site_config.wordpress is None:
            site_config.wordpress = WordPressConfig()
        wpconf = site_config.wordpress
        # Determine current state
        enabled = wpconf.auto_update_plugin
        # Toggle state
        new_state = not enabled
        # Run WP CLI
        result = run_wpcli_in_wpcli_container(domain, ["plugin", "auto-updates", "enable" if new_state else "disable", "--all"])
        if result is None:
            error(f"[AutoUpdate] Không thể {'bật' if new_state else 'tắt'} auto update cho plugin trên {domain}")
            return False
        wpconf.auto_update_plugin = new_state
        set_site_config(domain, site_config)
        success(f"[AutoUpdate] Đã {'bật' if new_state else 'tắt'} auto update cho plugin trên {domain}")
        return True 