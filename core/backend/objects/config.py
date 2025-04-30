import os
import json
from core.backend.utils.env_utils import env_required

env = env_required(["INSTALL_DIR"])


class Config:
    def __init__(self, config_path=None):
        self.config_path = config_path or os.path.join(env["INSTALL_DIR"], "config", "config.json")
        self.config = self._load()

    def _load(self):
        if not os.path.isfile(self.config_path):
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def save(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def reload(self):
        """Tải lại config từ file (nếu cần cập nhật ngoài luồng)."""
        self.config = self._load()

    def get(self):
        """Trả về toàn bộ dict config (dùng để đọc site/core/...)"""
        return self.config

    def update_key(self, key: str, value):
        """Ghi đè 1 key gốc (vd: 'core', 'site') trong config"""
        self.config[key] = value

    def delete_key(self, key: str):
        if key in self.config:
            del self.config[key]