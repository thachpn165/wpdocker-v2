import os
import json
from core.backend.utils.env_utils import env_required
env = env_required([
    "INSTALL_DIR",
])


class Config:
    def __init__(self, config_path=env["INSTALL_DIR"] + "/config/config.json"):
        self.config_path = config_path
        self.data = self.load()

    def load(self):
        with open(self.config_path, "r") as f:
            return json.load(f)

    def save(self):
        with open(self.config_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def get(self, path, fallback=None):
        keys = path.split(".")
        current = self.data
        for key in keys:
            if not isinstance(current, dict):
                return fallback
            current = current.get(key, fallback)
        return current

    def set(self, path, value, split_path=True):
        if split_path:
            keys = path.split(".")
            current = self.data
            for key in keys[:-1]:
                current = current.setdefault(key, {})
            current[keys[-1]] = value
        else:
            self.data[path] = value
        self.save()
