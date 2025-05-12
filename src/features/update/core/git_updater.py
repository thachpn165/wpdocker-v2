"""
Git-based update mechanism.

This module provides update functionality for git-based installations
of the WP Docker application.
"""

import os
import subprocess
from typing import Dict, Any, Optional, List

from src.common.logging import Debug, log_call, debug, info, warn, error, success


class GitUpdater:
    """
    Handles updates for git-based installations.
    
    This class provides functionality for checking and applying updates
    to git-based installations of the WP Docker application.
    """
    
    def __init__(self):
        """Initialize the git updater."""
        self.debug = Debug("GitUpdater")
        self.repo_url = "https://github.com/username/wpdocker-v2.git"  # TODO: Update to actual repo URL
        self.project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
    @log_call
    def _run_git_command(self, command: List[str]) -> Optional[str]:
        """
        Run a git command and return the output.
        
        Args:
            command: Git command as a list of arguments
            
        Returns:
            Command output as a string, or None if an error occurred
        """
        try:
            self.debug.debug(f"Running git command: {' '.join(command)}")
            result = subprocess.run(
                command,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.debug.error(f"Git command failed: {e.stderr}")
            return None
        except Exception as e:
            self.debug.error(f"Error running git command: {str(e)}")
            return None
            
    @log_call
    def fetch_remote(self) -> bool:
        """
        Fetch the latest information from the remote repository.
        
        Returns:
            bool: True if successful, False otherwise
        """
        result = self._run_git_command(["git", "fetch", "--tags", "--prune"])
        return result is not None
        
    @log_call
    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """
        Check if updates are available.
        
        Returns:
            Dict with update information or None if no updates are available
        """
        from src.version import VERSION, CHANNEL
        
        if CHANNEL == "dev":
            self.debug.info("Dev channel does not support automatic updates")
            return None
            
        # Fetch the latest information from the remote
        if not self.fetch_remote():
            self.debug.error("Failed to fetch from remote")
            return None
            
        if CHANNEL == "stable":
            # For stable channel, check for newer version tags
            self.debug.info("Checking for newer version tags")
            
            # Get all tags sorted by version (newest first)
            result = self._run_git_command(["git", "tag", "--sort=-v:refname"])
            if not result:
                self.debug.error("Failed to get tags")
                return None
                
            # Filter to only include version tags (starting with 'v')
            tags = [tag for tag in result.split("\n") if tag.startswith("v")]
            
            if not tags:
                self.debug.info("No version tags found")
                return None
                
            # Get the latest version tag
            latest_tag = tags[0]
            latest_version = latest_tag.lstrip("v")
            
            # Compare with current version
            try:
                import semver
                
                if semver.compare(latest_version, VERSION) > 0:
                    self.debug.info(f"New version available: {latest_version}")
                    return {
                        "version": latest_version,
                        "type": "tag",
                        "reference": latest_tag
                    }
                else:
                    self.debug.info(f"Current version {VERSION} is up to date")
                    return None
            except Exception as e:
                self.debug.error(f"Error comparing versions: {str(e)}")
                return None
                
        elif CHANNEL == "nightly":
            # For nightly channel, check for newer commits on the dev branch
            self.debug.info("Checking for new commits on dev branch")
            
            # Get the current commit
            local_commit = self._run_git_command(["git", "rev-parse", "HEAD"])
            if not local_commit:
                self.debug.error("Failed to get current commit")
                return None
                
            # Get the latest commit on the dev branch
            remote_commit = self._run_git_command(["git", "rev-parse", "origin/dev"])
            if not remote_commit:
                self.debug.error("Failed to get latest commit on origin/dev")
                return None
                
            # Compare the commits
            if local_commit != remote_commit:
                self.debug.info("New commits available on dev branch")
                
                # Get the date of the remote commit for the version
                commit_date = self._run_git_command([
                    "git", "show", "-s", "--format=%cd", 
                    "--date=format:%Y%m%d", remote_commit
                ])
                
                if not commit_date:
                    commit_date = "latest"
                    
                return {
                    "version": f"nightly-{commit_date}",
                    "type": "branch",
                    "reference": "origin/dev"
                }
            else:
                self.debug.info("Already at the latest commit on dev branch")
                return None
                
        return None
        
    @log_call
    def update(self) -> bool:
        """
        Apply available updates.
        
        Returns:
            bool: True if successful, False otherwise
        """
        from src.version import CHANNEL
        
        if CHANNEL == "dev":
            self.debug.info("Dev channel does not support automatic updates")
            return False
            
        # Check for updates
        update_info = self.check_for_updates()
        if not update_info:
            self.debug.info("No updates available")
            return False
            
        try:
            # Apply the update based on the type
            if update_info["type"] == "tag":
                # Checkout the tag
                tag = update_info["reference"]
                self.debug.info(f"Checking out tag: {tag}")
                
                # First stash any changes to avoid conflicts
                self._run_git_command(["git", "stash", "save", "Auto-stashed before update"])
                
                # Checkout the tag
                result = self._run_git_command(["git", "checkout", tag])
                if not result:
                    self.debug.error(f"Failed to checkout tag: {tag}")
                    return False
                    
            elif update_info["type"] == "branch":
                # Checkout and pull the branch
                branch = update_info["reference"]
                self.debug.info(f"Checking out and pulling branch: {branch}")
                
                # First stash any changes to avoid conflicts
                self._run_git_command(["git", "stash", "save", "Auto-stashed before update"])
                
                # Checkout the branch
                result = self._run_git_command(["git", "checkout", branch])
                if not result:
                    self.debug.error(f"Failed to checkout branch: {branch}")
                    return False
                    
                # Pull the latest changes
                result = self._run_git_command(["git", "pull"])
                if not result:
                    self.debug.error(f"Failed to pull latest changes")
                    return False
                    
            # Update dependencies
            self.debug.info("Updating dependencies")
            try:
                subprocess.run(
                    ["pip", "install", "-r", "requirements.txt"],
                    cwd=self.project_dir,
                    check=True
                )
            except Exception as e:
                self.debug.warn(f"Error updating dependencies: {str(e)}")
                # Continue anyway - dependency update is not critical
                
            self.debug.success(f"Successfully updated to {update_info['version']}")
            return True
            
        except Exception as e:
            self.debug.error(f"Error applying update: {str(e)}")
            return False