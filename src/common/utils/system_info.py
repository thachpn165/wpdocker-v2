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
def get_used_ram_mb() -> int:
    """
    Get the used system RAM in megabytes.

    Returns:
        Used RAM in MB
    """
    try:
        if os.path.exists('/proc/meminfo'):
            # Linux
            mem_info = {}
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        key = parts[0].strip()
                        value = parts[1].split()[0].strip()
                        mem_info[key] = int(value)

            # MemUsed = MemTotal - MemFree - Buffers - Cached
            if all(k in mem_info for k in ('MemTotal', 'MemFree', 'Buffers', 'Cached')):
                used = mem_info['MemTotal'] - mem_info['MemFree'] - mem_info['Buffers'] - mem_info['Cached']
                return used // 1024
            else:
                # Fallback if keys are missing
                return mem_info.get('MemTotal', 0) - mem_info.get('MemFree', 0) // 1024
        else:
            # macOS
            output = subprocess.check_output(['vm_stat']).decode()
            pages_used = 0
            page_size = 4096  # Default page size (4KB)

            # Get page size
            try:
                page_size_output = subprocess.check_output(['sysctl', 'vm.pagesize']).decode()
                page_size = int(page_size_output.split(':')[1].strip())
            except:
                pass

            for line in output.splitlines():
                if 'Pages active' in line or 'Pages wired down' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        pages_used += int(parts[1].strip().rstrip('.'))

            return (pages_used * page_size) // (1024 * 1024)
    except Exception as e:
        return 0

@log_call
def get_cpu_info() -> Dict[str, Any]:
    """
    Get CPU information including model and speed.

    Returns:
        Dictionary with CPU info (model, speed, cores)
    """
    info = {
        'cores': get_total_cpu_cores(),
        'model': 'Unknown',
        'speed': 'Unknown'
    }

    try:
        import platform
        if platform.system() == 'Darwin':  # macOS
            output = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string']).decode().strip()
            info['model'] = output

            # Try to get CPU speed
            try:
                speed_output = subprocess.check_output(['sysctl', '-n', 'hw.cpufrequency']).decode().strip()
                speed_mhz = int(speed_output) / 1000000
                info['speed'] = f"{speed_mhz:.2f} GHz"
            except:
                pass

        elif platform.system() == 'Linux':  # Linux
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        info['model'] = line.split(':')[1].strip()
                        break

            # Try to get CPU speed from cpuinfo
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'cpu MHz' in line:
                            speed_mhz = float(line.split(':')[1].strip())
                            info['speed'] = f"{speed_mhz / 1000:.2f} GHz"
                            break
            except:
                pass
    except Exception as e:
        pass

    return info

@log_call
def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information.

    Returns:
        Dictionary with system information (RAM, CPU, etc.)
    """
    info = {
        'ram_total_mb': get_total_ram_mb(),
        'ram_used_mb': get_used_ram_mb(),
        'cpu': get_cpu_info(),
    }

    # Add OS information if available
    try:
        import platform
        info['os'] = platform.system()
        info['os_version'] = platform.version()
        info['architecture'] = platform.machine()
    except ImportError:
        pass

    # Add docker information if available
    try:
        docker_version = subprocess.check_output(['docker', '--version']).decode().strip()
        info['docker'] = docker_version
    except:
        info['docker'] = 'Unknown'

    return info

@log_call
def format_system_info() -> Dict[str, str]:
    """
    Format system information into human-readable strings.

    Returns:
        Dictionary with formatted system information
    """
    info = get_system_info()

    # Format RAM
    ram_total = info['ram_total_mb']
    ram_used = info['ram_used_mb']

    if ram_total >= 1024:
        ram_total_str = f"{ram_total / 1024:.1f} GB"
    else:
        ram_total_str = f"{ram_total} MB"

    if ram_used >= 1024:
        ram_used_str = f"{ram_used / 1024:.1f} GB"
    else:
        ram_used_str = f"{ram_used} MB"

    ram_percent = (ram_used / ram_total) * 100 if ram_total > 0 else 0

    # Format CPU
    cpu_model = info['cpu']['model']
    cpu_speed = info['cpu']['speed']
    cpu_cores = info['cpu']['cores']

    # Simplify CPU model if it's too long
    if len(cpu_model) > 30:
        cpu_model = ' '.join(cpu_model.split()[:3]) + "..."

    return {
        'ram': f"{ram_used_str} / {ram_total_str} ({ram_percent:.1f}%)",
        'cpu': f"{cpu_model} ({cpu_speed}, {cpu_cores} cores)",
        'os': f"{info['os']} {info['architecture']}",
        'docker': info['docker']
    }