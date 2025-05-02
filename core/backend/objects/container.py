# File: core/backend/objects/container.py

from python_on_whales import DockerClient
from core.backend.utils.debug import log_call, debug, info, warn, error

class Container:
    def __init__(self, name):
        self.name = name
        self.docker = DockerClient()

    def get(self):
        try:
            container = self.docker.container.inspect(self.name)
            return container
        except Exception:
            return None

    def exists(self):
        return self.get() is not None

    @log_call(log_vars=["self.name"])
    def running(self):
        try:
            container = self.get()
            if not container:
                return False
            is_running = container.state.running
            debug(f"⚙️ Trạng thái container {self.name}: Running = {is_running}")
            return is_running
        except Exception as e:
            error(f"❌ Không kiểm tra được trạng thái container {self.name}: {e}")
            return False
        
        return {
            "self.name": self.name,
        }

    def not_running(self):
        try:
            container = self.get()
            return not container.state.running if container else False
        except Exception as e:
            error(f"❌ Không kiểm tra được trạng thái container {self.name}: {e}")
            return False

    @log_call
    def start(self):
        try:
            self.docker.container.start(self.name)
            info(f"✅ Đã khởi động container {self.name}.")
        except Exception as e:
            error(f"❌ Lỗi khi start container {self.name}: {e}")

    @log_call
    def stop(self):
        try:
            self.docker.container.stop(self.name)
            info(f"🛑 Đã dừng container {self.name}.")
        except Exception as e:
            error(f"❌ Lỗi khi stop container {self.name}: {e}")

    @log_call
    def restart(self):
        try:
            self.docker.container.restart(self.name)
            info(f"🔄 Đã restart container {self.name}.")
        except Exception as e:
            error(f"❌ Lỗi khi restart container {self.name}: {e}")

    @log_call
    def remove(self, force=True):
        try:
            self.docker.container.remove(self.name, force=force)
            info(f"🗑️ Đã xóa container {self.name}.")
        except Exception as e:
            error(f"❌ Lỗi khi xóa container {self.name}: {e}")

    @log_call
    def exec(self, cmd, workdir=None, user=None, envs=None):
        from colorama import Fore, Style
        """
        Thực thi lệnh trong container và trả về kết quả.
        Nếu có lỗi, in ra lỗi chi tiết từ container.
        Hỗ trợ tùy chọn user để chạy lệnh với quyền cụ thể.
        """
        try:
            # Thêm tùy chọn user nếu được truyền
            exec_result = self.docker.container.execute(
                self.name,
                command=cmd,
                workdir=workdir,
                tty=False,
                interactive=False,
                user=user,
                envs=envs or {}
            )
            from core.backend.utils.debug import debug
            debug(f"📤 Output từ container.exec: {exec_result!r}")

            return exec_result
        except Exception as e:
            # In lỗi chi tiết từ container
            error(f"Error: {e}") 
            #error(f"Lỗi khi thực thi lệnh trong container {self.name}. Đọc lỗi ở trên. {e}")
            return None

    @log_call
    def logs(self, follow=False, tail=100):
        try:
            logs = self.docker.container.logs(self.name, follow=follow, tail=tail)
            return logs
        except Exception as e:
            error(f"❌ Lỗi khi lấy logs container {self.name}: {e}")
            return None

    @log_call
    def inspect(self):
        try:
            container = self.docker.container.inspect(self.name)
            debug(f"📋 Thông tin container {self.name}: {container}")
            return container
        except Exception as e:
            error(f"❌ Lỗi khi inspect container {self.name}: {e}")
            return None

    @log_call
    def copy_to(self, src_path, dest_path_in_container):
        try:
            self.docker.container.copy(src_path, f"{self.name}:{dest_path_in_container}")
            info(f"📁 Đã copy {src_path} vào container {self.name}:{dest_path_in_container}")
        except Exception as e:
            error(f"❌ Lỗi khi copy file vào container {self.name}: {e}")

    @log_call
    def copy_from(self, src_path_in_container, dest_path):
        try:
            self.docker.container.copy(f"{self.name}:{src_path_in_container}", dest_path)
            info(f"📁 Đã copy {self.name}:{src_path_in_container} ra host {dest_path}")
        except Exception as e:
            error(f"❌ Lỗi khi copy file từ container {self.name}: {e}")
