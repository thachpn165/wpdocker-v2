import subprocess
import os

class Container:
    def __init__(self, name, template_path, output_path, env_map, sensitive_env=None):
        self.name = name
        self.template_path = template_path
        self.output_path = output_path
        self.env_map = env_map
        self.sensitive_env = sensitive_env or {}

    def exists(self):
        result = subprocess.run(["docker", "ps", "-a", "-q", "-f", f"name=^{self.name}$"],
                                capture_output=True, text=True)
        return result.stdout.strip() != ""

    def generate_compose_file(self):
        with open(self.template_path, "r") as f:
            content = f.read()

        for key, value in self.env_map.items():
            content = content.replace(f"${{{key}}}", value)

        for key, value in self.sensitive_env.items():
            content = content.replace(f"${{{key}}}", value)

        with open(self.output_path, "w") as f:
            f.write(content)

    def up(self):
        subprocess.run(["docker", "compose", "-f", self.output_path, "up", "-d"], check=True)