#!/usr/bin/env python3
"""
CLI for managing and executing cron jobs.
"""
import sys
import os
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.modules.cron.job_registry import JobRegistry
from core.backend.modules.cron.cron_manager import CronManager
from core.backend.modules.cron.models.cron_job import CronJob
from core.backend.modules.cron.models.job_result import JobResult


def setup_parser():
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="WP Docker Cron CLI - Automated scheduling management tool",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Run command: Execute jobs
    run_parser = subparsers.add_parser("run", help="Execute cron jobs")
    run_parser.add_argument("--job-id", help="ID of specific job")
    run_parser.add_argument("--job-type", help="Job type (backup, etc)")
    
    # List command: List all jobs
    list_parser = subparsers.add_parser("list", help="List registered jobs")
    list_parser.add_argument("--job-type", help="Filter by job type")
    list_parser.add_argument("--enabled", action="store_true", help="Show only enabled jobs")
    list_parser.add_argument("--disabled", action="store_true", help="Show only disabled jobs")
    
    # Enable command: Enable a job
    enable_parser = subparsers.add_parser("enable", help="Enable a job")
    enable_parser.add_argument("job_id", help="ID of job to enable")
    
    # Disable command: Disable a job
    disable_parser = subparsers.add_parser("disable", help="Disable a job")
    disable_parser.add_argument("job_id", help="ID of job to disable")
    
    # Remove command: Remove a job
    remove_parser = subparsers.add_parser("remove", help="Remove a job")
    remove_parser.add_argument("job_id", help="ID of job to remove")
    
    # Status command: Show job status
    status_parser = subparsers.add_parser("status", help="Show job status")
    status_parser.add_argument("job_id", help="ID of job to display")
    
    return parser


@log_call
def run_jobs(args):
    """
    Execute cron jobs.
    
    Args:
        args: Command line arguments
    """
    manager = CronManager()
    registry = JobRegistry()
    
    if args.job_id:
        # Run a specific job
        job = manager.get_job(args.job_id)
        if not job:
            error(f"❌ Job with ID {args.job_id} not found")
            return
        
        info(f"🔄 Executing job {job.id} (Type: {job.job_type})")
        result = registry.execute_job(job)
        
        if result.status == "success":
            success(f"✅ Successfully executed job {job.id}")
        else:
            error(f"❌ Failed to execute job {job.id}: {result.error}")
            
    elif args.job_type:
        # Run all jobs of the same type
        jobs = manager.list_jobs()
        filtered_jobs = [job for job in jobs if job.job_type == args.job_type and job.enabled]
        
        if not filtered_jobs:
            warn(f"⚠️ No enabled jobs found of type {args.job_type}")
            return
            
        info(f"🔄 Executing {len(filtered_jobs)} jobs of type {args.job_type}")
        
        for job in filtered_jobs:
            info(f"➡️ Executing job {job.id}")
            result = registry.execute_job(job)
            
            if result.status == "success":
                success(f"✅ Successfully executed job {job.id}")
            else:
                error(f"❌ Failed to execute job {job.id}: {result.error}")
    else:
        # Run all enabled jobs
        jobs = manager.list_jobs()
        enabled_jobs = [job for job in jobs if job.enabled]
        
        if not enabled_jobs:
            warn("⚠️ No enabled jobs found")
            return
            
        info(f"🔄 Executing {len(enabled_jobs)} enabled jobs")
        
        for job in enabled_jobs:
            info(f"➡️ Executing job {job.id} (Type: {job.job_type})")
            result = registry.execute_job(job)
            
            if result.status == "success":
                success(f"✅ Successfully executed job {job.id}")
            else:
                error(f"❌ Failed to execute job {job.id}: {result.error}")


@log_call
def list_jobs(args):
    """
    List registered jobs.
    
    Args:
        args: Command line arguments
    """
    manager = CronManager()
    jobs = manager.list_jobs()
    
    # Filter by parameters
    if args.job_type:
        jobs = [job for job in jobs if job.job_type == args.job_type]
    
    if args.enabled:
        jobs = [job for job in jobs if job.enabled]
    
    if args.disabled:
        jobs = [job for job in jobs if not job.enabled]
    
    if not jobs:
        info("No jobs found.")
        return
    
    # Display job list
    print("\nCron job list:")
    print("-" * 80)
    print(f"{'ID':<15} {'Type':<10} {'Schedule':<15} {'Status':<10} {'Target':<20} {'Last Run':<20}")
    print("-" * 80)
    
    for job in jobs:
        status = "✅ Enabled" if job.enabled else "❌ Disabled"
        print(f"{job.id:<15} {job.job_type:<10} {job.schedule:<15} {status:<10} {job.target_id:<20} {job.last_run or 'Never':<20}")
    
    print("-" * 80)
    print(f"Total: {len(jobs)} jobs")


@log_call
def enable_job(args):
    """
    Enable a job.
    
    Args:
        args: Command line arguments
    """
    manager = CronManager()
    
    if manager.enable_job(args.job_id):
        success(f"✅ Successfully enabled job {args.job_id}")
    else:
        error(f"❌ Could not enable job {args.job_id}")


@log_call
def disable_job(args):
    """
    Disable a job.
    
    Args:
        args: Command line arguments
    """
    manager = CronManager()
    
    if manager.disable_job(args.job_id):
        success(f"✅ Successfully disabled job {args.job_id}")
    else:
        error(f"❌ Could not disable job {args.job_id}")


@log_call
def remove_job(args):
    """
    Remove a job.
    
    Args:
        args: Command line arguments
    """
    manager = CronManager()
    
    if manager.remove_job(args.job_id):
        success(f"✅ Successfully removed job {args.job_id}")
    else:
        error(f"❌ Could not remove job {args.job_id}")


@log_call
def show_job_status(args):
    """
    Show job status.
    
    Args:
        args: Command line arguments
    """
    manager = CronManager()
    job = manager.get_job(args.job_id)
    
    if not job:
        error(f"❌ Job with ID {args.job_id} not found")
        return
    
    print("\nCron job information:")
    print("-" * 80)
    print(f"ID:               {job.id}")
    print(f"Type:             {job.job_type}")
    print(f"Schedule:         {job.schedule}")
    print(f"Status:           {'✅ Enabled' if job.enabled else '❌ Disabled'}")
    print(f"Target:           {job.target_id}")
    print(f"Created:          {job.created_at or 'Unknown'}")
    print(f"Last run:         {job.last_run or 'Never'}")
    print(f"Last status:      {job.last_status or 'None'}")
    print(f"Description:      {job.description or 'None'}")
    print(f"Parameters:       {job.parameters}")
    print("-" * 80)


def main():
    """Main program function."""
    parser = setup_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute the corresponding command
    if args.command == "run":
        run_jobs(args)
    elif args.command == "list":
        list_jobs(args)
    elif args.command == "enable":
        enable_job(args)
    elif args.command == "disable":
        disable_job(args)
    elif args.command == "remove":
        remove_job(args)
    elif args.command == "status":
        show_job_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation canceled.")
        sys.exit(1)
    except Exception as e:
        error(f"❌ Unhandled error: {e}")
        sys.exit(1)