"""
Environment utilities for managing configuration and environment variables.

This module provides functions for working with environment variables and 
configuration files, including loading environment variables from files,
validating required variables, and accessing variable values.
"""

import os
import sys
from typing import Dict, List, Optional, Any

def load_environment(env_file: str = None) -> Dict[str, str]:
    """
    Load environment variables from a specified file.
    
    Args:
        env_file: Path to environment file. If None, uses fixed path at /opt/wp-docker/core.env.
        
    Returns:
        Dictionary containing environment variables and their values.
    """
    if env_file is None:
        # Use a fixed path for the core.env file
        fixed_env_file = "/opt/wp-docker/core.env"
        env_file = fixed_env_file
    
    if not os.path.isfile(env_file):
        # If the file is not found at the fixed path
        print(f"Warning: Configuration file not found at fixed path: {env_file}")
        
        # Fallback: try to find it in the current directory or parent directory
        fallback_paths = [
            os.path.join(os.getcwd(), "core.env"),  # Current directory
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../core.env")),  # Parent directory of src
        ]
        
        for path in fallback_paths:
            if os.path.isfile(path):
                print(f"Using fallback configuration file at: {path}")
                env_file = path
                break
        else:
            print(f"No configuration file found. Using empty configuration.")
            return {}

    result = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    return result


# Global environment variables
env = load_environment()


def env_required(keys: List[str]) -> Dict[str, str]:
    """
    Verify required environment variables are present.
    
    Args:
        keys: List of required environment variable keys
        
    Returns:
        Dictionary of required environment variables and their values
        
    Raises:
        SystemExit: If any required variables are missing
    """
    result = {}
    missing = []

    for key in keys:
        value = env.get(key)
        if value is None:
            missing.append(key)
        else:
            result[key] = value

    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    return result


def get_env_value(key: str, default: Optional[Any] = None) -> Any:
    """
    Get the value of an environment variable.
    
    Args:
        key: Name of the environment variable
        default: Default value if the variable doesn't exist
        
    Returns:
        Value of the environment variable or the default value
    """
    return env.get(key, default)