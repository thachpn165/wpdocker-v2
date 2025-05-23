"""
Container path utilities.

This module provides utilities for path conversion between host and container
environments, allowing files to be referenced correctly in each context.
"""

from typing import Dict

from src.common.logging import Debug
from src.common.utils.environment import env


# Mapping for known container path mappings
# Format: {'container_name': {'host_path': 'container_path', ...}}
CONTAINER_PATH_MAPPINGS: Dict[str, Dict[str, str]] = {
    'rclone': {
        '/opt/wp-docker/data': '/data',
        '/opt/wp-docker': '/'
    },
    'php': {
        '/opt/wp-docker/data': '/var/www/html',
        '/opt/wp-docker': '/'
    },
    'mysql': {
        '/opt/wp-docker/data/mysql': '/var/lib/mysql',
        '/opt/wp-docker/data': '/data'
    },
    'nginx': {
        '/opt/wp-docker/data/sites': '/var/www/html',
        '/opt/wp-docker/data': '/data'
    }
}


def convert_host_path_to_container(host_path: str, container_type: str = 'rclone') -> str:
    """
    Convert host path to container path based on the container type.

    Args:
        host_path: Path on the host system
        container_type: Type of container ('rclone', 'php', 'mysql', 'nginx', etc.)

    Returns:
        Path as it would be seen inside the specified container
    """
    debug = Debug("ContainerUtils")

    # If container type not in our mapping, return the original path
    if container_type not in CONTAINER_PATH_MAPPINGS:
        debug.warn(f"No path mapping defined for container type: {container_type}")
        return host_path

    mappings = CONTAINER_PATH_MAPPINGS[container_type]

    # Try to find the longest matching prefix
    matching_prefix = ""
    container_path = host_path

    for host_prefix, container_prefix in mappings.items():
        if host_path.startswith(host_prefix) and len(host_prefix) > len(matching_prefix):
            matching_prefix = host_prefix
            container_path = host_path.replace(host_prefix, container_prefix)

    if matching_prefix:
        debug.info(f"Converted path for {container_type}: {host_path} → {container_path}")
    else:
        debug.info(f"No mapping found for {host_path} in {container_type} container")

    return container_path


def convert_container_path_to_host(container_path: str, container_type: str = 'rclone') -> str:
    """
    Convert container path to host path based on the container type.

    Args:
        container_path: Path inside the container
        container_type: Type of container ('rclone', 'php', 'mysql', 'nginx', etc.)

    Returns:
        Path as it would be seen on the host system
    """
    debug = Debug("ContainerUtils")

    # If container type not in our mapping, return the original path
    if container_type not in CONTAINER_PATH_MAPPINGS:
        debug.warn(f"No path mapping defined for container type: {container_type}")
        return container_path

    mappings = CONTAINER_PATH_MAPPINGS[container_type]

    # Create reverse mappings
    reverse_mappings = {container: host for host, container in mappings.items()}

    # Try to find the longest matching prefix
    matching_prefix = ""
    host_path = container_path

    for container_prefix, host_prefix in reverse_mappings.items():
        if container_path.startswith(container_prefix) and len(container_prefix) > len(matching_prefix):
            matching_prefix = container_prefix
            host_path = container_path.replace(container_prefix, host_prefix)

    if matching_prefix:
        debug.info(f"Converted path for {container_type}: {container_path} → {host_path}")
    else:
        debug.info(f"No mapping found for {container_path} in {container_type} container")

    return host_path


def get_container_volumes(container_type: str = 'rclone') -> Dict[str, str]:
    """
    Get the volume mappings for a specific container type.

    Args:
        container_type: Type of container ('rclone', 'php', 'mysql', 'nginx', etc.)

    Returns:
        Dictionary of host_path: container_path mappings
    """
    if container_type in CONTAINER_PATH_MAPPINGS:
        return CONTAINER_PATH_MAPPINGS[container_type]
    else:
        return {}


def update_container_mapping(container_type: str, host_path: str, container_path: str) -> None:
    """
    Add or update a path mapping for a container type.

    Args:
        container_type: Type of container ('rclone', 'php', 'mysql', 'nginx', etc.)
        host_path: Path on the host system
        container_path: Corresponding path inside the container
    """
    if container_type not in CONTAINER_PATH_MAPPINGS:
        CONTAINER_PATH_MAPPINGS[container_type] = {}

    CONTAINER_PATH_MAPPINGS[container_type][host_path] = container_path
    Debug("ContainerUtils").info(f"Added mapping for {container_type}: {host_path} → {container_path}")


def initialize_container_mappings() -> None:
    """
    Initialize container path mappings based on environment variables.

    This ensures paths are correctly mapped even when the install directory
    is not the default.
    """
    debug = Debug("ContainerUtils")
    debug.info("Initializing container path mappings")

    # Get install directory from environment
    install_dir = env.get("INSTALL_DIR", "/opt/wp-docker")
    # data_dir = env.get("DATA_DIR", f"{install_dir}/data")

    # Update mappings for all container types
    global CONTAINER_PATH_MAPPINGS

    for container_type in CONTAINER_PATH_MAPPINGS:
        # Create new mappings dictionary
        new_mappings = {}

        # Update each path in the mappings
        for host_path, container_path in CONTAINER_PATH_MAPPINGS[container_type].items():
            if host_path.startswith("/opt/wp-docker"):
                # Replace default install dir with actual install dir
                new_host_path = host_path.replace("/opt/wp-docker", install_dir)
                new_mappings[new_host_path] = container_path
                debug.debug(f"Updated mapping for {container_type}: {new_host_path} → {container_path}")
            else:
                # Keep original mapping
                new_mappings[host_path] = container_path

        # Replace old mappings with new ones
        CONTAINER_PATH_MAPPINGS[container_type] = new_mappings

    debug.success("Container path mappings initialized")
