from core.backend.abc.php_extension import PHPBaseExtension
from core.backend.modules.php.init_client import init_php_client
from core.backend.utils.debug import info, error
from core.backend.modules.website.website_utils import get_site_config, set_site_config
from core.backend.utils.validate import _is_arm
class IoncubeLoaderExtension(PHPBaseExtension):
    def get_id(self) -> str:
        return "ioncube_loader"

    def get_title(self) -> str:
        return "Ioncube Loader"

    def install(self, domain: str):
        container = init_php_client(domain)

        # Lấy version và arch
        php_version = container.exec(["php", "-r", "echo PHP_VERSION;"]).strip().split(".")[:2]
        php_version = ".".join(php_version)
        arch = container.exec(["uname", "-m"]).strip()

        if _is_arm():
            error("Ioncube Loader không hỗ trợ kiến trúc ARM")
            return

        # Kiểm tra ZTS hay NTS
        zts = container.exec(["php", "-i"]).find("Thread Safety => enabled") != -1
        zts_suffix = "_ts" if zts else ""
        loader_file = f"ioncube_loader_lin_{php_version}{zts_suffix}.so"
        loader_path = f"/opt/bitnami/php/lib/php/extensions/{loader_file}"

        info(f"🔍 Kiểm tra file loader: {loader_path}")
        if container.exec(["test", "-f", loader_path], user="root") != "":
            info("📥 Đang tải và giải nén ioncube...")
            container.exec([
                "bash", "-c",
                "mkdir -p /tmp/ioncube && "
                "curl -sSL -o /tmp/ioncube.tar.gz https://downloads.ioncube.com/loader_downloads/ioncube_loaders_lin_x86-64.tar.gz && "
                "tar -xzf /tmp/ioncube.tar.gz -C /tmp/ioncube && "
                "tar -tzf /tmp/ioncube.tar.gz > /tmp/ioncube/filelist.txt"
            ], user="root")

            if container.exec(["grep", f"ioncube/{loader_file}", "/tmp/ioncube/filelist.txt"]).strip() == "":
                error(f"❌ Không tìm thấy {loader_file} trong bản tải ioncube. Không tương thích.")
                container.exec(["rm", "-rf", "/tmp/ioncube", "/tmp/ioncube.tar.gz"], user="root")
                return

            container.exec([
                "bash", "-c",
                f"cp /tmp/ioncube/ioncube/{loader_file} {loader_path} && "
                f"chmod 755 {loader_path} && "
                f"rm -rf /tmp/ioncube /tmp/ioncube.tar.gz"
            ], user="root")

        # Kiểm tra lại
        if container.exec(["test", "-f", loader_path], user="root") != "":
            error(f"❌ Không tìm thấy file loader sau khi copy: {loader_path}")
            return

        # Chỉnh sửa php.ini
        from core.backend.utils.env_utils import env
        php_ini = f"{env['SITES_DIR']}/{domain}/php/php.ini"
        if not os.path.isfile(php_ini):
            error(f"❌ Không tìm thấy php.ini tại {php_ini}")
            return

        with open(php_ini, "r") as f:
            lines = [line for line in f if "ioncube_loader_lin" not in line]

        with open(php_ini, "w") as f:
            f.writelines(lines)
            f.write(f"\nzend_extension={loader_path}\n")

        container.restart()
        info(f"✅ Đã cài đặt Ioncube Loader thành công cho {domain}.")

    def update_config(self, domain: str):
        site_config = get_site_config(domain)
        if site_config and site_config.php:
            exts = site_config.php.php_installed_extensions or []
            if "ioncube_loader" not in exts:
                exts.append("ioncube_loader")
                site_config.php.php_installed_extensions = exts
                set_site_config(domain, site_config)

    
    def post_install(self, domain: str):
        super().post_install(domain)  # ✅ Gọi lại logic của PHPBaseExtension nếu có

        from core.backend.modules.php.init_client import init_php_client
        container = init_php_client(domain)
        output = container.exec(["php", "-v"])
        if output:
            from core.backend.utils.debug import info
            info("📦 Phiên bản PHP hiện tại trong container:")
            print(output)
