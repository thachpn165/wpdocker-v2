"""
CLI interface for viewing website logs.

This module provides a command-line interface for viewing and managing
website logs, including NGINX access and error logs and PHP error logs.
"""

import os
import sys
import subprocess
from questionary import select
from typing import Optional, Dict, Any, List

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import select_website, get_site_config


@log_call
def get_log_options(domain: str) -> Optional[Dict[str, str]]:
    """
    Get available log file options for a website.
    
    Args:
        domain: Website domain name
        
    Returns:
        Optional[Dict[str, str]]: Dictionary mapping log type to file path,
                                 or None if no logs are available
    """
    site_config = get_site_config(domain)
    if not site_config or not site_config.logs:
        error(f"No log configuration found for website {domain}")
        return None
    
    logs = {}
    
    if site_config.logs.access and os.path.exists(site_config.logs.access):
        logs["NGINX Access Log"] = site_config.logs.access
    
    if site_config.logs.error and os.path.exists(site_config.logs.error):
        logs["NGINX Error Log"] = site_config.logs.error
    
    if site_config.logs.php_error and os.path.exists(site_config.logs.php_error):
        logs["PHP Error Log"] = site_config.logs.php_error
    
    if site_config.logs.php_slow and os.path.exists(site_config.logs.php_slow):
        logs["PHP Slow Log"] = site_config.logs.php_slow
    
    return logs if logs else None


@log_call
def view_log(log_path: str, lines: int = 100, follow: bool = False) -> bool:
    """
    View a log file using the tail command.
    
    Args:
        log_path: Path to the log file
        lines: Number of lines to display
        follow: Whether to follow the log (tail -f)
        
    Returns:
        bool: True if log viewing was successful, False otherwise
    """
    if not os.path.exists(log_path):
        error(f"Log file does not exist: {log_path}")
        return False
    
    try:
        cmd = ["tail", f"-n{lines}"]
        if follow:
            cmd.append("-f")
        cmd.append(log_path)
        
        # When running tail -f, we need to handle keyboard interrupt
        if follow:
            try:
                subprocess.run(cmd)
            except KeyboardInterrupt:
                info("\nLog viewing stopped.")
        else:
            subprocess.run(cmd)
        
        return True
    except Exception as e:
        error(f"Error viewing log: {e}")
        return False


@log_call
def prompt_log_options(domain: str) -> Optional[Dict[str, Any]]:
    """
    Prompt the user to select a log file and viewing options.
    
    Args:
        domain: Website domain name
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary with log path and options if successful,
                                None if cancelled
    """
    log_options = get_log_options(domain)
    if not log_options:
        warn(f"No log files found for website {domain}")
        return None
    
    try:
        # Select log type
        log_types = list(log_options.keys())
        log_type = select(
            "Select log file to view:",
            choices=log_types
        ).ask()
        
        if not log_type:
            return None
        
        log_path = log_options[log_type]
        
        # Select viewing options
        view_options = [
            "View last 100 lines",
            "View last 500 lines",
            "View last 1000 lines",
            "Follow log (live updates, Ctrl+C to stop)"
        ]
        
        view_option = select(
            "Select viewing option:",
            choices=view_options
        ).ask()
        
        if not view_option:
            return None
        
        # Parse options
        follow = "Follow" in view_option
        if "100" in view_option:
            lines = 100
        elif "500" in view_option:
            lines = 500
        elif "1000" in view_option:
            lines = 1000
        else:
            lines = 50  # Default for follow mode
        
        return {
            "log_path": log_path,
            "lines": lines,
            "follow": follow
        }
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def cli_view_logs() -> bool:
    """
    CLI entry point for viewing website logs.
    
    Returns:
        bool: True if log viewing was successful, False otherwise
    """
    domain = select_website("Select website to view logs:")
    
    if not domain:
        warn("No website selected or no websites available.")
        return False
    
    log_options = prompt_log_options(domain)
    if not log_options:
        return False
    
    return view_log(
        log_options["log_path"],
        log_options["lines"],
        log_options["follow"]
    )


if __name__ == "__main__":
    success = cli_view_logs()
    sys.exit(0 if success else 1)