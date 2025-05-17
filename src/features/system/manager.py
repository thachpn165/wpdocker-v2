from typing import List
from src.common.config.manager import ConfigManager
import subprocess
import os
from src.common.logging import info, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
import json

LANG_CONFIG_PATH = os.path.expanduser("~/wpdocker-v2/data/core.language.json")


class SystemManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_core_containers(self):
        config = ConfigManager().get()
        return config.get("core", {}).get("containers", [])

    @with_pause
    def rebuild_core_containers(self, container_names: List[str], interactive: bool = True) -> bool:
        containers = self.get_core_containers()
        name_to_compose = {c["name"]: c["compose_file"] for c in containers}
        ok = True
        for name in container_names:
            compose_file = name_to_compose.get(name)
            if not compose_file or not os.path.exists(compose_file):
                error(f"❌ Compose file not found for container {name}")
                ok = False
                continue
            info(f"🔄 Rebuilding container {name} ...")
            try:
                subprocess.run(
                    ["docker", "compose", "-f", compose_file, "up", "--build", "-d"],
                    check=True
                )
                success(f"✅ Container {name} rebuilt successfully")
            except Exception as e:
                error(f"❌ Error rebuilding container {name}: {e}")
                ok = False
        return ok

    def set_language(self, lang_code: str):
        config_mgr = ConfigManager()
        config = config_mgr.get()
        if "core" not in config:
            config["core"] = {}
        config["core"]["lang"] = lang_code
        config_mgr.save()

    def get_language(self) -> str:
        config_mgr = ConfigManager()
        config = config_mgr.get()
        return config.get("core", {}).get("lang", "en")
