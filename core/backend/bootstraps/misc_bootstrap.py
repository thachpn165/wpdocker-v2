import os
from core.backend.utils.env_utils import env_required, env
from core.backend.objects.downloader import Downloader

env_required([
    "INSTALL_DIR",
])

def ensure_wp_cli():
    wp_cli_path = os.path.join(env["INSTALL_DIR"], "core", "wp", "wp-cli.phar")
    if not os.path.isfile(wp_cli_path):
        print("⬇️ Đang tải WP-CLI...")
        os.makedirs(os.path.dirname(wp_cli_path), exist_ok=True)

        downloader = Downloader(
            url="https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar",
            desc="WP-CLI"
        )
        downloader.download_to(wp_cli_path)

        os.chmod(wp_cli_path, 0o755)
        print("✅ Đã tải xong WP-CLI.")

        
def run_misc_bootstrap():
    ensure_wp_cli()