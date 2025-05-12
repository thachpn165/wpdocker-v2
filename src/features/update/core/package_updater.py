"""
Package-based update mechanism.

This module provides update functionality for package-based installations
of the WP Docker application.
"""

import os
import requests
import zipfile
import shutil
from typing import Dict, Any, Optional

from src.common.logging import Debug, log_call, debug, info, warn, error, success
from src.common.utils.environment import env


class PackageUpdater:
    """
    Handles updates for package-based installations.
    
    This class provides functionality for checking and applying updates
    to package-based installations of the WP Docker application.
    """
    
    def __init__(self):
        """Initialize the package updater."""
        self.debug = Debug("PackageUpdater")
        self.github_api_url = "https://api.github.com/repos/username/wpdocker-v2"  # TODO: Update to actual repo URL
        
    @log_call
    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """
        Check if updates are available from GitHub releases.
        
        Returns:
            Dict with update information or None if no updates are available
        """
        from src.version import VERSION, CHANNEL
        
        if CHANNEL == "dev":
            self.debug.info("Dev channel does not support automatic updates")
            return None
            
        try:
            headers = {}
            # Add GitHub token if available (for higher rate limits)
            github_token = env.get("GITHUB_TOKEN")
            if github_token:
                headers["Authorization"] = f"token {github_token}"
                
            if CHANNEL == "stable":
                # For stable channel, get the latest release
                self.debug.info("Checking for latest stable release")
                response = requests.get(
                    f"{self.github_api_url}/releases/latest",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code != 200:
                    self.debug.error(f"Failed to get latest release: {response.status_code}")
                    return None
                    
                release_data = response.json()
                
            else:  # nightly
                # For nightly channel, get the latest pre-release
                self.debug.info("Checking for latest nightly release")
                response = requests.get(
                    f"{self.github_api_url}/releases?per_page=5",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code != 200:
                    self.debug.error(f"Failed to get releases: {response.status_code}")
                    return None
                    
                # Find the first pre-release
                releases = response.json()
                prerelease = next((r for r in releases if r.get("prerelease", False)), None)
                
                if not prerelease:
                    self.debug.info("No nightly releases found")
                    return None
                    
                release_data = prerelease
                
            # Extract version from the tag name
            tag_name = release_data.get("tag_name", "")
            if not tag_name:
                self.debug.error("Release tag name is empty")
                return None
                
            latest_version = tag_name.lstrip("v")
            
            # Compare with current version
            try:
                import semver
                
                if semver.compare(latest_version, VERSION) > 0:
                    # Find the asset to download
                    assets = release_data.get("assets", [])
                    if not assets:
                        self.debug.error("No assets found in release")
                        return None
                        
                    # Look for the appropriate asset based on platform
                    # For now, just get the first asset
                    asset = assets[0]
                    download_url = asset.get("browser_download_url")
                    
                    if not download_url:
                        self.debug.error("No download URL found for asset")
                        return None
                        
                    # Prepare update information
                    update_info = {
                        "version": latest_version,
                        "url": download_url,
                        "notes": release_data.get("body", "")
                    }
                    
                    self.debug.info(f"New version available: {latest_version}")
                    return update_info
                else:
                    self.debug.info(f"Current version {VERSION} is up to date")
                    return None
            except Exception as e:
                self.debug.error(f"Error comparing versions: {str(e)}")
                return None
                
        except Exception as e:
            self.debug.error(f"Error checking for updates: {str(e)}")
            return None
            
    @log_call
    def download_and_install_update(self, update_info: Dict[str, Any]) -> bool:
        """
        Download and install an update.
        
        Args:
            update_info: Update information from check_for_updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a temporary directory for the update
            temp_dir = os.path.join(env.get("TEMP_DIR", "/tmp"), "wpdocker_update")
            os.makedirs(temp_dir, exist_ok=True)
            self.debug.info(f"Created temporary directory: {temp_dir}")
            
            # Download the update
            zip_path = os.path.join(temp_dir, "update.zip")
            self.debug.info(f"Downloading update from {update_info['url']}")
            
            response = requests.get(update_info["url"], stream=True, timeout=60)
            if response.status_code != 200:
                self.debug.error(f"Failed to download update: {response.status_code}")
                return False
                
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            self.debug.info(f"Download completed: {zip_path}")
            
            # Verify the downloaded file
            if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
                self.debug.error("Downloaded file is empty or does not exist")
                return False
                
            # Extract the update
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            self.debug.info(f"Extracting update to {extract_dir}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
            # Install the update
            # This depends on the actual package structure
            # For now, we'll implement a simple copy
            install_dir = env.get("INSTALL_DIR")
            if not install_dir:
                self.debug.error("INSTALL_DIR environment variable not set")
                return False
                
            # Copy files to the installation directory
            self.debug.info(f"Installing update to {install_dir}")
            
            # Example: Copy the src directory
            src_dir = os.path.join(extract_dir, "src")
            if os.path.exists(src_dir):
                # Backup current src directory
                src_backup = os.path.join(temp_dir, "src_backup")
                if os.path.exists(os.path.join(install_dir, "src")):
                    shutil.copytree(
                        os.path.join(install_dir, "src"),
                        src_backup
                    )
                    self.debug.info(f"Backed up src directory to {src_backup}")
                
                # Copy new src directory
                shutil.rmtree(os.path.join(install_dir, "src"), ignore_errors=True)
                shutil.copytree(
                    src_dir,
                    os.path.join(install_dir, "src")
                )
                self.debug.info("Copied new src directory")
            else:
                self.debug.warn("src directory not found in update package")
                
            # Copy requirements.txt if it exists
            req_file = os.path.join(extract_dir, "requirements.txt")
            if os.path.exists(req_file):
                shutil.copy(
                    req_file,
                    os.path.join(install_dir, "requirements.txt")
                )
                self.debug.info("Copied new requirements.txt")
                
                # Update dependencies
                try:
                    self.debug.info("Updating dependencies")
                    subprocess.run(
                        ["pip", "install", "-r", "requirements.txt"],
                        cwd=install_dir,
                        check=True
                    )
                except Exception as e:
                    self.debug.warn(f"Error updating dependencies: {str(e)}")
                    # Continue anyway - dependency update is not critical
            
            # Clean up
            try:
                shutil.rmtree(temp_dir)
                self.debug.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                self.debug.warn(f"Error cleaning up: {str(e)}")
                
            self.debug.success(f"Successfully updated to version {update_info['version']}")
            return True
            
        except Exception as e:
            self.debug.error(f"Error installing update: {str(e)}")
            return False