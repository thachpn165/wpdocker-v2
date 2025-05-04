"""
Docker installation functionality.

This module provides functions to install and verify Docker on various operating systems.
"""
import os
import subprocess
from typing import Dict, Optional, List

from src.common.logging import log_call, info, debug, warn, error


@log_call
def install_docker_almalinux() -> bool:
    """
    Install Docker on AlmaLinux/CentOS/RHEL systems.
    
    Returns:
        bool: True if installation was successful, False otherwise.
    """
    info("📦 Installing Docker on AlmaLinux/CentOS/RHEL...")

    try:
        # Remove old Docker versions
        subprocess.run([
            "dnf", "remove", "-y",
            "docker", "docker-client", "docker-client-latest", "docker-common",
            "docker-latest", "docker-latest-logrotate", "docker-logrotate",
            "docker-engine", "podman", "runc"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Install dnf plugin
        subprocess.run(["dnf", "-y", "install", "dnf-plugins-core"], check=True)

        # Add Docker repo
        subprocess.run(["dnf", "config-manager", "--add-repo", 
                       "https://download.docker.com/linux/centos/docker-ce.repo"], check=True)

        # Install Docker
        subprocess.run([
            "dnf", "install", "-y",
            "docker-ce", "docker-ce-cli", "containerd.io",
            "docker-buildx-plugin", "docker-compose-plugin"
        ], check=True)

        # Start Docker service
        subprocess.run(["systemctl", "enable", "--now", "docker"], check=True)

        info("✅ Docker installed and service started.")
    except Exception as e:
        error(f"Failed to install Docker: {e}")
        return False

    return verify_docker()


@log_call
def install_docker_general() -> bool:
    """
    Install Docker using the official get.docker.com script.
    
    This method works on most Linux distributions.
    
    Returns:
        bool: True if installation was successful, False otherwise.
    """
    info("📦 Installing Docker via get.docker.com script...")

    script_url = "https://get.docker.com"
    tmp_script = "/tmp/install-docker.sh"

    try:
        subprocess.run(["curl", "-fsSL", script_url, "-o", tmp_script], check=True)
        subprocess.run(["chmod", "+x", tmp_script], check=True)
        subprocess.run(["sh", tmp_script], check=True)
        os.remove(tmp_script)
    except Exception as e:
        error(f"Docker installation script failed: {e}")
        return False

    return verify_docker()


@log_call
def verify_docker() -> bool:
    """
    Verify that Docker is installed and running correctly.
    
    This function checks Docker version, Docker Compose version,
    service status, and runs a test container.
    
    Returns:
        bool: True if verification was successful, False otherwise.
    """
    try:
        subprocess.run(["docker", "--version"], check=True)
        subprocess.run(["docker", "compose", "version"], check=True)
        subprocess.run(["systemctl", "is-active", "docker"], check=True)
        subprocess.run(["docker", "run", "--rm", "hello-world"], check=True)
        info("🎉 Docker verified successfully.")
        return True
    except Exception as e:
        warn(f"⚠️ Docker verification failed: {e}")
        return False


@log_call
def install_docker_if_missing() -> bool:
    """
    Check if Docker is installed, and install it if missing.
    
    This function detects the operating system and calls the appropriate
    installation method based on the OS type.
    
    Returns:
        bool: True if Docker is installed (or was already installed), False otherwise.
    """
    # Check if Docker is already installed
    if subprocess.call(["which", "docker"], stdout=subprocess.DEVNULL) == 0:
        try:
            subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL)
            info("🐳 Docker already installed and running.")
            return True
        except Exception:
            warn("⚠️ Docker found but not running. Attempting to start.")
            subprocess.run(["systemctl", "enable", "--now", "docker"])
            return True

    # Detect OS
    os_info = get_os_info()
    os_name = os_info.get("ID", "")
    os_version = os_info.get("VERSION_ID", "").split(".")[0] if os_info.get("VERSION_ID") else ""

    if os_name in ["almalinux", "centos", "rhel"] and os_version in ["8", "9"]:
        return install_docker_almalinux()
    else:
        return install_docker_general()


def get_os_info() -> Dict[str, str]:
    """
    Get operating system information from /etc/os-release.
    
    Returns:
        Dict[str, str]: Dictionary containing OS information.
    """
    os_info = {}
    
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            lines = f.readlines()
            
        for line in lines:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                os_info[key] = value.strip('"')
                
    return os_info