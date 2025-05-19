"""
WP Docker application.

This package is the main entry point for the WP Docker application,
providing functionality for managing WordPress websites with Docker.

The package is organized into the following modules:
- features: Domain-specific modules (website, backup, MySQL, etc.)
- common: Shared utilities and helper functions
- interfaces: Abstract base classes and interfaces
- core: Core system functionality
"""

from .version import __version__