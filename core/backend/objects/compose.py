# File: core/backend/objects/compose.py

from python_on_whales import DockerClient
import os
from core.backend.utils.debug import log_call, info, debug, warn, error

class Compose:
    def __init__(self, name, template_path=None, output_path=None, env_map=None, sensitive_env=None):
        self.name = name
        self.template_path = template_path
        self.output_path = output_path
        self.env_map = env_map or {}
        self.sensitive_env = sensitive_env or {}

        if self.output_path:
            self.docker = DockerClient(compose_files=[self.output_path])
        else:
            self.docker = DockerClient()

    def get_container(self):
        containers = self.docker.container.list(all=True, filters={"name": self.name})
        return containers[0] if containers else None

    def exists(self):
        return self.get_container() is not None

    def running(self):
        container = self.get_container()
        return container is not None and container.state == "running"

    def not_running(self):
        container = self.get_container()
        return container is not None and container.state != "running"

    @log_call
    def generate_compose_file(self):
        with open(self.template_path, "r") as f:
            content = f.read()

        for key, value in self.env_map.items():
            content = content.replace(f"${{{key}}}", value)

        for key, value in self.sensitive_env.items():
            content = content.replace(f"${{{key}}}", value)

        with open(self.output_path, "w") as f:
            f.write(content)

    @log_call
    def up(self, detach=True, force_recreate=False, no_build=False):
        try:
            self.docker.compose.up(
                detach=detach,
                force_recreate=force_recreate,
                no_build=no_build,
                remove_orphans=False,
                quiet=True
            )
        except Exception as e:
            error(f"❌ Lỗi khi khởi động container {self.name}: {e}")

    @log_call
    def down(self):
        try:
            self.docker.compose.down()
        except Exception as e:
            error(f"❌ Lỗi khi dừng container {self.name}: {e}")

    def restart(self):
        try:
            self.down()
            self.up(force_recreate=True)
        except Exception as e:
            error(f"❌ Lỗi khi restart container {self.name}: {e}")

    @log_call
    def ensure_running(self):
        container = self.get_container()
        if container is None:
            warn(f"⚠️ Container {self.name} chưa tồn tại. Đang tạo mới...")
            self.up()
        elif container.state != "running":
            warn(f"⏸️ Container {self.name} đang dừng. Đang khởi động lại...")
            self.docker.container.start(container)
        else:
            info(f"✅ Container {self.name} đang chạy.")

    @log_call
    def ensure_ready(self, auto_start=True):
        compose_missing = not os.path.exists(self.output_path)
        container_missing = not self.exists()

        if compose_missing:
            info(f"📦 Tạo file docker-compose cho container {self.name}...")
            self.generate_compose_file()

        if container_missing:
            info(f"📦 Tạo container {self.name}...")
            self.up()
        else:
            debug(f"📦 Container {self.name} đã tồn tại.")

        if auto_start:
            self.ensure_running()
