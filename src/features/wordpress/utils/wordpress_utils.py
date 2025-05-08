import subprocess
from src.common.logging import info, error
from src.features.website.utils import get_site_config

WP_PATH_TEMPLATE = "/data/sites/{domain}/wordpress"

CACHE_PLUGINS = [
    "redis-cache", "wp-super-cache", "w3-total-cache", "wp-fastest-cache"
]

def get_wp_path(domain: str) -> str:
    return WP_PATH_TEMPLATE.format(domain=domain)

def get_active_plugins(domain: str) -> list:
    wp_path = get_wp_path(domain)
    cmd = [
        "wp", "plugin", "list", "--status=active", "--field=name", f"--path={wp_path}"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip().splitlines()
    except Exception as e:
        error(f"Error getting active plugins: {e}")
        return []

def deactivate_all_cache_plugins(domain: str) -> bool:
    active_plugins = get_active_plugins(domain)
    wp_path = get_wp_path(domain)
    for plugin in CACHE_PLUGINS:
        if plugin in active_plugins:
            cmd = ["wp", "plugin", "deactivate", plugin, f"--path={wp_path}"]
            try:
                subprocess.run(cmd, check=True)
                info(f"Deactivated plugin: {plugin}")
            except Exception as e:
                error(f"Failed to deactivate {plugin}: {e}")
                return False
    return True

def install_and_activate_plugin(domain: str, plugin_slug: str) -> bool:
    wp_path = get_wp_path(domain)
    try:
        subprocess.run(["wp", "plugin", "install", plugin_slug, "--activate", f"--path={wp_path}"], check=True)
        info(f"Installed and activated plugin: {plugin_slug}")
        return True
    except Exception as e:
        error(f"Failed to install/activate {plugin_slug}: {e}")
        return False

def update_wp_config_cache(domain: str, cache_type: str) -> bool:
    wp_path = get_wp_path(domain)
    wp_config = f"{wp_path}/wp-config.php"
    try:
        with open(wp_config, "r") as f:
            lines = f.readlines()
        # Remove old WP_CACHE define
        lines = [l for l in lines if "define('WP_CACHE'" not in l]
        # Add new define at the top after <?php
        for i, l in enumerate(lines):
            if l.strip().startswith("<?php"):
                lines.insert(i+1, f"define('WP_CACHE', true); // {cache_type}\n")
                break
        with open(wp_config, "w") as f:
            f.writelines(lines)
        info(f"Updated wp-config.php for cache: {cache_type}")
        return True
    except Exception as e:
        error(f"Failed to update wp-config.php: {e}")
        return False 