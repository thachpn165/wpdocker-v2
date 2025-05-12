"""
Version checking functionality.

This module provides utilities for checking version information
and comparing versions.
"""

import re
from typing import Dict, Any, Optional, Tuple

from src.common.logging import Debug, log_call


class VersionChecker:
    """
    Utilities for checking and comparing versions.
    
    This class provides functionality for checking version information
    and comparing versions using semantic versioning.
    """
    
    def __init__(self):
        """Initialize the version checker."""
        self.debug = Debug("VersionChecker")
        
    @log_call
    def get_current_version(self) -> Tuple[str, str, str]:
        """
        Get the current version information.
        
        Returns:
            Tuple of (version, channel, build_date)
        """
        from src.version import VERSION, CHANNEL, BUILD_DATE
        return VERSION, CHANNEL, BUILD_DATE
        
    @log_call
    def format_version_info(self) -> Dict[str, Any]:
        """
        Format the current version information for display.
        
        Returns:
            Dict with formatted version information
        """
        version, channel, build_date = self.get_current_version()
        
        return {
            "version": version,
            "channel": channel,
            "build_date": build_date,
            "formatted": f"{version} ({channel}, built on {build_date})"
        }
        
    @log_call
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings using semantic versioning.
        
        Args:
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        try:
            import semver
            return semver.compare(version1, version2)
        except Exception as e:
            self.debug.error(f"Error comparing versions: {str(e)}")
            
            # Fallback to simple version comparison
            # This may not be accurate for all cases
            v1_parts = self._parse_version(version1)
            v2_parts = self._parse_version(version2)
            
            # Compare major, minor, patch in order
            for i in range(min(len(v1_parts), len(v2_parts))):
                if v1_parts[i] < v2_parts[i]:
                    return -1
                elif v1_parts[i] > v2_parts[i]:
                    return 1
                    
            # If we get here, the common parts are equal
            # The version with more parts is considered greater
            if len(v1_parts) < len(v2_parts):
                return -1
            elif len(v1_parts) > len(v2_parts):
                return 1
                
            return 0
            
    def _parse_version(self, version: str) -> list:
        """
        Parse a version string into parts.
        
        Args:
            version: Version string to parse
            
        Returns:
            List of version parts as integers
        """
        # Remove leading 'v' if present
        if version.startswith('v'):
            version = version[1:]
            
        # Split on dots and convert to integers where possible
        parts = []
        for part in version.split('.'):
            try:
                parts.append(int(part))
            except ValueError:
                # If not a number, try to extract numbers from it
                matches = re.findall(r'\d+', part)
                if matches:
                    parts.append(int(matches[0]))
                else:
                    # If no numbers, just append the string
                    parts.append(part)
                    
        return parts


# Singleton instance
version_checker = VersionChecker()


@log_call
def get_current_version() -> Tuple[str, str, str]:
    """
    Get the current version information.
    
    Returns:
        Tuple of (version, channel, build_date)
    """
    return version_checker.get_current_version()


@log_call
def format_version_info() -> Dict[str, Any]:
    """
    Format the current version information for display.
    
    Returns:
        Dict with formatted version information
    """
    return version_checker.format_version_info()


@log_call
def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings.
    
    Args:
        version1: First version to compare
        version2: Second version to compare
        
    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2
    """
    return version_checker.compare_versions(version1, version2)