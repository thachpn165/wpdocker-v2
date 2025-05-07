#!/usr/bin/env python3
"""
CLI for managing and running cron jobs.

This module provides a command-line interface for the cron management system,
allowing jobs to be listed, run, and managed.
"""

import os
import sys
import argparse
from datetime import datetime
import json
import tempfile

from src.common.logging import info, error, debug, warn
from src.features.cron.cron_manager import CronManager
from src.features.cron.models.job_result import JobResult


def list_jobs():
    """List all registered cron jobs."""
    manager = CronManager()
    jobs = manager.list_jobs()
    
    if not jobs:
        print("No cron jobs found.")
        return
    
    print(f"Found {len(jobs)} registered cron jobs:")
    print("-" * 80)
    
    for job in jobs:
        status = "✅ Enabled" if job.enabled else "❌ Disabled"
        print(f"ID: {job.id}")
        print(f"Type: {job.job_type}")
        print(f"Target: {job.target_id}")
        print(f"Schedule: {job.schedule}")
        print(f"Status: {status}")
        
        if job.last_run:
            print(f"Last Run: {job.last_run}")
            print(f"Last Status: {job.last_status or 'Unknown'}")
            
        # Description is no longer explicitly shown
            
        print("-" * 80)


def run_job(job_id=None):
    """Run a specific job or all pending jobs."""
    manager = CronManager()
    
    if job_id:
        # Run a specific job
        info(f"Running job {job_id}...")
        job = manager.get_job(job_id)
        
        if not job:
            error(f"Job {job_id} not found.")
            return False
            
        if not job.enabled:
            warn(f"Job {job_id} is disabled. Running anyway.")
        
        # Create a job result record
        job_result = JobResult(
            job_id=job_id,
            status="running",
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Choose the appropriate runner for this job type
        from src.features.cron import job_registry
        runner_class = job_registry.get_runner_for_job_type(job.job_type)
        
        if not runner_class:
            error(f"No runner found for job type: {job.job_type}")
            job_result.complete("failure", f"No runner found for job type: {job.job_type}")
            _save_job_result(job_result)
            return False
            
        # Create a runner instance
        runner = runner_class(job, job_result)
        
        try:
            # Run the job
            success = runner.run()
            
            # Update status
            status = "success" if success else "failure"
            job_result.complete(status)
            
            # Update job status in cron manager
            manager.update_job_status(job_id, status)
            
            # Save job result
            _save_job_result(job_result)
            
            return success
        except Exception as e:
            error(f"Error running job {job_id}: {e}")
            job_result.complete("failure", str(e))
            _save_job_result(job_result)
            return False
    else:
        # TODO: Run all pending jobs
        error("Running all pending jobs is not yet implemented.")
        return False


def _save_job_result(job_result):
    """Save job result to file."""
    try:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.environ.get("WP_DOCKER_HOME", "."), "logs", "cron", "results")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(logs_dir, f"{job_result.job_id}_{timestamp}.json")
        
        # Write job result to file
        with open(file_path, "w") as f:
            json.dump(job_result.to_dict(), f, indent=2)
            
        debug(f"Job result saved to {file_path}")
    except Exception as e:
        error(f"Error saving job result: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Cron job management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all cron jobs")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run a cron job")
    run_parser.add_argument("--job-id", help="ID of the job to run")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_jobs()
    elif args.command == "run":
        success = run_job(args.job_id)
        if not success:
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()