"""
Main CLI module for backup operations.

This module provides the primary entry points for backup operations
in the command-line interface, coordinating various backup functionality.
"""

import os
import argparse
from typing import List, Optional, Dict, Any

from src.common.logging import log_call, info, error, success, debug
from src.features.backup.backup_manager import BackupManager
from src.features.website.utils import get_website_list


@log_call
def handle_create(args: argparse.Namespace) -> int:
    """
    Handle backup creation command.
    
    Args:
        args: CLI arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    domain = args.domain
    
    if not domain:
        error("❌ Domain is required")
        return 1
    
    storage_provider = args.provider or "local"
    
    info(f"🚀 Creating backup for website: {domain}")
    info(f"📂 Using storage provider: {storage_provider}")
    
    backup_manager = BackupManager()
    success_result, message = backup_manager.create_backup(domain, storage_provider)
    
    if success_result:
        success(f"✅ {message}")
        return 0
    else:
        error(f"❌ {message}")
        return 1


@log_call
def handle_restore(args: argparse.Namespace) -> int:
    """
    Handle backup restoration command.
    
    Args:
        args: CLI arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    domain = args.domain
    backup_file = args.file
    
    if not domain:
        error("❌ Domain is required")
        return 1
    
    if not backup_file:
        error("❌ Backup file is required")
        return 1
    
    storage_provider = args.provider or "local"
    
    info(f"🔄 Restoring backup for website: {domain}")
    info(f"📁 Backup file: {os.path.basename(backup_file)}")
    info(f"📂 Using storage provider: {storage_provider}")
    
    backup_manager = BackupManager()
    success_result, message = backup_manager.restore_backup(domain, os.path.basename(backup_file), storage_provider)
    
    if success_result:
        success(f"✅ {message}")
        return 0
    else:
        error(f"❌ {message}")
        return 1


@log_call
def handle_list(args: argparse.Namespace) -> int:
    """
    Handle backup listing command.
    
    Args:
        args: CLI arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    domain = args.domain
    storage_provider = args.provider
    
    backup_manager = BackupManager()
    
    # Get available providers
    available_providers = backup_manager.get_available_providers()
    
    if storage_provider and storage_provider not in available_providers:
        error(f"❌ Storage provider '{storage_provider}' not found")
        info(f"Available providers: {', '.join(available_providers)}")
        return 1
    
    info(f"📋 Listing backups" + (f" for {domain}" if domain else "") + 
         (f" from {storage_provider}" if storage_provider else ""))
    
    # Get backups
    backups = backup_manager.list_backups(domain, storage_provider)
    
    if not backups:
        info("No backups found")
        return 0
    
    # Group backups by provider and domain
    grouped_backups: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    
    for backup in backups:
        provider = backup.get("provider", "unknown")
        website = backup.get("website", "unknown")
        
        if provider not in grouped_backups:
            grouped_backups[provider] = {}
        
        if website not in grouped_backups[provider]:
            grouped_backups[provider][website] = []
        
        grouped_backups[provider][website].append(backup)
    
    # Display backups
    for provider_name, websites in grouped_backups.items():
        info(f"\n📂 {provider_name}:")
        
        for website_name, website_backups in websites.items():
            info(f"  📁 {website_name}:")
            
            # Sort by name (most recent first assumes standard naming)
            sorted_backups = sorted(website_backups, key=lambda x: x.get("name", ""), reverse=True)
            
            for i, backup in enumerate(sorted_backups, 1):
                name = backup.get("name", "unknown")
                size = backup.get("size", "unknown")
                modified = backup.get("modified", "unknown")
                modified_str = modified if isinstance(modified, str) else "unknown"
                
                # Classify backup type
                backup_type = "Unknown"
                if name.endswith('.sql'):
                    backup_type = "Database"
                elif name.endswith(('.tar.gz', '.tgz')):
                    backup_type = "Files"
                
                info(f"    {i}. {name} [{backup_type}] - {size} - {modified_str}")
    
    return 0


@log_call
def handle_delete(args: argparse.Namespace) -> int:
    """
    Handle backup deletion command.
    
    Args:
        args: CLI arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    domain = args.domain
    backup_file = args.file
    
    if not domain:
        error("❌ Domain is required")
        return 1
    
    if not backup_file:
        error("❌ Backup file is required")
        return 1
    
    storage_provider = args.provider or "local"
    
    info(f"🗑️ Deleting backup for website: {domain}")
    info(f"📁 Backup file: {backup_file}")
    info(f"📂 From storage provider: {storage_provider}")
    
    backup_manager = BackupManager()
    success_result, message = backup_manager.delete_backup(domain, backup_file, storage_provider)
    
    if success_result:
        success(f"✅ {message}")
        return 0
    else:
        error(f"❌ {message}")
        return 1


@log_call
def handle_schedule(args: argparse.Namespace) -> int:
    """
    Handle backup scheduling command.
    
    Args:
        args: CLI arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    domain = args.domain
    
    if not domain:
        error("❌ Domain is required")
        return 1
    
    # Schedule configuration
    schedule = {
        "enabled": not args.disable,
        "schedule_type": args.schedule_type or "daily",
        "hour": args.hour or 2,
        "minute": args.minute or 0,
        "day_of_week": args.day_of_week,
        "day_of_month": args.day_of_month,
        "retention_count": args.retention_count or 5
    }
    
    # Storage provider
    storage_provider = args.provider or "local"
    
    # Create backup schedule
    info(f"🕒 {'Configuring' if schedule['enabled'] else 'Disabling'} backup schedule for website: {domain}")
    
    if schedule["enabled"]:
        info(f"📂 Using storage provider: {storage_provider}")
        info(f"🔄 Schedule type: {schedule['schedule_type']}")
        
        # Display specific schedule parameters based on type
        if schedule["schedule_type"] == "daily":
            info(f"⏰ Time: {schedule['hour']}:{schedule['minute']:02d}")
        elif schedule["schedule_type"] == "weekly":
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_name = days[schedule["day_of_week"]] if schedule["day_of_week"] in range(7) else "Unknown"
            info(f"📅 Day: {day_name}")
            info(f"⏰ Time: {schedule['hour']}:{schedule['minute']:02d}")
        elif schedule["schedule_type"] == "monthly":
            info(f"📅 Day of month: {schedule['day_of_month']}")
            info(f"⏰ Time: {schedule['hour']}:{schedule['minute']:02d}")
        
        info(f"🗄️ Keep last {schedule['retention_count']} backups")
    
    backup_manager = BackupManager()
    success_result, message = backup_manager.schedule_backup(domain, schedule, storage_provider)
    
    if success_result:
        success(f"✅ {message}")
        return 0
    else:
        error(f"❌ {message}")
        return 1


@log_call
def handle_providers(args: argparse.Namespace) -> int:
    """
    Handle listing available backup providers.
    
    Args:
        args: CLI arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    backup_manager = BackupManager()
    providers = backup_manager.get_available_providers()
    
    info(f"📋 Available backup providers:")
    
    for i, provider in enumerate(providers, 1):
        info(f"{i}. {provider}")
    
    return 0


@log_call
def setup_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Set up the argument parser for backup commands.
    
    Args:
        subparsers: Subparsers object from argparse
    """
    # Create backup parser
    backup_parser = subparsers.add_parser(
        "backup", 
        help="Manage website backups"
    )
    backup_subparsers = backup_parser.add_subparsers(dest="backup_action", help="Backup action")
    
    # Create backup command
    create_parser = backup_subparsers.add_parser("create", help="Create a backup")
    create_parser.add_argument("domain", help="Website domain")
    create_parser.add_argument("--provider", "-p", help="Storage provider")
    create_parser.set_defaults(func=handle_create)
    
    # Restore backup command
    restore_parser = backup_subparsers.add_parser("restore", help="Restore a backup")
    restore_parser.add_argument("domain", help="Website domain")
    restore_parser.add_argument("file", help="Backup file name")
    restore_parser.add_argument("--provider", "-p", help="Storage provider")
    restore_parser.set_defaults(func=handle_restore)
    
    # List backups command
    list_parser = backup_subparsers.add_parser("list", help="List backups")
    list_parser.add_argument("--domain", "-d", help="Filter by website domain")
    list_parser.add_argument("--provider", "-p", help="Filter by storage provider")
    list_parser.set_defaults(func=handle_list)
    
    # Delete backup command
    delete_parser = backup_subparsers.add_parser("delete", help="Delete a backup")
    delete_parser.add_argument("domain", help="Website domain")
    delete_parser.add_argument("file", help="Backup file name")
    delete_parser.add_argument("--provider", "-p", help="Storage provider")
    delete_parser.set_defaults(func=handle_delete)
    
    # Schedule backup command
    schedule_parser = backup_subparsers.add_parser("schedule", help="Schedule backups")
    schedule_parser.add_argument("domain", help="Website domain")
    schedule_parser.add_argument("--disable", action="store_true", help="Disable scheduled backups")
    schedule_parser.add_argument("--schedule-type", choices=["daily", "weekly", "monthly"], help="Schedule type")
    schedule_parser.add_argument("--hour", type=int, help="Hour (0-23)")
    schedule_parser.add_argument("--minute", type=int, help="Minute (0-59)")
    schedule_parser.add_argument("--day-of-week", type=int, help="Day of week (0=Monday, 6=Sunday)")
    schedule_parser.add_argument("--day-of-month", type=int, help="Day of month (1-31)")
    schedule_parser.add_argument("--retention-count", type=int, help="Number of backups to keep")
    schedule_parser.add_argument("--provider", "-p", help="Storage provider")
    schedule_parser.set_defaults(func=handle_schedule)
    
    # List providers command
    providers_parser = backup_subparsers.add_parser("providers", help="List available storage providers")
    providers_parser.set_defaults(func=handle_providers)


@log_call
def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the backup CLI.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Manage website backups")
    
    # Set up subparsers
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")
    
    # Set up backup parser
    setup_parser(subparsers)
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    # Handle command
    if hasattr(parsed_args, "func"):
        return parsed_args.func(parsed_args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit(main())