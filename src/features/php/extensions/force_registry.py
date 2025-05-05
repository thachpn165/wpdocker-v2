"""
Force registry to load all extensions.

This module ensures all extension modules are properly imported and registered
to avoid issues with empty extension registry.
"""

from src.common.logging import debug, info, warn, error

# Explicitly import the ioncube_loader module
import src.features.php.extensions.ioncube_loader

# Import registry to access the extension list
from src.features.php.extensions.registry import EXTENSION_REGISTRY


def ensure_extensions_loaded():
    """
    Ensure all extensions are properly loaded and registered.
    
    This function should be called at application startup to verify
    that the extension registry has been populated.
    """
    # Check if registry has extensions
    extension_count = len(EXTENSION_REGISTRY)
    
    if extension_count == 0:
        error("❌ No PHP extensions found in registry. This is unexpected.")
        # Try reimporting modules
        try:
            reload_module(src.features.php.extensions.ioncube_loader)
            extension_count = len(EXTENSION_REGISTRY)
        except Exception as e:
            error(f"❌ Failed to reload extension modules: {e}")
    
    info(f"✅ PHP Extension registry contains {extension_count} extensions: {list(EXTENSION_REGISTRY.keys())}")


def reload_module(module):
    """
    Reload a module to ensure all its contents are processed.
    
    Args:
        module: Module to reload
    """
    import importlib
    importlib.reload(module)


# Automatically run the check when this module is imported
ensure_extensions_loaded()