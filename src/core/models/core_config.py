"""
Core system configuration model.

This module defines the dataclass for core system configuration settings.
"""

from dataclasses import dataclass


@dataclass
class CoreConfig:
    """
    Core system configuration settings.
    
    Attributes:
        channel: Release channel (stable, beta, etc.)
        timezone: System timezone setting
        webserver: Web server type (nginx, etc.)
        mysql_version: MySQL/MariaDB version
        lang: Interface language
    """
    channel: str
    timezone: str
    webserver: str
    mysql_version: str
    lang: str