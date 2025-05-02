from dataclasses import dataclass
from typing import Optional


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
class SiteConfig:
    domain: str
    php_version: str
    logs: SiteLogs 
    cache: Optional[str] = None
    mysql: Optional[SiteMySQL] = None
    container_php: Optional[str] = None