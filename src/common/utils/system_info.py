"""
System information utilities.

This module provides functions for retrieving system resource information
like RAM, CPU cores, and other hardware details.
"""

import os
import subprocess
from typing import Optional, Dict, Any

from src.common.logging import log_call


@log_call
def get_total_ram_mb() -> int:
    """
    Get the total system RAM in megabytes.
    
    Returns:
        Total RAM in MB
    """
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemTotal' in line:
                    return int(line.split()[1]) // 1024
    except FileNotFoundError:
        # Fallback for macOS (no /proc)
        output = subprocess.check_output(['sysctl', 'hw.memsize']).decode()
        return int(output.split(":")[1].strip()) // (1024 * 1024)
    return 1024  # Default fallback


@log_call
def get_total_cpu_cores() -> int:
    """
    Get the total number of CPU cores.
    
    Returns:
        Number of CPU cores
    """
    return os.cpu_count() or 2  # Default to 2 if detection fails


@log_call
def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information.
    
    Returns:
        Dictionary with system information (RAM, CPU, etc.)
    """
    info = {
        'ram_mb': get_total_ram_mb(),
        'cpu_cores': get_total_cpu_cores(),
    }
    
    # Add OS information if available
    try:
        import platform
        info['os'] = platform.system()
        info['os_version'] = platform.version()
        info['architecture'] = platform.machine()
    except ImportError:
        pass
        
    return info