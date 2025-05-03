from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class CoreConfig:
    channel: str
    timezone: str
    webserver: str
    mysql_version: str
    lang: str


@dataclass
class SiteLogs:
    access: Optional[str] = None
    error: Optional[str] = None
    php_error: Optional[str] = None
    php_slow: Optional[str] = None


@dataclass
class SiteMySQL:
    db_name: str
    db_user: str
    db_pass: str


@dataclass
class SitePHP:
    php_version: str
    php_container: Optional[str] = None
    php_installed_extensions: Optional[List[str]] = None


@dataclass
class SiteBackupInfo:
    time: str
    file: str
    database: str


@dataclass
class BackupSchedule:
    """Cấu hình lịch trình backup tự động."""
    enabled: bool = False
    schedule_type: str = "daily"  # daily, weekly, monthly
    hour: int = 0                 # Giờ trong ngày (0-23)
    minute: int = 0               # Phút (0-59)
    day_of_week: Optional[int] = None  # 0-6, Thứ Hai là 0 (cho backup hàng tuần)
    day_of_month: Optional[int] = None  # 1-31 (cho backup hàng tháng)
    retention_count: int = 3      # Số lượng bản backup giữ lại
    cloud_sync: bool = False      # Có đồng bộ lên cloud storage không


@dataclass
class CloudConfig:
    """Cấu hình cloud storage."""
    provider: str = "rclone"      # Hiện tại chỉ hỗ trợ rclone
    remote_name: str = ""         # Tên remote rclone
    remote_path: str = ""         # Đường dẫn trong remote
    enabled: bool = False         # Cloud sync có bật không


@dataclass
class SiteBackup:
    last_backup: Optional[SiteBackupInfo] = None
    schedule: Optional[BackupSchedule] = None
    cloud_config: Optional[CloudConfig] = None
    job_id: Optional[str] = None  # ID của công việc cron


@dataclass
class SiteConfig:
    domain: str
    logs: SiteLogs
    cache: Optional[str] = None
    mysql: Optional[SiteMySQL] = None
    php: Optional[SitePHP] = None
    backup: Optional[SiteBackup] = None