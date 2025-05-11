"""
System management prompt module.

This module provides the user interface for system-specific management functions,
separate from container management.
"""

from questionary import Style
from rich.console import Console

from src.common.logging import Debug
from src.features.system.utils.system_info import show_system_info_table

debug = Debug("SystemToolsPrompt")
# Custom style for the menu
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:cyan bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:green bold'),
    ('selected', 'fg:green bold'),
    ('separator', 'fg:cyan'),
    ('instruction', 'fg:gray'),
    ('text', ''),
    ('disabled', 'fg:gray italic'),
])


def not_implemented() -> None:
    """Handle not implemented features."""
    debug.error("🚧 Feature not implemented yet")
    input("Press Enter to continue...")


def prompt_view_system_info() -> None:
    """Display system information."""
    console = Console()
    show_system_info_table(console)
    input("\nNhấn Enter để quay lại...")


def prompt_clean_docker() -> None:
    """Clean up Docker resources."""
    try:
        # This would implement functions to:
        # - Remove unused images
        # - Remove stopped containers
        # - Clean up volumes
        # - Clear build cache
        not_implemented()
    except Exception as e:
        debug.error(f"Error cleaning Docker resources: {e}")
        input("Press Enter to continue...")


def prompt_update_wpdocker() -> None:
    """Update WP Docker version."""
    try:
        # This would implement the version update functionality
        not_implemented()
    except Exception as e:
        debug.error(f"Error updating WP Docker: {e}")
        input("Press Enter to continue...")


def prompt_rebuild_containers() -> None:
    """Rebuild core containers."""
    try:
        # This would implement container rebuild functionality
        not_implemented()
    except Exception as e:
        debug.error(f"Error rebuilding containers: {e}")
        input("Press Enter to continue...")
