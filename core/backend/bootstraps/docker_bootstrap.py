import subprocess
import platform
import os
from core.backend.utils.env_utils import env_required, env
from core.backend.utils.debug import log_call, info, debug, warn, error, success
from core.backend.modules.docker.docker_install import install_docker_if_missing


@log_call
def run_docker_bootstrap():
    env_required(["DOCKER_NETWORK"])
    if not install_docker_if_missing():
        error("Docker installation failed. Please check the logs.")
        return
    # Kiểm tra Docker có hoạt động không
    try:
        subprocess.run(["docker", "info"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        info("Docker is installed and running.")
    except Exception:
        error(
            "❌ Docker is not installed or not running. Please start Docker and try again.")
        return

    # Tạo Docker network nếu chưa có
    network = env["DOCKER_NETWORK"]
    try:
        result = subprocess.run(
            ["docker", "network", "ls", "--format", "{{.Name}}"], capture_output=True, text=True)
        networks = result.stdout.strip().splitlines()
        if network not in networks:
            subprocess.run(
                ["docker", "network", "create", network], check=True)
            success(f"Created Docker network: {network}")
        else:
            debug(f"Docker network already exists: {network}")
    except Exception as e:
        error(f"Failed to create Docker network: {e}")

    # Tạo volume FastCGI cache nếu chưa có
    try:
        result = subprocess.run(
            ["docker", "volume", "ls", "--format", "{{.Name}}"], capture_output=True, text=True)
        volumes = result.stdout.strip().splitlines()
        volume_name = "wpdocker_fastcgi_cache_data"
        if volume_name not in volumes:
            subprocess.run(
                ["docker", "volume", "create", volume_name], check=True)
            success(f"Created Docker volume: {volume_name}")
        else:
            debug(f"Docker volume already exists: {volume_name}")
    except Exception as e:
        error(f"Failed to create volume: {e}")

    # Thêm user vào group docker (chỉ trên Linux)
    if platform.system() != "Darwin":
        try:
            user = os.getenv("USER")
            subprocess.run(["sudo", "usermod", "-aG",
                           "docker", user], check=True)
            success(
                f"Added user '{user}' to 'docker' group (may require logout)")
        except Exception as e:
            warn(f"Could not add user to docker group: {e}")
    else:
        debug("macOS detected — skipping usermod for Docker group.")
