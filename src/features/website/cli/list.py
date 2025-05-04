"""
CLI interface for listing websites.

This module provides a command-line interface for displaying a list of all
websites in the system with their current status.
"""

import sys
import json
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import website_list, is_website_running


@log_call
def get_websites_with_status() -> List[Dict[str, Any]]:
    """
    Get a list of all websites with their status.
    
    Returns:
        List[Dict[str, Any]]: List of dictionaries with domain and status for each website
    """
    domains = website_list()
    result = []
    
    for domain in domains:
        status = is_website_running(domain)
        result.append({
            "domain": domain,
            "status": status
        })
    
    return result


@log_call
def format_website_list(websites: List[Dict[str, Any]]) -> None:
    """
    Format a list of websites for display using Rich.
    
    Args:
        websites: List of website dictionaries with domain and status
    """
    console = Console()
    
    if not websites:
        console.print("No websites found.", style="bold red")
        return
    
    # Create a table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Domain", style="bold white")
    table.add_column("Status", style="bold white")
    
    for site in websites:
        domain = site["domain"]
        status = site["status"]
        
        # Set color based on status
        status_style = "green" if "✅" in status else "red"
        
        table.add_row(domain, f"[{status_style}]{status}[/{status_style}]")
    
    console.print(table)


@log_call
def list_websites(json_output: bool = False) -> bool:
    """
    Display a list of websites with their status.
    
    Args:
        json_output: Whether to output in JSON format
        
    Returns:
        bool: True if listing was successful, False otherwise
    """
    try:
        websites = get_websites_with_status()
        
        if json_output:
            print(json.dumps(websites, indent=2))
        else:
            format_website_list(websites)
        
        return True
    except Exception as e:
        error(f"Error listing websites: {e}")
        return False


@log_call
def cli_list_websites() -> bool:
    """
    CLI entry point for website listing.
    
    Returns:
        bool: True if listing was successful, False otherwise
    """
    # Check if --json flag is provided
    json_output = "--json" in sys.argv
    return list_websites(json_output)


if __name__ == "__main__":
    success = cli_list_websites()
    sys.exit(0 if success else 1)