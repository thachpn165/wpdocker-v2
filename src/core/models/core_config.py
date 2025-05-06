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
        lang: Interface language
    """
    channel: str
    timezone: str
    webserver: str
    lang: str