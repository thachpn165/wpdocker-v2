#!/usr/bin/env python3
"""
Version bumping utility for WP Docker.

This script provides functionality for automatically bumping the version
of the WP Docker application according to semantic versioning.
"""

import argparse
import re
import subprocess
import os
from typing import Optional


def update_version_file(new_version: str) -> bool:
    """
    Update the version in the version.py file.
    
    Args:
        new_version: The new version to set
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get the path to version.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    version_file = os.path.join(project_root, "version.py")
    
    try:
        # Read the current content
        with open(version_file, "r") as f:
            content = f.read()
        
        # Update the version
        content = re.sub(
            r'VERSION = "[^"]+"',
            f'VERSION = "{new_version}"',
            content
        )
        
        # Write the updated content
        with open(version_file, "w") as f:
            f.write(content)
        
        print(f"Updated version in {version_file} to {new_version}")
        return True
    except Exception as e:
        print(f"Error updating version file: {str(e)}")
        return False


def commit_and_tag(new_version: str, push: bool = False) -> bool:
    """
    Commit the version change and create a tag.
    
    Args:
        new_version: The new version
        push: Whether to push the changes to the remote
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Add version.py to staging
        subprocess.run(["git", "add", "src/version.py"], check=True)
        
        # Commit the change
        subprocess.run(
            ["git", "commit", "-m", f"bump: version {new_version}"],
            check=True
        )
        print(f"Committed version change")
        
        # Create a tag
        subprocess.run(
            ["git", "tag", "-a", f"v{new_version}", "-m", f"Version {new_version}"],
            check=True
        )
        print(f"Created tag v{new_version}")
        
        # Push if requested
        if push:
            subprocess.run(["git", "push", "origin", "dev"], check=True)
            print("Pushed changes to dev branch")
            
            subprocess.run(["git", "push", "origin", f"v{new_version}"], check=True)
            print(f"Pushed tag v{new_version}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in git operations: {e}")
        return False
    except Exception as e:
        print(f"Error committing and tagging: {str(e)}")
        return False


def bump_version(level: str = "patch", version: Optional[str] = None, push: bool = False) -> Optional[str]:
    """
    Bump the version according to semantic versioning.
    
    Args:
        level: The level to bump (patch, minor, major)
        version: A specific version to set (overrides level)
        push: Whether to push the changes to the remote
        
    Returns:
        str: The new version, or None if an error occurred
    """
    try:
        # Get the current version
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        sys.path.insert(0, project_root)
        
        from src.version import VERSION as current_version
        
        # Calculate the new version
        if version:
            new_version = version
        else:
            import semver
            
            if level == "patch":
                new_version = semver.bump_patch(current_version)
            elif level == "minor":
                new_version = semver.bump_minor(current_version)
            elif level == "major":
                new_version = semver.bump_major(current_version)
            else:
                print(f"Invalid level: {level}")
                return None
        
        print(f"Bumping version from {current_version} to {new_version}")
        
        # Update the version file
        if not update_version_file(new_version):
            return None
        
        # Commit and tag
        if not commit_and_tag(new_version, push):
            return None
        
        print(f"Version bumped from {current_version} to {new_version}")
        
        if not push:
            print("\nTo push the changes to the remote, run:")
            print(f"  git push origin dev")
            print(f"  git push origin v{new_version}")
        
        return new_version
    except Exception as e:
        print(f"Error bumping version: {str(e)}")
        return None


if __name__ == "__main__":
    import sys
    
    parser = argparse.ArgumentParser(description="Bump the version of WP Docker")
    
    # Level argument (patch, minor, major)
    parser.add_argument(
        "level",
        choices=["patch", "minor", "major"],
        nargs="?",
        default="patch",
        help="The level to bump (patch: 0.0.x, minor: 0.x.0, major: x.0.0)"
    )
    
    # Specific version argument
    parser.add_argument(
        "--version",
        help="A specific version to set (overrides level)"
    )
    
    # Push argument
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push the changes to the remote"
    )
    
    args = parser.parse_args()
    
    # Bump the version
    new_version = bump_version(args.level, args.version, args.push)
    
    # Exit with appropriate code
    sys.exit(0 if new_version else 1)