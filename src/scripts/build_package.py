#!/usr/bin/env python3
"""
Package building utility for WP Docker.

This script creates distributable packages of the WP Docker application
for different release channels (stable, nightly, dev).
"""

import argparse
import os
import subprocess
import zipfile
import shutil
import datetime
import re
from typing import Optional


def read_version_info():
    """
    Read version information using version_helper.
    
    Returns:
        tuple: (version, channel, build_date)
    """
    # Get the root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Add project root to path to import version_helper
    import sys
    sys.path.insert(0, os.path.dirname(project_root))
    
    try:
        from src.common.utils.version_helper import get_version, get_channel, get_build_date
        
        # Get version information
        version = get_version()
        channel = get_channel()
        build_date = get_build_date()
            
        return version, channel, build_date
    except Exception as e:
        print(f"Error reading version info: {str(e)}")
        # Default values if error
        version = "0.0.0"
        channel = "stable"
        build_date = datetime.datetime.now().strftime("%Y-%m-%d")
        return version, channel, build_date


def update_version_info(channel: str) -> bool:
    """
    Update the channel and build date in config using version_helper.
    
    Args:
        channel: The channel to set
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get the root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Add project root to path to import version_helper
    import sys
    sys.path.insert(0, os.path.dirname(project_root))
    
    try:
        from src.common.utils.version_helper import get_version, update_version_info
        
        # Get the current version
        current_version = get_version()
        
        # Update build date and channel
        build_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Update version info with new channel and build date
        update_version_info(
            version=current_version,
            channel=channel,
            build_date=build_date
        )
        
        print(f"Updated version info for channel {channel} with build date {build_date}")
        return True
    except Exception as e:
        print(f"Error updating version info: {str(e)}")
        return False


def build_package(channel: str = "stable") -> Optional[str]:
    """
    Build a package for the specified channel.
    
    Args:
        channel: The channel to build for (stable, nightly, dev)
        
    Returns:
        str: The path to the created package, or None if an error occurred
    """
    try:
        # Update version info
        if not update_version_info(channel):
            return None
        
        # Read version information
        version, actual_channel, build_date = read_version_info()
        print(f"Building package for version {version}, channel {actual_channel}, build date {build_date}")
        
        # Create the output directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        dist_dir = os.path.join(project_root, "..", "dist")
        os.makedirs(dist_dir, exist_ok=True)
        
        # Determine the package filename
        if channel == "stable":
            package_name = f"wpdocker-v2-{version}.zip"
        else:
            today = datetime.datetime.now().strftime("%Y%m%d")
            package_name = f"wpdocker-v2-{channel}-{today}.zip"
            
        package_path = os.path.join(dist_dir, package_name)
        
        # Create the package
        with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from src, excluding src/config
            src_dir = os.path.join(project_root)
            for root, dirs, files in os.walk(src_dir):
                # Skip the config directory
                if "/config" in root or "\\config" in root:
                    continue

                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate the relative path for the archive
                    rel_path = os.path.relpath(file_path, os.path.dirname(project_root))
                    zipf.write(file_path, rel_path)
                        
            # Add requirements.txt
            req_file = os.path.join(project_root, "..", "requirements.txt")
            if os.path.exists(req_file):
                zipf.write(req_file, "requirements.txt")
                
            # Add README.md
            readme_file = os.path.join(project_root, "..", "README.md")
            if os.path.exists(readme_file):
                zipf.write(readme_file, "README.md")
        
        print(f"Package created: {package_path}")
        return package_path
    except Exception as e:
        print(f"Error building package: {str(e)}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a package for WP Docker")
    
    # Channel argument
    parser.add_argument(
        "--channel",
        choices=["stable", "nightly", "dev"],
        default="stable",
        help="The channel to build for"
    )
    
    args = parser.parse_args()
    
    # Build the package
    package_path = build_package(args.channel)
    
    # Exit with appropriate code
    import sys
    sys.exit(0 if package_path else 1)