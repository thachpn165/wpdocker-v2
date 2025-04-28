import os
import json
from core.backend.utils.env_utils import env_required

env = env_required([
    "INSTALL_DIR",
])

class Config:
    def __init__(self, config_path=None):
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = os.path.join(env["INSTALL_DIR"], "config", "config.json")
        self.config = self.load()

    def load(self):
        if not os.path.isfile(self.config_path):
            return {}
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def save(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def get(self, key, default=None, split_path=True):
        keys = key.split('.') if split_path else [key]
        ref = self.config
        for k in keys:
            if isinstance(ref, dict) and k in ref:
                ref = ref[k]
            else:
                return default
        return ref

    def set(self, key, value, split_path=True):
        keys = key.split('.') if split_path else [key]
        ref = self.config
        for k in keys[:-1]:
            ref = ref.setdefault(k, {})
        ref[keys[-1]] = value