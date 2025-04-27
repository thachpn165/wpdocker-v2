import os
import json

class Config:
    def __init__(self, config_path="/app/config/config.json"):
        self.config_path = config_path
        self.data = {}
        self.load()

    def load(self):
        if not os.path.exists(self.config_path):
            self.data = {}
            return
        with open(self.config_path, "r") as f:
            try:
                self.data = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ File config bị lỗi định dạng JSON: {self.config_path}")
                self.data = {}

    def save(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def get(self, path, fallback=None):
        keys = path.split(".")
        current = self.data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return fallback
        return current

    def set(self, path, value):
        keys = path.split(".")
        current = self.data
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = value