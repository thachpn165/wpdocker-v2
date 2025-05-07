"""
Cron job management menu prompt module.

This module provides the user interface for cron job management functions
like listing, enabling/disabling, and deleting tasks.
"""

import os
import questionary
from questionary import Style
from typing import Optional, Dict, Any, List
from datetime import datetime

# Try to import humanize, but gracefully handle if not available
try:
    import humanize
    HUMANIZE_AVAILABLE = True
except ImportError:
    HUMANIZE_AVAILABLE = False

from src.common.logging import info, error, debug, success, warn
from src.features.cron.cron_manager import CronManager
from src.features.cron.models.cron_job import CronJob
from src.features.cron import job_registry

# Custom style for the menu
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:cyan bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:green bold'),
    ('selected', 'fg:green bold'),
    ('separator', 'fg:cyan'),
    ('instruction', 'fg:gray'),
    ('text', ''),
    ('disabled', 'fg:gray italic'),
])

def display_job_info(job: CronJob) -> None:
    """
    Display detailed information about a job.
    
    Args:
        job: CronJob object to display
    """
    status_symbol = "✅" if job.enabled else "❌"
    
    # Create a human-readable description of the schedule
    schedule_desc = ""
    if job.schedule == "0 0 * * *":
        schedule_desc = "Daily at midnight"
    elif job.schedule == "0 2 * * *":
        schedule_desc = "Daily at 2:00 AM"
    elif job.schedule.startswith("0 0 * * 0"):
        schedule_desc = "Weekly on Sunday at midnight"
    elif job.schedule.startswith("0 0 1 * *"):
        schedule_desc = "Monthly on the 1st at midnight"
    else:
        schedule_desc = f"Custom schedule: {job.schedule}"
    
    # Format dates
    created_at = job.created_at or "Unknown"
    last_run = job.last_run or "Never"
    
    # Try to make dates relative for better readability
    if HUMANIZE_AVAILABLE:
        try:
            if job.created_at:
                dt = datetime.strptime(job.created_at, "%Y-%m-%d %H:%M:%S")
                created_at = f"{job.created_at} ({humanize.naturaltime(dt)})"
            
            if job.last_run:
                dt = datetime.strptime(job.last_run, "%Y-%m-%d %H:%M:%S")
                last_run = f"{job.last_run} ({humanize.naturaltime(dt)})"
        except (ValueError, AttributeError):
            # If date format is wrong, use the original strings
            pass
    
    # Format last status with color indicator
    last_status = job.last_status or "Unknown"
    if last_status == "success":
        last_status = "✅ Success"
    elif last_status == "failure":
        last_status = "❌ Failed"
    elif last_status == "running":
        last_status = "🔄 Running"
    
    # Display information
    info(f"\n{'='*78}")
    info(f"Job ID: {job.id} {status_symbol}")
    info(f"Description: {job.description or 'No description'}")
    info(f"Type: {job.job_type}")
    info(f"Target: {job.target_id}")
    info(f"Schedule: {schedule_desc}")
    
    # Display parameters if any
    if job.parameters:
        info("Parameters:")
        for key, value in job.parameters.items():
            info(f"  - {key}: {value}")
    
    info(f"Created: {created_at}")
    info(f"Last Run: {last_run}")
    info(f"Last Status: {last_status}")
    info(f"{'='*78}")

def list_cron_jobs() -> None:
    """List all cron jobs."""
    info("\n📋 Scheduled Tasks List")
    
    manager = CronManager()
    jobs = manager.list_jobs()
    
    if not jobs:
        info("No scheduled tasks found.")
        input("\nPress Enter to continue...")
        return
    
    # Group jobs by type for better organization
    grouped_jobs: Dict[str, List[CronJob]] = {}
    for job in jobs:
        job_type = job.job_type
        if job_type not in grouped_jobs:
            grouped_jobs[job_type] = []
        grouped_jobs[job_type].append(job)
    
    # Display jobs by group
    for job_type, job_list in grouped_jobs.items():
        info(f"\n📁 {job_type.capitalize()} Tasks:")
        
        for i, job in enumerate(sorted(job_list, key=lambda j: j.created_at or "", reverse=True), 1):
            status = "✅ Enabled" if job.enabled else "❌ Disabled"
            last_run = job.last_run or "Never"
            desc = job.description or f"{job.job_type} - {job.target_id}"
            info(f"  {i}. {status} {desc}")
    
    # Option to view job details
    should_view_details = questionary.confirm(
        "Would you like to view details of a specific task?",
        style=custom_style,
        default=False
    ).ask()
    
    if should_view_details:
        # Create job choices
        job_choices = []
        for job in jobs:
            status = "✅" if job.enabled else "❌"
            desc = job.description or f"{job.job_type} - {job.target_id}"
            job_choices.append({"name": f"{status} {desc}", "value": job.id})
        
        job_choices.append({"name": "Cancel", "value": "cancel"})
        
        # Select job to view
        job_id = questionary.select(
            "Select task to view:",
            choices=job_choices,
            style=custom_style
        ).ask()
        
        if job_id != "cancel":
            job = manager.get_job(job_id)
            if job:
                display_job_info(job)
    
    input("\nPress Enter to continue...")

def toggle_cron_job() -> None:
    """Enable or disable a cron job."""
    info("\n⚙️ Enable/Disable Task")
    
    manager = CronManager()
    jobs = manager.list_jobs()
    
    if not jobs:
        info("No scheduled tasks found.")
        input("\nPress Enter to continue...")
        return
    
    # Create job choices
    job_choices = []
    for job in jobs:
        status = "✅" if job.enabled else "❌"
        desc = job.description or f"{job.job_type} - {job.target_id}"
        job_choices.append({"name": f"{status} {desc}", "value": job.id})
    
    job_choices.append({"name": "Cancel", "value": "cancel"})
    
    # Select job to toggle
    job_id = questionary.select(
        "Select task to enable/disable:",
        choices=job_choices,
        style=custom_style
    ).ask()
    
    if job_id == "cancel":
        return
    
    # Get current job state
    job = manager.get_job(job_id)
    if not job:
        error(f"❌ Task with ID {job_id} not found.")
        input("\nPress Enter to continue...")
        return
    
    # Confirm action
    action = "disable" if job.enabled else "enable"
    if not questionary.confirm(
        f"Are you sure you want to {action} this task?",
        style=custom_style,
        default=True
    ).ask():
        return
    
    # Toggle job state
    if job.enabled:
        success_result = manager.disable_job(job_id)
        action_msg = "disabled"
    else:
        success_result = manager.enable_job(job_id)
        action_msg = "enabled"
    
    if success_result:
        success(f"✅ Task {action_msg} successfully.")
    else:
        error(f"❌ Failed to {action} task.")
    
    input("\nPress Enter to continue...")

def delete_cron_job() -> None:
    """Delete a cron job."""
    info("\n🗑️ Delete Task")
    
    manager = CronManager()
    jobs = manager.list_jobs()
    
    if not jobs:
        info("No scheduled tasks found.")
        input("\nPress Enter to continue...")
        return
    
    # Create job choices
    job_choices = []
    for job in jobs:
        status = "✅" if job.enabled else "❌"
        desc = job.description or f"{job.job_type} - {job.target_id}"
        job_choices.append({"name": f"{status} {desc}", "value": job.id})
    
    job_choices.append({"name": "Cancel", "value": "cancel"})
    
    # Select job to delete
    job_id = questionary.select(
        "Select task to delete:",
        choices=job_choices,
        style=custom_style
    ).ask()
    
    if job_id == "cancel":
        return
    
    # Get job details for confirmation
    job = manager.get_job(job_id)
    if not job:
        error(f"❌ Task with ID {job_id} not found.")
        input("\nPress Enter to continue...")
        return
    
    # Show job details
    display_job_info(job)
    
    # Double confirm deletion
    if not questionary.confirm(
        "⚠️ Are you sure you want to delete this task? This action cannot be undone.",
        style=custom_style,
        default=False
    ).ask():
        return
    
    # Delete the job
    success_result = manager.remove_job(job_id)
    
    if success_result:
        success(f"✅ Task deleted successfully.")
    else:
        error(f"❌ Failed to delete task.")
    
    input("\nPress Enter to continue...")

def run_cron_job() -> None:
    """Run a cron job immediately."""
    info("\n▶️ Run Task Now")
    
    manager = CronManager()
    jobs = manager.list_jobs()
    
    if not jobs:
        info("No scheduled tasks found.")
        input("\nPress Enter to continue...")
        return
    
    # Create job choices
    job_choices = []
    for job in jobs:
        status = "✅" if job.enabled else "❌"
        desc = job.description or f"{job.job_type} - {job.target_id}"
        last_run = job.last_run or "Never"
        job_choices.append({"name": f"{status} {desc} (Last run: {last_run})", "value": job.id})
    
    job_choices.append({"name": "Cancel", "value": "cancel"})
    
    # Select job to run
    job_id = questionary.select(
        "Select task to run:",
        choices=job_choices,
        style=custom_style
    ).ask()
    
    if job_id == "cancel":
        return
    
    # Get job details
    job = manager.get_job(job_id)
    if not job:
        error(f"❌ Task with ID {job_id} not found.")
        input("\nPress Enter to continue...")
        return
    
    # Show job details
    display_job_info(job)
    
    # Confirm run
    if not questionary.confirm(
        "Are you sure you want to run this task now?",
        style=custom_style,
        default=True
    ).ask():
        return
    
    info(f"▶️ Running task {job_id}...")
    
    try:
        # Import CLI module to run the job
        from src.features.cron.cli import run_job
        success_result = run_job(job_id)
        
        if success_result:
            success(f"✅ Task completed successfully.")
        else:
            error(f"❌ Task execution failed.")
    except Exception as e:
        error(f"❌ Error running task: {e}")
    
    input("\nPress Enter to continue...")

def add_cron_job() -> None:
    """Add a new cron job."""
    info("\n➕ Add New Scheduled Task")
    
    # Get available job types
    job_types = job_registry.get_available_job_types()
    
    if not job_types:
        error("❌ No job types registered. Cannot create a new task.")
        input("\nPress Enter to continue...")
        return
    
    # Select job type
    job_type_choices = [{"name": job_type, "value": job_type} for job_type in job_types]
    job_type_choices.append({"name": "Cancel", "value": "cancel"})
    
    job_type = questionary.select(
        "Select task type:",
        choices=job_type_choices,
        style=custom_style
    ).ask()
    
    if job_type == "cancel":
        return
    
    # Get target ID (e.g., website domain for backup tasks)
    if job_type == "backup":
        # For backup jobs, get the website domain
        from src.features.website.utils import select_website
        target_id = select_website("Select website to backup:")
        
        if not target_id:
            info("Operation cancelled.")
            return
    else:
        # For other job types, ask for a target ID
        target_id = questionary.text(
            "Enter target ID (e.g., website name):",
            style=custom_style
        ).ask()
    
    if not target_id:
        error("❌ Target ID is required.")
        input("\nPress Enter to continue...")
        return
    
    # Get schedule
    schedule_choices = [
        {"name": "Daily at midnight", "value": "0 0 * * *"},
        {"name": "Daily at 2:00 AM", "value": "0 2 * * *"},
        {"name": "Weekly on Sunday at midnight", "value": "0 0 * * 0"},
        {"name": "Monthly on the 1st at midnight", "value": "0 0 1 * *"},
        {"name": "Custom", "value": "custom"},
        {"name": "Cancel", "value": "cancel"}
    ]
    
    schedule = questionary.select(
        "Select schedule:",
        choices=schedule_choices,
        style=custom_style
    ).ask()
    
    if schedule == "cancel":
        return
    
    if schedule == "custom":
        # Provide help text for cron format
        info("\n📋 Cron Format Help:")
        info("  ┌─────────── minute (0 - 59)")
        info("  │ ┌───────── hour (0 - 23)")
        info("  │ │ ┌─────── day of month (1 - 31)")
        info("  │ │ │ ┌───── month (1 - 12)")
        info("  │ │ │ │ ┌─── day of week (0 - 6) (Sunday=0)")
        info("  │ │ │ │ │")
        info("  * * * * *")
        
        # Ask for custom schedule
        schedule = questionary.text(
            "Enter cron schedule expression:",
            style=custom_style
        ).ask()
        
        if not schedule:
            error("❌ Schedule is required.")
            input("\nPress Enter to continue...")
            return
    
    # Get job description
    description = questionary.text(
        "Enter task description:",
        style=custom_style
    ).ask() or f"{job_type} task for {target_id}"
    
    # Job parameters based on type
    parameters = {}
    
    if job_type == "backup":
        # For backup jobs, ask for provider and retention count
        from src.features.backup.backup_manager import BackupManager
        backup_manager = BackupManager()
        providers = backup_manager.get_available_providers()
        
        if providers:
            provider_choices = [{"name": p, "value": p} for p in providers]
            provider = questionary.select(
                "Select storage provider:",
                choices=provider_choices,
                style=custom_style
            ).ask()
            
            if provider:
                parameters["provider"] = provider
        
        retention_count = questionary.select(
            "Select how many backups to keep:",
            choices=[
                {"name": "1", "value": 1},
                {"name": "3", "value": 3},
                {"name": "5", "value": 5},
                {"name": "10", "value": 10}
            ],
            style=custom_style
        ).ask()
        
        if retention_count:
            parameters["retention_count"] = int(retention_count)
    
    # Create the job
    job = CronJob(
        job_type=job_type,
        schedule=schedule,
        target_id=target_id,
        parameters=parameters,
        description=description
    )
    
    # Display job summary
    info("\n📋 Task Summary:")
    info(f"  Type: {job.job_type}")
    info(f"  Target: {job.target_id}")
    info(f"  Schedule: {job.schedule}")
    info(f"  Description: {job.description}")
    
    if parameters:
        info("  Parameters:")
        for key, value in parameters.items():
            info(f"    {key}: {value}")
    
    # Confirm job creation
    if not questionary.confirm(
        "Create this scheduled task?",
        style=custom_style,
        default=True
    ).ask():
        return
    
    # Add the job
    manager = CronManager()
    success_result = manager.add_job(job)
    
    if success_result:
        success(f"✅ Task created successfully with ID: {job.id}")
    else:
        error(f"❌ Failed to create task.")
    
    input("\nPress Enter to continue...")

def prompt_cron_menu() -> None:
    """Display cron job management menu and handle user selection."""
    try:
        choices = [
            {"name": "1. List Tasks", "value": "1"},
            {"name": "2. Add New Task", "value": "2"},
            {"name": "3. Enable/Disable Task", "value": "3"},
            {"name": "4. Delete Task", "value": "4"},
            {"name": "5. Run Task Now", "value": "5"},
            {"name": "0. Back to System Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n⏱️ Scheduled Task Management:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "0":
            return
        elif answer == "1":
            list_cron_jobs()
        elif answer == "2":
            add_cron_job()
        elif answer == "3":
            toggle_cron_job()
        elif answer == "4":
            delete_cron_job()
        elif answer == "5":
            run_cron_job()
    except Exception as e:
        error(f"Error in cron menu: {e}")
        input("Press Enter to continue...")