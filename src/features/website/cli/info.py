"""
CLI interface for website information.

This module provides a command-line interface for displaying detailed
information about a website's configuration and status.
"""

import sys
import json
import jsons
from typing import Optional, Dict, Any

from src.common.logging import log_call, info, warn, error, success
from src.common.containers.container import Container
from src.features.website.utils import (
    select_website, 
    get_site_config, 
    is_website_running
)


@log_call
def format_website_info(domain: str) -> Optional[str]:
    """
    Generate a formatted string with website information.
    
    Args:
        domain: Website domain name
        
    Returns:
        Optional[str]: Formatted website information or None if website not found
    """
    site_config = get_site_config(domain)
    if not site_config:
        error(f"No configuration found for website {domain}")
        return None
        
    status = is_website_running(domain)
    
    # Container status
    container_status = "Unknown"
    if site_config.php and site_config.php.php_container:
        container = Container(name=site_config.php.php_container)
        if container.running():
            container_status = "Running"
        elif container.exists():
            container_status = "Stopped"
        else:
            container_status = "Not created"
    
    # Format output
    result = [
        f"🌐 Website: {domain}",
        f"🚦 Status: {status}",
        f"🐳 Container: {site_config.php.php_container if site_config.php else 'None'} ({container_status})",
        f"🐘 PHP Version: {site_config.php.php_version if site_config.php else 'Unknown'}",
    ]
    
    # MySQL info
    if site_config.mysql:
        result.append(f"🗄️ Database: {site_config.mysql.db_name}")
        result.append(f"👤 DB User: {site_config.mysql.db_user}")
        # Don't show password
    
    # Cache config
    if site_config.cache:
        result.append(f"⚡ Cache: {site_config.cache}")
    
    # Backup info
    if site_config.backup and site_config.backup.last_backup:
        result.append("📦 Last Backup:")
        result.append(f"   Time: {site_config.backup.last_backup.time}")
        result.append(f"   File: {site_config.backup.last_backup.file}")
        result.append(f"   Database: {site_config.backup.last_backup.database}")
    
    # Schedule info
    if site_config.backup and site_config.backup.schedule:
        schedule = site_config.backup.schedule
        if schedule.enabled:
            schedule_type = schedule.schedule_type
            time_str = f"{schedule.hour:02d}:{schedule.minute:02d}"
            
            if schedule_type == "daily":
                schedule_info = f"Daily at {time_str}"
            elif schedule_type == "weekly" and schedule.day_of_week is not None:
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                day = days[schedule.day_of_week]
                schedule_info = f"Weekly on {day} at {time_str}"
            elif schedule_type == "monthly" and schedule.day_of_month is not None:
                schedule_info = f"Monthly on day {schedule.day_of_month} at {time_str}"
            else:
                schedule_info = f"{schedule_type} at {time_str}"
                
            result.append("🔄 Backup Schedule:")
            result.append(f"   {schedule_info}")
            result.append(f"   Retention: {schedule.retention_count} backups")
            
            if schedule.cloud_sync and site_config.backup.cloud_config:
                cloud = site_config.backup.cloud_config
                result.append(f"   Cloud Sync: Enabled ({cloud.provider})")
                result.append(f"   Remote: {cloud.remote_name}:{cloud.remote_path}")
    
    # Log paths
    if site_config.logs:
        result.append("📄 Log Files:")
        if site_config.logs.access:
            result.append(f"   Access: {site_config.logs.access}")
        if site_config.logs.error:
            result.append(f"   Error: {site_config.logs.error}")
        if site_config.logs.php_error:
            result.append(f"   PHP Error: {site_config.logs.php_error}")
        if site_config.logs.php_slow:
            result.append(f"   PHP Slow: {site_config.logs.php_slow}")
    
    return "\n".join(result)


@log_call
def get_website_info(domain: str, json_output: bool = False) -> bool:
    """
    Display information about a specific website.
    
    Args:
        domain: Website domain name
        json_output: Whether to output in JSON format
        
    Returns:
        bool: True if information was displayed successfully, False otherwise
    """
    site_config = get_site_config(domain)
    if not site_config:
        error(f"No configuration found for website {domain}")
        return False
    
    if json_output:
        # Convert to JSON and print
        config_dict = jsons.dump(site_config)
        print(json.dumps(config_dict, indent=2))
    else:
        # Format and print human-readable output
        info_text = format_website_info(domain)
        if info_text:
            print(info_text)
        else:
            return False
    
    return True


@log_call
def cli_website_info(json_output: bool = False) -> bool:
    """
    CLI entry point for website information display.
    
    Args:
        json_output: Whether to output in JSON format
        
    Returns:
        bool: True if information was displayed successfully, False otherwise
    """
    domain = select_website("Select website to show information:")
    
    if not domain:
        warn("No website selected or no websites available.")
        return False
        
    return get_website_info(domain, json_output)


if __name__ == "__main__":
    # Check if --json flag is provided
    json_output = "--json" in sys.argv
    success = cli_website_info(json_output)
    sys.exit(0 if success else 1)