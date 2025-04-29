from core.backend.modules.website.website_actions import WEBSITE_CLEANUP_ACTIONS
from core.backend.modules.nginx.nginx import reload as nginx_reload


def delete_website(domain):
    """
    Xoá website với tên miền đã cho, sử dụng WEBSITE_CLEANUP_ACTIONS.
    """
    try:
        for action in WEBSITE_CLEANUP_ACTIONS:
            action(domain)

        # Reload NGINX sau khi xoá site
        nginx_reload()

        print(f"✅ Website '{domain}' đã được xoá thành công.")
    except Exception as e:
        print(f"❌ Lỗi khi xoá website '{domain}': {e}")