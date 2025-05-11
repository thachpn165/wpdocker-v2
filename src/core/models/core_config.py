"""
Core system configuration model.

This module defines the dataclass for core system configuration settings.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ContainerConfig:
    """
    Container configuration settings.

    Attributes:
        name: Container name
        id: Container ID
    """
    name: str
    id: str
    compose_file: str


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
    containers: Optional[List[ContainerConfig]] = None
