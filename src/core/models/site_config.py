"""
Website configuration models.

This module defines dataclasses for website-specific configuration.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class SiteLogs:
    """
    Website log file paths.
    
    Attributes:
        access: Path to access log file
        error: Path to error log file
        php_error: Path to PHP error log
        php_slow: Path to PHP slow script log
    """
    access: Optional[str] = None
    error: Optional[str] = None
    php_error: Optional[str] = None
    php_slow: Optional[str] = None


@dataclass
class SiteMySQL:
    """
    MySQL database configuration for a website.
    
    Attributes:
        db_name: Database name
        db_user: Database username
        db_pass: Database password
    """
    db_name: str
    db_user: str
    db_pass: str


@dataclass
class SitePHP:
    """
    PHP configuration for a website.
    
    Attributes:
        php_version: PHP version
        php_container: PHP container name
        php_installed_extensions: List of installed PHP extensions
    """
    php_version: str
    php_container: Optional[str] = None
    php_installed_extensions: Optional[List[str]] = None


@dataclass
class SiteBackupInfo:
    """
    Backup information for a website.
    
    Attributes:
        time: Timestamp of the backup
        file: Path to website files backup
        database: Path to database backup
    """
    time: str
    file: str
    database: str


@dataclass
class BackupSchedule:
    """
    Automatic backup schedule configuration.
    
    Attributes:
        enabled: Whether automatic backup is enabled
        schedule_type: Schedule type (daily, weekly, monthly)
        hour: Hour of day (0-23)
        minute: Minute (0-59)
        day_of_week: Day of week (0-6, Monday=0) for weekly backups
        day_of_month: Day of month (1-31) for monthly backups
        retention_count: Number of backups to keep
        cloud_sync: Whether to sync to cloud storage
    """
    enabled: bool = False
    schedule_type: str = "daily"
    hour: int = 0
    minute: int = 0
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    retention_count: int = 3
    cloud_sync: bool = False


@dataclass
class CloudConfig:
    """
    Cloud storage configuration.
    
    Attributes:
        provider: Cloud storage provider (currently only rclone)
        remote_name: Rclone remote name
        remote_path: Path in remote storage
        enabled: Whether cloud sync is enabled
    """
    provider: str = "rclone"
    remote_name: str = ""
    remote_path: str = ""
    enabled: bool = False


@dataclass
class SiteBackup:
    """
    Complete backup configuration for a website.
    
    Attributes:
        last_backup: Information about the last backup
        schedule: Backup schedule configuration
        cloud_config: Cloud storage configuration
        job_id: Cron job ID for scheduled backups
    """
    last_backup: Optional[SiteBackupInfo] = None
    schedule: Optional[BackupSchedule] = None
    cloud_config: Optional[CloudConfig] = None
    job_id: Optional[str] = None


@dataclass
class SiteConfig:
    """
    Complete website configuration.
    
    Attributes:
        domain: Website domain name
        logs: Log file paths
        cache: Cache configuration
        mysql: MySQL database configuration
        php: PHP configuration
        backup: Backup configuration
    """
    domain: str
    logs: SiteLogs
    cache: Optional[str] = None
    mysql: Optional[SiteMySQL] = None
    php: Optional[SitePHP] = None
    backup: Optional[SiteBackup] = None