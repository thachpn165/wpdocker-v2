from dataclasses import dataclass
from typing import Optional, List


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
class SiteBackup:
    last_backup: Optional[SiteBackupInfo] = None

@dataclass
class SiteConfig:
    domain: str
    logs: SiteLogs
    cache: Optional[str] = None
    mysql: Optional[SiteMySQL] = None
    php: Optional[SitePHP] = None
    backup: Optional[SiteBackup] = None
