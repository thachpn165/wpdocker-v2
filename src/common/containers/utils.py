"""
Container utility functions.

This module provides common utility functions for working with Docker containers.
"""


from src.common.logging import info, error


def handle_container_check(container_manager) -> bool:
    """
    Check if a container is running and start it if necessary.

    Args:
        container_manager: An instance of a container manager class with is_container_running() 
                          and start_container() methods

    Returns:
        bool: True if container is running or was started successfully, False otherwise
    """
    if not container_manager.is_container_running():
        info(f"Starting {container_manager.__class__.__name__.replace('Manager', '')} container...")
        if not container_manager.start_container():
            error("❌ Failed to start container. Please check your Docker configuration.")
            return False
    return True


def ensure_container_running(container_manager, on_failure_callback=None) -> bool:
    """
    Ensure a container is running, with custom failure handling.

    Args:
        container_manager: Container manager instance
        on_failure_callback: Optional callback to execute if container can't be started

    Returns:
        bool: True if container is running or was started successfully, False otherwise
    """
    if not container_manager.is_container_running():
        info(f"Starting {container_manager.__class__.__name__.replace('Manager', '')} container...")
        if not container_manager.start_container():
            error("❌ Failed to start container. Please check your Docker configuration.")
            if on_failure_callback:
                on_failure_callback()
            return False
    return True
