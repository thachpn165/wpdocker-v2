# File: core/backend/objects/container.py

from python_on_whales import DockerClient
from core.backend.utils.debug import log_call, debug, info, warn, error

class Container:
    def __init__(self, name):
        self.name = name
        self.docker = DockerClient()

    def get(self):
        containers = self.docker.container.list(all=True, filters={"name": self.name})
        return containers[0] if containers else None

    def exists(self):
        return self.get() is not None

    def running(self):
        container = self.get()
        return container is not None and container.state == "running"

    def not_running(self):
        container = self.get()
        return container is not None and container.state != "running"

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
    def exec(self, command, workdir=None, environment=None, user=None):
        try:
            result = self.docker.container.execute(
                self.name,
                command,
                workdir=workdir,
                envs=environment or {},
                user=user,
                interactive=True,
                tty=True,
            )
            debug(f"✅ Đã thực thi lệnh: {' '.join(command)} trong container {self.name}")
            return result
        except Exception as e:
            error(f"❌ Lỗi khi thực thi lệnh {' '.join(command)} trong container {self.name}: {e}")
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
            self.docker.container.cp(src_path, f"{self.name}:{dest_path_in_container}")
            info(f"📁 Đã copy {src_path} vào container {self.name}:{dest_path_in_container}")
        except Exception as e:
            error(f"❌ Lỗi khi copy file vào container {self.name}: {e}")

    @log_call
    def copy_from(self, src_path_in_container, dest_path):
        try:
            self.docker.container.cp(f"{self.name}:{src_path_in_container}", dest_path)
            info(f"📁 Đã copy {self.name}:{src_path_in_container} ra host {dest_path}")
        except Exception as e:
            error(f"❌ Lỗi khi copy file từ container {self.name}: {e}")
