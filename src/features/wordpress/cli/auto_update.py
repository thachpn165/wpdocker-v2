import click
from src.common.logging import success, error
from src.features.wordpress.actions import (
    toggle_theme_auto_update_action,
    toggle_plugin_auto_update_action,
)

def cli_toggle_theme_auto_update(domain: str, interactive: bool = True) -> bool:
    result = toggle_theme_auto_update_action(domain)
    if result:
        success(f"Toggled theme auto update for {domain}")
    else:
        error(f"Failed to toggle theme auto update for {domain}")
    return result

def cli_toggle_plugin_auto_update(domain: str, interactive: bool = True) -> bool:
    result = toggle_plugin_auto_update_action(domain)
    if result:
        success(f"Toggled plugin auto update for {domain}")
    else:
        error(f"Failed to toggle plugin auto update for {domain}")
    return result

# Click commands (có thể bổ sung sau) 