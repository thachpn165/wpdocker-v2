import os
from core.backend.utils.debug import log_call, info, debug, warn, error
from python_on_whales import DockerClient


class Container:
    def __init__(self, name, template_path, output_path, env_map, sensitive_env=None):
        self.name = name
        self.template_path = template_path
        self.output_path = output_path
        self.env_map = env_map
        self.sensitive_env = sensitive_env or {}
        self.docker = DockerClient(compose_files=[self.output_path])

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

    def ensure_network(self):
        network_name = self.env_map.get("DOCKER_NETWORK")
        if not network_name:
            warn("⚠️ Không tìm thấy biến DOCKER_NETWORK trong env_map.")
            return
        existing_networks = self.docker.network.list()
        if network_name not in [n.name for n in existing_networks]:
            info(f"🌐 Tạo Docker network: {network_name}")
            self.docker.network.create(network_name)
        else:
            debug(f"🌐 Docker network {network_name} đã tồn tại.")

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
    def up(self):
        try:
            self.docker.compose.up(detach=True, build=False)
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
            self.docker.container.restart(services=[self.name])
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
        self.ensure_network()
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