"""
Package for cron module data models.
"""
from core.backend.modules.cron.models.cron_job import CronJob
from core.backend.modules.cron.models.job_result import JobResult

__all__ = ["CronJob", "JobResult"]