import os
import sys

def env_required(keys):
    env = {}
    missing = []

    for key in keys:
        value = os.getenv(key)
        if value is None:
            missing.append(key)
        else:
            env[key] = value

    if missing:
        print(f"❌ Thiếu biến môi trường: {', '.join(missing)}")
        sys.exit(1)

    return env