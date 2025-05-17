"""
Support for managing version information.

This module provides utility functions to access and manage the application's
version information, replacing the use of version.py.
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from src.common.logging import debug, error, info, log_call
from src.common.config.manager import ConfigManager


# Default values for version information
DEFAULT_VERSION = "0.1.4"
DEFAULT_CHANNEL = "stable"
DEFAULT_BUILD_DATE = "2023-06-01" 
DEFAULT_DISPLAY_NAME = f"{DEFAULT_VERSION} ({DEFAULT_CHANNEL.capitalize()})"


@log_call
def initialize_version_info() -> None:
    """
    Initialize version information in config if it does not exist.
    
    This function ensures that version information always exists in the config,
    even if the config is newly created or reset.
    """
    config = ConfigManager()
    
    # Check if version information already exists in config
    current_version = config.get("core.version")
    
    # If not, initialize with default values
    if not current_version:
        debug("Initializing version information in config...")
        config.set("core.version", DEFAULT_VERSION)
        config.set("core.channel", DEFAULT_CHANNEL)
        config.set("core.build_date", DEFAULT_BUILD_DATE)
        config.set("core.display_name", DEFAULT_DISPLAY_NAME)
        config.save()
        debug("Version information initialized in config")


@log_call
def get_version() -> str:
    """
    Get the current version number.
    
    Returns:
        str: Version number (e.g., "0.1.4")
    """
    config = ConfigManager()
    return config.get("core.version", DEFAULT_VERSION)


@log_call
def get_channel() -> str:
    """
    Get the current release channel.
    
    Returns:
        str: Release channel ("stable", "nightly", "dev")
    """
    config = ConfigManager()
    return config.get("core.channel", DEFAULT_CHANNEL)


@log_call
def get_build_date() -> str:
    """
    Get the build date of the current version.
    
    Returns:
        str: Build date (e.g., "2023-06-01")
    """
    config = ConfigManager()
    return config.get("core.build_date", DEFAULT_BUILD_DATE)


@log_call
def get_display_name() -> str:
    """
    Get the display name of the current version.
    
    Returns:
        str: Display name (e.g., "0.1.4 Stable" or "Nightly Build 20230802")
    """
    config = ConfigManager()
    version = get_version()
    channel = get_channel()
    
    # Prefer using the saved display name if available
    display_name = config.get("core.display_name")
    if display_name:
        return display_name
    
    # If not available, create a default display name based on version and channel
    return f"{version} ({channel.capitalize()})"


@log_call
def get_version_metadata() -> Dict[str, Any]:
    """
    Get metadata of the current version.
    
    Returns:
        Dict[str, Any]: Version metadata or empty dict if not available
    """
    config = ConfigManager()
    metadata = config.get("core.metadata", {})
    return metadata


@log_call
def get_version_info() -> Dict[str, str]:
    """
    Get all version information.
    
    Returns:
        Dict[str, str]: Full version information
    """
    info = {
        "version": get_version(),
        "channel": get_channel(),
        "build_date": get_build_date(),
        "display_name": get_display_name()
    }
    
    # Add metadata if available
    metadata = get_version_metadata()
    if metadata:
        info["metadata"] = metadata
        
        # Add additional information if present in metadata
        if "code_name" in metadata:
            info["code_name"] = metadata["code_name"]
        if "build_number" in metadata:
            info["build_number"] = metadata["build_number"]
    
    return info


@log_call
def update_version_info(version: str, channel: str = None, build_date: str = None, 
                       display_name: str = None, metadata: Dict[str, Any] = None) -> None:
    """
    Update version information in config.
    
    Args:
        version: New version number
        channel: New release channel (if not provided, keep current value)
        build_date: New build date (if not provided, use current date)
        display_name: New display name (if not provided, auto-generate)
        metadata: Additional metadata information
    """
    config = ConfigManager()
    
    # Update version (required)
    config.set("core.version", version)
    
    # Update channel if provided
    if channel:
        config.set("core.channel", channel)
    else:
        channel = config.get("core.channel", DEFAULT_CHANNEL)
    
    # Update build_date if provided, otherwise use current date
    if build_date:
        config.set("core.build_date", build_date)
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        config.set("core.build_date", today)
    
    # Update metadata if provided
    if metadata:
        config.set("core.metadata", metadata)
        debug(f"Version metadata updated: {metadata}")
    
    # Update display_name if provided
    if display_name:
        config.set("core.display_name", display_name)
    else:
        # Auto-generate display_name if not provided
        # Prefer using code_name from metadata if available
        auto_display_name = version
        
        if metadata and "code_name" in metadata:
            auto_display_name = f"{version} \"{metadata['code_name']}\""
        else:
            auto_display_name = f"{version} ({channel.capitalize()})"
            
        # Add build number if available
        if metadata and "build_number" in metadata:
            auto_display_name += f" (Build {metadata['build_number']})"
            
        config.set("core.display_name", auto_display_name)
    
    # Save changes
    config.save()
    debug(f"Version information updated: {version} ({channel})")


@log_call
def parse_version_metadata_from_release(release_body: str) -> Dict[str, Any]:
    """
    Parse version metadata from the release body.
    
    Look for metadata in the format:
    <!-- VERSION_INFO
    {
        "display_name": "Nightly Build 20230802",
        "code_name": "Thunder",
        "other_info": "value"
    }
    -->
    
    Or a simpler format:
    <!-- VERSION_INFO display_name: "Nightly Build 20230802" code_name: "Thunder" -->
    
    Args:
        release_body: Release description content
        
    Returns:
        Dict[str, Any]: Version metadata or empty dict if not found
    """
    if not release_body:
        return {}
    
    # Search for metadata in <!-- VERSION_INFO ... --> format
    pattern = r'<!--\s*VERSION_INFO\s*([\s\S]*?)\s*-->'
    match = re.search(pattern, release_body)
    
    if not match:
        debug("VERSION_INFO metadata not found in release body")
        return {}
    
    # Get content from the matched section
    content = match.group(1).strip()
    
    # Try parsing as JSON first
    try:
        # Check if content starts with { and ends with }, possibly JSON
        if content.startswith('{') and content.endswith('}'):
            metadata = json.loads(content)
            info(f"Parsed version metadata from JSON: {metadata}")
            return metadata
    except json.JSONDecodeError:
        # If not valid JSON, try another method
        debug("Content is not valid JSON, trying another method")
    
    # Try parsing simple key: "value" key2: "value2" format
    try:
        # Use regex to find key: "value" pairs
        simple_pattern = r'(\w+):\s*"([^"]*)"'
        simple_matches = re.findall(simple_pattern, content)
        
        if simple_matches:
            metadata = {key: value for key, value in simple_matches}
            info(f"Parsed version metadata from simple format: {metadata}")
            return metadata
    except Exception as e:
        error(f"Error parsing simple format version metadata: {str(e)}")
    
    # Try extracting important information
    try:
        metadata = {}
        
        # Find display_name if available
        display_match = re.search(r'display_name[=:]\s*"([^"]*)"', content, re.IGNORECASE)
        if display_match:
            metadata["display_name"] = display_match.group(1)
        
        # Find code_name if available
        code_name_match = re.search(r'code_name[=:]\s*"([^"]*)"', content, re.IGNORECASE)
        if code_name_match:
            metadata["code_name"] = code_name_match.group(1)
        
        # Find build_number if available
        build_match = re.search(r'build_number[=:]\s*"?(\d+)"?', content, re.IGNORECASE)
        if build_match:
            metadata["build_number"] = build_match.group(1)
        
        if metadata:
            info(f"Extracted some metadata from content analysis: {metadata}")
            return metadata
    except Exception as e:
        error(f"Error extracting metadata from content: {str(e)}")
    
    # If all methods fail, return empty dict
    debug("Unable to parse metadata from content, returning empty dict")
    return {}


@log_call
def extract_metadata_from_tag_name(tag_name: str) -> Dict[str, Any]:
    """
    Extract metadata from tag name, especially useful for nightly builds.
    
    Supports formats:
    - nightly-YYYYMMDD
    - vX.Y.Z-nightly.YYYYMMDD
    - vX.Y.Z-alpha.N
    - vX.Y.Z-beta.N
    - vX.Y.Z-rc.N
    
    Args:
        tag_name: Tag name to extract metadata from
        
    Returns:
        Dict[str, Any]: Extracted metadata
    """
    metadata = {}
    
    if not tag_name:
        return metadata
    
    # Remove 'v' prefix if present
    if tag_name.startswith('v'):
        version = tag_name[1:]
    else:
        version = tag_name
    
    # Extract date from nightly tag
    nightly_date_pattern = r'(nightly[.-])?(\d{8})'
    nightly_match = re.search(nightly_date_pattern, tag_name)
    if nightly_match:
        date_str = nightly_match.group(2)
        try:
            # Reformat date to YYYY-MM-DD
            date_formatted = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            metadata["build_date"] = date_formatted
            
            # Create display name for nightly build
            formatted_date = f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"
            metadata["display_name"] = f"Nightly Build {formatted_date}"
            debug(f"Extracted date from nightly tag: {formatted_date}")
        except Exception as e:
            error(f"Error formatting date from tag: {str(e)}")
    
    # Extract prerelease information
    prerelease_pattern = r'-(alpha|beta|rc)\.?(\d+)'
    prerelease_match = re.search(prerelease_pattern, tag_name)
    if prerelease_match:
        prerelease_type = prerelease_match.group(1)
        prerelease_number = prerelease_match.group(2)
        
        metadata["prerelease_type"] = prerelease_type
        metadata["prerelease_number"] = prerelease_number
        
        # Create display name for prerelease version
        base_version = version.split('-')[0]
        prerelease_display = f"{prerelease_type.capitalize()} {prerelease_number}"
        metadata["display_name"] = f"{base_version} {prerelease_display}"
        debug(f"Extracted prerelease information: {prerelease_type} {prerelease_number}")
    
    # Extract build information (if any)
    build_pattern = r'\+build\.(\d+)'
    build_match = re.search(build_pattern, tag_name)
    if build_match:
        build_number = build_match.group(1)
        metadata["build_number"] = build_number
        debug(f"Extracted build number: {build_number}")
    
    return metadata


@log_call
def extract_metadata_from_release(release_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract full metadata from GitHub release data.
    
    This function combines both intentionally embedded metadata and
    information that can be inferred from tag name, release name, and description.
    
    Args:
        release_data: Release data from GitHub API
        
    Returns:
        Dict[str, Any]: Extracted full metadata
    """
    metadata = {}
    
    if not release_data:
        return metadata
    
    # Get basic information from release
    tag_name = release_data.get("tag_name", "")
    release_name = release_data.get("name", "")
    is_prerelease = release_data.get("prerelease", False)
    published_at = release_data.get("published_at", "")
    release_body = release_data.get("body", "")
    
    # 1. First, parse intentionally embedded metadata from release body
    embedded_metadata = parse_version_metadata_from_release(release_body)
    if embedded_metadata:
        metadata.update(embedded_metadata)
        info(f"Found embedded metadata in release description: {embedded_metadata}")
    
    # 2. Extract metadata from tag name
    tag_metadata = extract_metadata_from_tag_name(tag_name)
    if tag_metadata:
        # Only update fields not already present in embedded metadata
        for key, value in tag_metadata.items():
            if key not in metadata:
                metadata[key] = value
        debug(f"Added metadata from tag name: {tag_metadata}")
    
    # 3. Use release name and release information
    # If display_name is not present, use release name if available
    if "display_name" not in metadata and release_name and release_name != tag_name:
        # Remove unnecessary prefixes if present
        display_name = release_name
        for prefix in ["WP Docker v2 ", "WP Docker ", "wpdocker-v2-", "wpdocker-"]:
            if display_name.startswith(prefix):
                display_name = display_name[len(prefix):]
                break
        metadata["display_name"] = display_name
        debug(f"Using release name as display_name: {display_name}")
    
    # 4. Determine release channel
    if "channel" not in metadata:
        if is_prerelease or "nightly" in tag_name.lower() or "alpha" in tag_name.lower() or "beta" in tag_name.lower() or "rc" in tag_name.lower():
            metadata["channel"] = "nightly"
        else:
            metadata["channel"] = "stable"
        debug(f"Determined release channel: {metadata['channel']}")
    
    # 5. Determine build date
    if "build_date" not in metadata and published_at:
        try:
            # Reformat date from ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
            from datetime import datetime
            pub_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
            metadata["build_date"] = pub_date.strftime("%Y-%m-%d")
            debug(f"Using published date as build_date: {metadata['build_date']}")
        except Exception as e:
            error(f"Error formatting published date: {str(e)}")
    
    # 6. Extract version from tag_name if not already present
    if "version" not in metadata and tag_name:
        version = tag_name.lstrip("v")
        # Remove prerelease and build metadata according to semver
        semver_pattern = r'^(\d+\.\d+\.\d+)(?:-|$)'
        semver_match = re.match(semver_pattern, version)
        if semver_match:
            version = semver_match.group(1)
            metadata["version"] = version
            debug(f"Extracted version from tag_name: {version}")
    
    # 7. Create a nicer display_name if not already present
    if "display_name" not in metadata:
        # Create display_name from other components
        if "version" in metadata:
            base_version = metadata["version"]
            
            # If it's a nightly version, create a richer display name
            if metadata.get("channel") == "nightly":
                if "build_date" in metadata:
                    # Reformat date for friendlier display
                    try:
                        date_parts = metadata["build_date"].split("-")
                        if len(date_parts) == 3:
                            formatted_date = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
                            display_name = f"Nightly Build {formatted_date}"
                            
                            # Add code_name if available
                            if "code_name" in metadata:
                                display_name += f" \"{metadata['code_name']}\""
                                
                            metadata["display_name"] = display_name
                            info(f"Created display_name for nightly build: {display_name}")
                    except Exception as e:
                        debug(f"Error formatting date for display_name: {str(e)}")
                        
                        # Simple fallback
                        display_name = f"Nightly Build - {base_version}"
                        if "code_name" in metadata:
                            display_name += f" \"{metadata['code_name']}\""
                        metadata["display_name"] = display_name
            else:
                # For stable version, use version and code_name if available
                display_name = base_version
                if "code_name" in metadata:
                    display_name += f" \"{metadata['code_name']}\""
                metadata["display_name"] = display_name
                debug(f"Created display_name from version: {display_name}")
    
    # 8. Add additional information for nightly builds
    if metadata.get("channel") == "nightly" and "display_name" in metadata:
        # Ensure display_name clearly indicates this is a nightly build if not already present
        current_display = metadata["display_name"]
        if "nightly" not in current_display.lower() and "build" not in current_display.lower():
            metadata["display_name"] = f"Nightly Build - {current_display}"
        
        # Add build number if available and not already in display_name
        if "build_number" in metadata and "build" not in current_display.lower():
            build_number = metadata["build_number"]
            if f"build {build_number}" not in current_display.lower():
                metadata["display_name"] += f" (Build {build_number})"
    
    return metadata


# Ensure version information is initialized when the module is imported
initialize_version_info()