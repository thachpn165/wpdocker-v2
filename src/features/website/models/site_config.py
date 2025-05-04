"""
Website configuration models.

This module defines the data models for website configuration,
including site details, database settings, PHP settings, and backup information.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class SiteLogs:
    """Website log file paths."""
    
    access: Optional[str] = None
    error: Optional[str] = None
    php_error: Optional[str] = None
    php_slow: Optional[str] = None


@dataclass
class SiteMySQL:
    """MySQL database configuration for a website."""
    
    db_name: str
    db_user: str
    db_pass: str


@dataclass
class SitePHP:
    """PHP configuration for a website."""
    
    php_version: str
    php_container: Optional[str] = None
    php_installed_extensions: Optional[List[str]] = None


@dataclass
class SiteBackupInfo:
    """Information about a specific backup."""
    
    time: str
    file: str
    database: str


@dataclass
class BackupSchedule:
    """Automatic backup schedule configuration."""
    
    enabled: bool = False
    schedule_type: str = "daily"  # daily, weekly, monthly
    hour: int = 0                 # Hour of the day (0-23)
    minute: int = 0               # Minute (0-59)
    day_of_week: Optional[int] = None  # 0-6, Monday is 0 (for weekly backups)
    day_of_month: Optional[int] = None  # 1-31 (for monthly backups)
    retention_count: int = 3      # Number of backups to keep
    cloud_sync: bool = False      # Whether to sync to cloud storage


@dataclass
class CloudConfig:
    """Cloud storage configuration."""
    
    provider: str = "rclone"      # Currently only supports rclone
    remote_name: str = ""         # Rclone remote name
    remote_path: str = ""         # Path within the remote
    enabled: bool = False         # Whether cloud sync is enabled


@dataclass
class SiteBackup:
    """Website backup configuration."""
    
    last_backup: Optional[SiteBackupInfo] = None
    schedule: Optional[BackupSchedule] = None
    cloud_config: Optional[CloudConfig] = None
    job_id: Optional[str] = None  # ID of the cron job


@dataclass
class SiteConfig:
    """Main website configuration."""
    
    domain: str
    logs: SiteLogs
    cache: Optional[str] = None
    mysql: Optional[SiteMySQL] = None
    php: Optional[SitePHP] = None
    backup: Optional[SiteBackup] = None