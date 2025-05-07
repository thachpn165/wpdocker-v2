"""
Rclone management menu prompt module.

This module provides the user interface for Rclone management functions
like adding/removing remotes, file operations, and cloud backup management.
"""

import os
import datetime
import questionary
from questionary import prompt
from typing import Dict, List, Optional, Tuple, Any

from src.common.logging import info, error, debug, success
from src.common.utils.environment import env
from src.common.utils.editor import choose_editor
from src.common.containers.path_utils import convert_host_path_to_container
from src.common.containers.utils import handle_container_check
from src.common.ui.prompt_helpers import (
    custom_style, 
    wait_for_enter, 
    prompt_with_cancel,
    execute_with_exception_handling
)
from src.features.rclone.manager import RcloneManager
from src.features.rclone.config.manager import RcloneConfigManager
from src.features.rclone.backup_integration import RcloneBackupIntegration
from src.features.rclone.utils.remote_utils import (
    format_size,
    get_remote_type_display_name,
    ensure_remotes_available,
    create_directory_structure,
    get_available_websites,
    get_backup_files_for_website,
    # New utility functions
    create_remote_choices,
    select_remote,
    select_website,
    select_backup_file,
    process_backup_files,
    validate_backup_path,
    execute_rclone_operation
)


# Note: create_remote_choices function has been moved to remote_utils.py


def prompt_remote_params(remote_type: str) -> Dict[str, str]:
    """Prompt for remote-specific parameters and provide detailed guidance.
    
    Args:
        remote_type: Type of remote (s3, drive, etc.)
        
    Returns:
        Dict[str, str]: Parameters for the remote configuration
    """
    params = {}
    
    # Get a user-friendly display name
    display_name = get_remote_type_display_name(remote_type)
    
    # Show detailed guidance based on remote type
    info("\n" + "="*80)
    info(f"🛠️  SETUP GUIDE FOR {display_name.upper()}")
    info("="*80)
    
    if remote_type == "s3":
        info("""
To set up Amazon S3 or compatible S3 service, you need:

1. Access Key ID and Secret Access Key:
   - For AWS S3: Create at https://console.aws.amazon.com/iam/
   - For Wasabi, DigitalOcean Spaces: Create in the service control panel

2. Region: The region you chose when creating the bucket
   - Examples: us-east-1, eu-west-2, ap-southeast-1, etc.

3. Endpoint (only needed for S3-compatible services):
   - Wasabi: s3.wasabisys.com or s3.eu-central-1.wasabisys.com
   - DigitalOcean: nyc3.digitaloceanspaces.com (replace nyc3 with your region)
   - Cloudflare R2: <account-id>.r2.cloudflarestorage.com

All this information is available in your service dashboard.
""")
        params["provider"] = questionary.select(
            "Select S3 provider:",
            choices=[
                {"name": "AWS", "value": "AWS"},
                {"name": "Wasabi", "value": "Wasabi"},
                {"name": "DigitalOcean", "value": "DigitalOcean"},
                {"name": "Cloudflare R2", "value": "Other"},
                {"name": "Minio", "value": "Minio"},
                {"name": "Other", "value": "Other"},
            ],
            style=custom_style
        ).ask()
        
        params["access_key_id"] = questionary.text(
            "Enter Access Key ID:",
            style=custom_style
        ).ask()
        
        params["secret_access_key"] = questionary.password(
            "Enter Secret Access Key:",
            style=custom_style
        ).ask()
        
        params["region"] = questionary.text(
            "Enter Region:",
            style=custom_style
        ).ask()
        
        # Only ask for endpoint for non-AWS providers
        if params["provider"] != "AWS":
            params["endpoint"] = questionary.text(
                "Enter Endpoint URL:",
                style=custom_style
            ).ask()
        
        bucket = questionary.text(
            "Enter Bucket Name:",
            style=custom_style
        ).ask()
        if bucket:
            params["bucket"] = bucket
    
    elif remote_type == "b2":
        info("""
To set up Backblaze B2, you need:

1. Account ID and Application Key:
   - Log in to Backblaze B2 at https://secure.backblaze.com/b2_buckets.htm
   - In the dashboard, click "App Keys" in the left menu
   - Create a new Application Key with appropriate permissions
   - Note: You'll only see the Application Key once when created, save it immediately!

Application Keys can be limited to a specific bucket or apply to the entire account.
""")
        params["account"] = questionary.text(
            "Enter Account ID:",
            style=custom_style
        ).ask()
        
        params["key"] = questionary.password(
            "Enter Application Key:",
            style=custom_style
        ).ask()
    
    elif remote_type in ["drive", "dropbox", "onedrive", "box", "mega", "pcloud"]:
        info(f"\n⚠️ IMPORTANT - VPS AND SSH ENVIRONMENT ⚠️\n")
        info(f"{display_name} uses OAuth authentication, which requires a web browser.")
        info("When using SSH on a VPS, you should create the Rclone config on your local machine first,")
        info("then copy the configuration to the VPS.\n")
        
        info("Setup instructions:\n")
        info("1. Install Rclone on your local machine (personal computer):")
        info("   - Download from: https://rclone.org/downloads/")
        info("   - Or install via terminal: curl https://rclone.org/install.sh | sudo bash\n")
        
        info("2. Run the following command to create a configuration:")
        info("   - rclone config")
        info("   - Choose \"New remote\" (n)")
        info("   - Enter a remote name (e.g., \"mydrive\")")
        info(f"   - Select the type \"{display_name}\" ({remote_type})")
        info("   - Follow the OAuth authentication process in the browser")
        info("   - Complete the setup\n")
        
        info("3. Copy the configuration from your local machine to the VPS:")
        info("   - Configuration file is usually at: ~/.config/rclone/rclone.conf")
        config_dir = env.get("CONFIG_DIR")
        info(f"   - Use command: scp ~/.config/rclone/rclone.conf user@your_vps:/path/to/{config_dir}/rclone/rclone.conf\n")
        
        info("4. Or copy the content from your local rclone.conf and paste it below")
        info("   (the format should look like this):\n")
        
        info("   [remote-name]")
        info(f"   type = {remote_type}")
        info('   token = {"access_token":"xxxxxx","token_type":"Bearer","refresh_token":"xxxxxx","expiry":"2025-12-31T12:00:00Z"}')
        info("   client_id = xxxxxx")
        info("   client_secret = xxxxxx")
        info("   ...\n")
        
        use_manual_config = questionary.confirm(
            "Do you have a configuration from your local machine to paste?",
            style=custom_style,
            default=True
        ).ask()
        
        if use_manual_config:
            import tempfile
            import subprocess
            
            # Create a temporary file for the user to enter configuration
            with tempfile.NamedTemporaryFile(suffix='.conf', delete=False, mode='w+') as temp_file:
                temp_path = temp_file.name
                # Create a template for the user
                temp_file.write(f"# Paste your {remote_type} configuration below, do not include the remote name [xxx]\n")
                temp_file.write(f"# Example for {remote_type}:\n")
                temp_file.write(f"type = {remote_type}\n")
                temp_file.write('token = {"access_token":"xxxxxx","token_type":"Bearer","refresh_token":"xxxxxx","expiry":"2025-12-31T12:00:00Z"}\n')
                temp_file.write("client_id = xxxxxx\n")
                temp_file.write("client_secret = xxxxxx\n")
                temp_file.write("# Delete these lines and paste your actual configuration here\n")
            
            info("\nAfter the editor opens:")
            info("- Paste your Rclone configuration")
            info("- Delete the guide lines (starting with #)")
            info("- Save and close the editor to continue")
            
            # Choose and open an editor
            default_editor = env.get("EDITOR")
            editor = choose_editor(default_editor)
            
            # Cancel if user doesn't choose an editor
            if not editor:
                os.unlink(temp_path)
                info("\n❌ Configuration entry canceled.")
                return {}
            
            try:
                # Open the selected editor
                subprocess.run([editor, temp_path], check=True)
                
                # Read the configuration file after user has saved
                with open(temp_path, 'r') as f:
                    content = f.read()
                
                # Filter out meaningful lines, skip comments and empty lines
                raw_config_lines = []
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        raw_config_lines.append(line)
                
                # Clean up the temporary file
                os.unlink(temp_path)
            
            except Exception as e:
                error(f"\n❌ Error when opening editor: {str(e)}")
                return {}
            
            # Parse the configuration
            if not raw_config_lines:
                error("\n❌ No configuration was entered. Please try again.")
                return {}
            
            raw_config = "\n".join(raw_config_lines)
            
            # Validate the raw config (check for required fields)
            valid = False
            
            # Check for required fields
            has_type = f"type = {remote_type}" in raw_config 
            has_token = "token =" in raw_config
            
            # Check for valid JSON token format
            token_valid = True
            if has_token:
                token_line = next((line for line in raw_config_lines if "token =" in line), "")
                if token_line:
                    # Simple check to ensure the token JSON contains valid expiry date format
                    if '"expiry":"***"' in token_line or '"expiry":"date"' in token_line:
                        token_valid = False
                        error("\n❌ Token contains placeholder values. Please use your actual token.")
                        error("The expiry date should be a valid date like: 2025-12-31T12:00:00Z")
            
            if has_type and has_token and token_valid:
                valid = True
            
            if not valid:
                error("\n❌ Invalid configuration. Please check the format.")
                error("Make sure it contains the correct type and valid token parameters.")
                return {}
            
            # Parse into parameters
            config_params = {}
            for line in raw_config_lines:
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key != "type":  # We already know the type
                        config_params[key] = value
            
            success(f"\n✅ Manual configuration received successfully.")
            info(f"This will be saved directly to the rclone.conf file for '{remote_type}'.")
            info("This allows you to use cloud storage without OAuth browser authentication.")
            return config_params
        
        # If the user doesn't want to use manual configuration
        info("\nYou chose not to enter manual configuration.")
        info(f"To set up {display_name}, you'll need to run manual configuration:")
        info(f"  docker exec -it {env.get('RCLONE_CONTAINER_NAME', 'wpdocker_rclone')} rclone config")
        info("Follow the interactive prompts in that command to set up your remote.")
        return {}
    
    elif remote_type in ["sftp", "ftp"]:
        info(f"""
To set up {remote_type.upper()} connection, you need:

1. Server information:
   - Host: IP address or domain name of the server
   - Port: Connection port (default is 22 for SFTP, 21 for FTP)

2. Login credentials:
   - Username: Your username on the server
   - Password: Your password (can be blank if using key-based auth for SFTP)

For SFTP, you can use key-based authentication instead of a password.
""")
        params["host"] = questionary.text(
            "Enter Host (server address):",
            style=custom_style
        ).ask()
        
        params["user"] = questionary.text(
            "Enter Username:",
            style=custom_style
        ).ask()
        
        params["pass"] = questionary.password(
            "Enter Password (leave empty for key-based auth):",
            style=custom_style
        ).ask()
        
        params["port"] = questionary.text(
            f"Enter Port (default: {'22' if remote_type == 'sftp' else '21'}):",
            default=f"{'22' if remote_type == 'sftp' else '21'}",
            style=custom_style
        ).ask()
    
    elif remote_type == "webdav":
        info("""
To set up WebDAV, you need:

1. WebDAV Server URL:
   - Nextcloud/Owncloud: https://your-cloud.com/remote.php/webdav/
   - SharePoint: https://your-sharepoint.com/sites/your-site/_api/web/getfolderbyserverrelativeurl('/shared%20documents')/files
   - Other services: Check the documentation for your specific service

2. Login credentials:
   - Username: Your WebDAV username
   - Password: Your WebDAV password

For Nextcloud/Owncloud, you can create App Passwords in the Security section.
""")
        params["url"] = questionary.text(
            "Enter WebDAV URL:",
            style=custom_style
        ).ask()
        
        params["vendor"] = questionary.select(
            "Select WebDAV Service Provider:",
            choices=[
                {"name": "Nextcloud", "value": "nextcloud"},
                {"name": "Owncloud", "value": "owncloud"},
                {"name": "SharePoint", "value": "sharepoint"},
                {"name": "Other", "value": "other"},
            ],
            style=custom_style
        ).ask()
        
        params["user"] = questionary.text(
            "Enter Username:",
            style=custom_style
        ).ask()
        
        params["pass"] = questionary.password(
            "Enter Password:",
            style=custom_style
        ).ask()
    
    elif remote_type == "azureblob":
        info("""
To set up Azure Blob Storage, you need:

1. Storage Account Name:
   - Found in the Azure portal under Storage Accounts

2. Account Key or SAS URL:
   - Account Key: Found in the "Access keys" section of the Storage Account
   - SAS URL: Can be generated in the "Shared access signature" section

You can find this information in the Azure Portal: https://portal.azure.com/
""")
        params["account"] = questionary.text(
            "Enter Storage Account Name:",
            style=custom_style
        ).ask()
        
        params["key"] = questionary.password(
            "Enter Account Key:",
            style=custom_style
        ).ask()
    
    else:
        info(f"""
For {remote_type}, we'll use an interactive configuration process.

For more details on setting up {remote_type}, please refer to:
https://rclone.org/docs/#{remote_type}

After continuing, the system will guide you through the setup process.
""")
        return {}
    
    info("\nAfter entering this information, rclone may request additional authentication via the web browser.")
    info("Please follow on-screen instructions when prompted.")
    info("="*80 + "\n")
    
    return {k: v for k, v in params.items() if v}  # Filter out empty values


def list_remotes() -> None:
    """List all configured rclone remotes with their types."""
    def _list_remotes():
        rclone_manager = RcloneManager()
        config_manager = RcloneConfigManager()
        
        # Check if Rclone container is running
        if not handle_container_check(rclone_manager):
            return
        
        # Get list of remotes
        remotes = rclone_manager.list_remotes()
        if remotes:
            info("\n📋 Configured Remotes:")
            for i, remote in enumerate(remotes, 1):
                # Get remote type for more detailed display
                remote_config = config_manager.get_remote_config(remote)
                remote_type = remote_config.get("type", "unknown") if remote_config else "unknown"
                display_type = get_remote_type_display_name(remote_type)
                
                info(f"{i}. {remote} ({display_type})")
        else:
            info("No remotes configured yet.")
        wait_for_enter()
    
    execute_with_exception_handling(_list_remotes, "Error listing remotes")


def add_remote() -> None:
    """Add a new rclone remote with interactive configuration."""
    def _add_remote():
        rclone_manager = RcloneManager()
        config_manager = RcloneConfigManager()
        
        # Check if Rclone container is running
        if not handle_container_check(rclone_manager):
            return
        
        # Get remote name
        remote_name = questionary.text(
            "Enter name for the new remote:",
            style=custom_style
        ).ask()
        
        if not remote_name:
            return
        
        # Extended list of remote types
        remote_types = [
            {"name": "S3 (Amazon S3, Wasabi, etc.)", "value": "s3"},
            {"name": "Google Drive", "value": "drive"},
            {"name": "Dropbox", "value": "dropbox"},
            {"name": "Microsoft OneDrive", "value": "onedrive"},
            {"name": "SFTP", "value": "sftp"},
            {"name": "FTP", "value": "ftp"},
            {"name": "WebDAV / Nextcloud", "value": "webdav"},
            {"name": "Backblaze B2", "value": "b2"},
            {"name": "Box", "value": "box"},
            {"name": "Azure Blob Storage", "value": "azureblob"},
            {"name": "Cancel", "value": "cancel"},
        ]
        
        remote_type = questionary.select(
            "Select remote type:",
            choices=remote_types,
            style=custom_style
        ).ask()
        
        if remote_type == "cancel":
            return
        
        # Use the prompt_remote_params function to get the parameters with detailed guidance
        params = prompt_remote_params(remote_type)
        
        # Add the remote if parameters were provided
        if params:
            # If this is an OAuth method and there's a token, use ConfigManager directly
            if remote_type in ["drive", "dropbox", "onedrive", "box"] and "token" in params:
                # Add type to params for direct configuration
                params["type"] = remote_type
                
                # Use ConfigManager to add directly to the config file
                success_result = config_manager.add_remote(remote_name, params)
                
                if success_result:
                    success(f"✅ Remote '{remote_name}' added successfully using manual configuration")
                else:
                    error(f"❌ Failed to add remote '{remote_name}' to config file")
            else:
                # Use the RcloneManager method to add the remote
                success_result = rclone_manager.add_remote(remote_name, remote_type, params)
                
                if success_result:
                    success(f"✅ Remote '{remote_name}' added successfully")
                else:
                    error(f"❌ Failed to add remote '{remote_name}'")
        
        wait_for_enter()
    
    execute_with_exception_handling(_add_remote, "Error adding remote")


def remove_remote() -> None:
    """Remove a configured rclone remote with confirmation."""
    def _remove_remote():
        rclone_manager = RcloneManager()
        config_manager = RcloneConfigManager()
        
        # Check if Rclone container is running
        if not handle_container_check(rclone_manager):
            return
        
        # Get list of remotes
        remotes = rclone_manager.list_remotes()
        if not remotes:
            info("No remotes configured yet.")
            wait_for_enter()
            return
        
        # Select remote using utility function
        remote_to_remove = select_remote(remotes, "Select remote to remove:", config_manager)
        if not remote_to_remove:
            return
            
        # Show clear warning with remote information
        config = config_manager.get_remote_config(remote_to_remove)
        if config:
            remote_type = config.get("type", "unknown")
            display_type = get_remote_type_display_name(remote_type)
            info(f"\n⚠️  WARNING: You are about to delete the '{remote_to_remove}' ({display_type}) remote.")
            info("    This action cannot be undone and will remove the configuration linked to this service.")
            info("    Data stored on the service will not be affected.")
        
        # Confirm removal
        confirm = questionary.confirm(
            f"Are you sure you want to remove '{remote_to_remove}'?",
            style=custom_style,
            default=False
        ).ask()
        
        if confirm:
            # Use execute_rclone_operation utility
            def remove_operation():
                success_result = rclone_manager.remove_remote(remote_to_remove)
                return success_result, f"Remote '{remote_to_remove}' removed" if success_result else "Failed to remove remote"
            
            execute_rclone_operation(
                remove_operation,
                f"Remote '{remote_to_remove}' removed successfully",
                f"Failed to remove remote '{remote_to_remove}'"
            )
        
        wait_for_enter()
    
    execute_with_exception_handling(_remove_remote, "Error removing remote")


def view_remote_config() -> None:
    """View detailed configuration of a selected remote."""
    def _view_remote_config():
        rclone_manager = RcloneManager()
        config_manager = RcloneConfigManager()
        
        # Check if Rclone container is running
        if not handle_container_check(rclone_manager):
            return
        
        # Get list of remotes
        remotes = rclone_manager.list_remotes()
        if not remotes:
            info("No remotes configured yet.")
            wait_for_enter()
            return
        
        # Select remote using utility function
        selected_remote = select_remote(remotes, "Select remote to view:", config_manager)
        if not selected_remote:
            return
            
        remote_config = config_manager.get_remote_config(selected_remote)
        
        if remote_config:
            remote_type = remote_config.get("type", "unknown")
            display_type = get_remote_type_display_name(remote_type)
            
            info(f"\nConfiguration details for '{selected_remote}' ({display_type}):")
            info("="*80)
            
            # Group the information for better display
            # Group 1: Basic information
            info("BASIC INFORMATION:")
            info(f"  Name: {selected_remote}")
            info(f"  Type: {display_type}")
            
            # Group 2: Connection and authentication
            info("\nCONNECTION DETAILS:")
            for key, value in remote_config.items():
                if key == "type":
                    continue  # Already displayed above
                
                # User-friendly labels for fields
                key_display = {
                    "provider": "Provider",
                    "access_key_id": "Access Key ID",
                    "region": "Region",
                    "endpoint": "Endpoint",
                    "account": "Account",
                    "user": "Username",
                    "host": "Host",
                    "port": "Port",
                    "url": "URL"
                }.get(key, key)
                
                # Mask sensitive information
                if key in ["secret", "key", "pass", "password", "secret_access_key", "token", "client_secret"]:
                    value = "********"
                    key_display = f"{key_display} (hidden)"
                    
                info(f"  {key_display}: {value}")
            
            info("="*80)
            
            # Add usage information
            info(f"\nNote: This shows the remote configuration. To manage data,")
            info(f"use options like 'View backup files' or 'Backup to remote'.")
        else:
            error(f"❌ Failed to retrieve configuration for '{selected_remote}'")
        
        wait_for_enter()
    
    execute_with_exception_handling(_view_remote_config, "Error viewing remote configuration")


def prompt_manage_remotes() -> None:
    """Display Rclone remotes management menu and handle user selection."""
    def _prompt_manage_remotes():
        # Check if Rclone container is running
        rclone_manager = RcloneManager()
        if not handle_container_check(rclone_manager):
            return
        
        choices = [
            {"name": "1. List Remotes", "value": "1"},
            {"name": "2. Add Remote", "value": "2"},
            {"name": "3. Remove Remote", "value": "3"},
            {"name": "4. View Remote Configuration", "value": "4"},
            {"name": "0. Back", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n🛰️  Rclone Remotes Management:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "0":
            return
        elif answer == "1":
            list_remotes()
        elif answer == "2":
            add_remote()
        elif answer == "3":
            remove_remote()
        elif answer == "4":
            view_remote_config()
    
    execute_with_exception_handling(_prompt_manage_remotes, "Error in remotes management menu")


def list_remote_files() -> None:
    """List files and directories on a remote storage."""
    def _list_remote_files():
        rclone_manager = RcloneManager()
        
        # Check if Rclone container is running
        if not handle_container_check(rclone_manager):
            return
        
        # Get list of remotes
        remotes = ensure_remotes_available(rclone_manager)
        if not remotes:
            return
        
        # Select remote
        remote_choices = create_remote_choices(remotes)
        selected_remote = prompt_with_cancel(remote_choices, "Select remote:")
        
        if not selected_remote:
            return
        
        # Get path
        remote_path = questionary.text(
            "Enter path on remote (leave empty for root):",
            style=custom_style
        ).ask() or ""
        
        # List files in remote path
        files = rclone_manager.list_files(selected_remote, remote_path)
        
        if files:
            info(f"\n📋 Files/directories in '{selected_remote}:{remote_path}':")
            for i, file_info in enumerate(files, 1):
                file_type = "📁" if file_info.get("IsDir", False) else "📄"
                file_name = file_info.get("Name", "Unknown")
                file_size = file_info.get("Size", 0)
                size_str = format_size(file_size)
                info(f"{i}. {file_type} {file_name} ({size_str})")
        else:
            info(f"No files found in '{selected_remote}:{remote_path}'")
        
        wait_for_enter()
    
    execute_with_exception_handling(_list_remote_files, "Error listing remote files")


def sync_directories() -> None:
    """Sync directories between local and remote storage or between remotes."""
    def _sync_directories():
        rclone_manager = RcloneManager()
        
        # Check if Rclone container is running
        if not handle_container_check(rclone_manager):
            return
        
        # Get list of remotes
        remotes = ensure_remotes_available(rclone_manager)
        if not remotes:
            return
        
        # Select source type
        source_choices = create_remote_choices(remotes)
        source_choices.insert(0, {"name": "Local directory", "value": "local"})
        
        source_type = prompt_with_cancel(source_choices, "Select source type:")
        
        if not source_type:
            return
        
        if source_type == "local":
            # Local source, remote destination
            source_path = questionary.text(
                "Enter local source directory (absolute path):",
                style=custom_style
            ).ask()
            
            if not source_path:
                return
            
            # Validate source path exists
            if not os.path.exists(source_path):
                error(f"❌ Source path '{source_path}' does not exist")
                wait_for_enter(True)
                return
            
            # Select remote destination
            dest_choices = create_remote_choices(remotes)
            
            dest_remote = prompt_with_cancel(dest_choices, "Select destination remote:")
            
            if not dest_remote:
                return
            
            dest_path = questionary.text(
                "Enter destination path on remote:",
                style=custom_style
            ).ask() or ""
            
            # Prepare destination
            if not dest_remote.endswith(':'):
                dest_remote = f"{dest_remote}:"
            destination = f"{dest_remote}{dest_path}"
        
        else:
            # Remote source
            source_remote = source_type
            
            source_path = questionary.text(
                f"Enter path on '{source_remote}':",
                style=custom_style
            ).ask() or ""
            
            # Prepare source
            if not source_remote.endswith(':'):
                source_remote = f"{source_remote}:"
            source = f"{source_remote}{source_path}"
            
            # Select destination type
            dest_choices = [
                {"name": "Local directory", "value": "local"},
                {"name": "Another remote", "value": "remote"},
                {"name": "Cancel", "value": "cancel"},
            ]
            
            dest_type = prompt_with_cancel(dest_choices, "Select destination type:")
            
            if not dest_type:
                return
            
            if dest_type == "local":
                # Local destination
                destination = questionary.text(
                    "Enter local destination directory (absolute path):",
                    style=custom_style
                ).ask()
                
                if not destination:
                    return
                
                # Ensure destination directory exists
                os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            else:
                # Remote destination
                remaining_remotes = [r for r in remotes if r != source_type]
                dest_remote_choices = create_remote_choices(remaining_remotes)
                
                dest_remote = prompt_with_cancel(
                    dest_remote_choices,
                    "Select destination remote:"
                )
                
                if not dest_remote:
                    return
                
                dest_path = questionary.text(
                    "Enter destination path on remote:",
                    style=custom_style
                ).ask() or ""
                
                # Prepare destination
                if not dest_remote.endswith(':'):
                    dest_remote = f"{dest_remote}:"
                destination = f"{dest_remote}{dest_path}"
        
        # Configure sync flags
        flags = ["--progress"]
        
        if questionary.confirm(
            "Add --dry-run flag to simulate the operation without actually transferring files?",
            style=custom_style
        ).ask():
            flags.append("--dry-run")
        
        # Perform sync operation
        if source_type == "local":
            info(f"\n🔄 Syncing from {source_path} to {destination}...")
            success_result, message = rclone_manager.sync(source_path, destination, flags)
        else:
            info(f"\n🔄 Syncing from {source} to {destination}...")
            success_result, message = rclone_manager.sync(source, destination, flags)
        
        if success_result:
            success("✅ Sync operation completed successfully")
            info(message)
        else:
            error(f"❌ Sync operation failed: {message}")
        
        wait_for_enter()
    
    execute_with_exception_handling(_sync_directories, "Error syncing directories")


def copy_files() -> None:
    """Copy files between local and remote storage or between remotes."""
    def _copy_files():
        rclone_manager = RcloneManager()
        
        # Check if Rclone container is running
        if not handle_container_check(rclone_manager):
            return
        
        # Get list of remotes
        remotes = ensure_remotes_available(rclone_manager)
        if not remotes:
            return
        
        # Select source type
        source_choices = create_remote_choices(remotes)
        source_choices.insert(0, {"name": "Local file", "value": "local"})
        
        source_type = prompt_with_cancel(source_choices, "Select source type:")
        
        if not source_type:
            return
        
        if source_type == "local":
            # Local source, remote destination
            source_path = questionary.text(
                "Enter local source file (absolute path):",
                style=custom_style
            ).ask()
            
            if not source_path:
                return
            
            # Validate source path exists
            if not os.path.exists(source_path):
                error(f"❌ Source file '{source_path}' does not exist")
                wait_for_enter(True)
                return
            
            # Select remote destination
            dest_choices = create_remote_choices(remotes)
            
            dest_remote = prompt_with_cancel(dest_choices, "Select destination remote:")
            
            if not dest_remote:
                return
            
            dest_path = questionary.text(
                "Enter destination path on remote:",
                style=custom_style
            ).ask() or ""
            
            # If destination is a directory (ends with / or is empty), append source filename
            if not dest_path or dest_path.endswith('/'):
                dest_path = f"{dest_path}{os.path.basename(source_path)}"
            
            # Prepare destination
            if not dest_remote.endswith(':'):
                dest_remote = f"{dest_remote}:"
            destination = f"{dest_remote}{dest_path}"
        
        else:
            # Remote source
            source_remote = source_type
            
            # List remote files
            files = rclone_manager.list_files(source_remote, "")
            
            if not files:
                error(f"❌ No files found in remote '{source_remote}'")
                wait_for_enter(True)
                return
            
            # Create file choices
            file_choices = [{"name": f["Name"], "value": f["Name"]} for f in files if not f.get("IsDir", False)]
            
            if not file_choices:
                # If no files in root, prompt for path
                source_path = questionary.text(
                    f"No files found in root of '{source_remote}'. Enter specific path:",
                    style=custom_style
                ).ask()
                
                if not source_path:
                    return
            else:
                # Add custom path option
                file_choices.append({"name": "Enter custom path", "value": "custom"})
                file_choices.append({"name": "Cancel", "value": "cancel"})
                
                source_file = questionary.select(
                    f"Select file from '{source_remote}':",
                    choices=file_choices,
                    style=custom_style
                ).ask()
                
                if source_file == "cancel":
                    return
                
                if source_file == "custom":
                    source_path = questionary.text(
                        f"Enter path on '{source_remote}':",
                        style=custom_style
                    ).ask()
                    
                    if not source_path:
                        return
                else:
                    source_path = source_file
            
            # Prepare source
            if not source_remote.endswith(':'):
                source_remote = f"{source_remote}:"
            source = f"{source_remote}{source_path}"
            
            # Select destination type
            dest_choices = [
                {"name": "Local directory", "value": "local"},
                {"name": "Another remote", "value": "remote"},
                {"name": "Cancel", "value": "cancel"},
            ]
            
            dest_type = questionary.select(
                "Select destination type:",
                choices=dest_choices,
                style=custom_style
            ).ask()
            
            if dest_type == "cancel":
                return
            
            if dest_type == "local":
                # Local destination
                destination = questionary.text(
                    "Enter local destination path (absolute path):",
                    style=custom_style
                ).ask()
                
                if not destination:
                    return
                
                # If destination is a directory, append source filename
                if os.path.isdir(destination):
                    source_filename = os.path.basename(source_path)
                    destination = os.path.join(destination, source_filename)
                
                # Ensure destination directory exists
                os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            else:
                # Remote destination
                remaining_remotes = [r for r in remotes if r != source_type]
                dest_remote_choices = create_remote_choices(remaining_remotes)
                
                dest_remote = prompt_with_cancel(
                    dest_remote_choices,
                    "Select destination remote:"
                )
                
                if not dest_remote:
                    return
                
                dest_path = questionary.text(
                    "Enter destination path on remote (including filename):",
                    style=custom_style
                ).ask()
                
                if not dest_path:
                    # Use source filename if no path provided
                    dest_path = os.path.basename(source_path)
                
                # Prepare destination
                if not dest_remote.endswith(':'):
                    dest_remote = f"{dest_remote}:"
                destination = f"{dest_remote}{dest_path}"
        
        # Show summary and confirm
        info("\n📋 Copy Operation Summary:")
        if source_type == "local":
            info(f"  Source: {source_path}")
        else:
            info(f"  Source: {source}")
        info(f"  Destination: {destination}")
        
        confirm = questionary.confirm(
            "Proceed with the copy operation?",
            style=custom_style,
            default=True
        ).ask()
        
        if not confirm:
            return
        
        # Configure flags
        flags = ["--progress"]
        
        # Execute the copy
        if source_type == "local":
            # Convert the host path to container path for Rclone
            container_source_path = convert_host_path_to_container(source_path, 'rclone')
            info(f"\n📂 Copying from {source_path} to {destination}...")
            success_result, message = rclone_manager.execute_command(
                ["copyto", container_source_path, destination] + flags
            )
        else:
            info(f"\n📂 Copying from {source} to {destination}...")
            if dest_type == "local":
                # Convert the host path to container path for Rclone
                container_dest_path = convert_host_path_to_container(destination, 'rclone')
                success_result, message = rclone_manager.execute_command(
                    ["copyto", source, container_dest_path] + flags
                )
            else:
                success_result, message = rclone_manager.execute_command(
                    ["copyto", source, destination] + flags
                )
        
        if success_result:
            success("✅ Copy operation completed successfully")
            info(message)
        else:
            error(f"❌ Copy operation failed: {message}")
        
        wait_for_enter()
    
    execute_with_exception_handling(_copy_files, "Error copying files")


def prompt_file_operations() -> None:
    """Display Rclone file operations menu and handle user selection."""
    def _prompt_file_operations():
        # Check if Rclone container is running
        rclone_manager = RcloneManager()
        if not handle_container_check(rclone_manager):
            return
        
        # Get list of remotes
        remotes = ensure_remotes_available(rclone_manager)
        if not remotes:
            return
        
        choices = [
            {"name": "1. List Remote Files", "value": "1"},
            {"name": "2. Copy Files", "value": "2"},
            {"name": "3. Sync Directories", "value": "3"},
            {"name": "0. Back", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n📂 Rclone File Operations:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "0":
            return
        elif answer == "1":
            list_remote_files()
        elif answer == "2":
            copy_files()
        elif answer == "3":
            sync_directories()
    
    execute_with_exception_handling(_prompt_file_operations, "Error in file operations menu")


def list_remote_backups() -> None:
    """List backups on a remote storage."""
    def _list_remote_backups():
        rclone_manager = RcloneManager()
        config_manager = RcloneConfigManager()
        backup_integration = RcloneBackupIntegration()
        
        # Check if Rclone container is running
        if not handle_container_check(rclone_manager):
            return
        
        # Get list of remotes
        remotes = ensure_remotes_available(rclone_manager)
        if not remotes:
            return
        
        # Select remote using utility function
        selected_remote = select_remote(remotes, "Select remote to view backups:", config_manager)
        if not selected_remote:
            return
            
        # Optionally filter by website
        website_name = questionary.text(
            "Enter website name to filter backups (leave empty for all):",
            style=custom_style
        ).ask() or None
        
        # List backups
        files = backup_integration.list_remote_backups(selected_remote, website_name)
        
        if files:
            info(f"\n📋 Backups in '{selected_remote}' storage" + (f" for website '{website_name}'" if website_name else "") + ":")
            info("="*80)
            info(f"{'Name':40} {'Size':15} {'Type':15} {'Last Modified'}")
            info("-"*80)
            
            for file_info in files:
                file_type = "📁 Directory" if file_info.get("IsDir", False) else "📄 File"
                file_name = file_info.get("Name", "Unknown")
                file_size = file_info.get("Size", 0)
                size_str = format_size(file_size)
                mod_time = file_info.get("ModTime", "Unknown")
                
                # Truncate filename if too long
                if len(file_name) > 37:
                    display_name = file_name[:34] + "..."
                else:
                    display_name = file_name
                    
                info(f"{display_name:40} {size_str:15} {file_type:15} {mod_time}")
            
            info("="*80)
        else:
            info(f"No backups found" + (f" for website '{website_name}'" if website_name else "") + f" in '{selected_remote}'")
        
        wait_for_enter()
    
    execute_with_exception_handling(_list_remote_backups, "Error listing remote backups")


def upload_backup_to_cloud() -> None:
    """Upload a backup to a remote storage."""
    def _upload_backup_to_cloud():
        rclone_manager = RcloneManager()
        config_manager = RcloneConfigManager()
        backup_integration = RcloneBackupIntegration()
        
        # Check if Rclone container is running
        if not handle_container_check(rclone_manager):
            return
        
        # Get list of remotes
        remotes = ensure_remotes_available(rclone_manager)
        if not remotes:
            return
        
        # Select remote using utility function
        selected_remote = select_remote(remotes, "Select destination remote storage:", config_manager)
        if not selected_remote:
            return
        
        # Select website using utility function
        website_name = select_website("Select website to backup:")
        if not website_name:
            error("❌ Website name is required for backup organization")
            wait_for_enter(True)
            return
        
        # Select backup file using utility function
        backup_path = select_backup_file(website_name, "Select backup file to upload:")
        if not backup_path:
            return
        
        # Validate backup file
        if not validate_backup_path(backup_path):
            wait_for_enter(True)
            return
        
        # Show summary and confirm
        info("\n📤 Backup Summary:")
        info(f"  Source: {backup_path}")
        info(f"  Destination: {selected_remote}:backups/{website_name}/")
        
        confirm = questionary.confirm(
            "Proceed with the upload?",
            style=custom_style,
            default=True
        ).ask()
        
        if not confirm:
            return
        
        # Upload the backup using execute_rclone_operation utility
        info(f"\n☁️  Uploading backup to '{selected_remote}' storage...")
        
        def upload_operation():
            return backup_integration.backup_to_remote(selected_remote, website_name, backup_path)
        
        success_result = execute_rclone_operation(
            upload_operation,
            f"Backup successfully uploaded to {selected_remote}",
            f"Failed to upload backup to {selected_remote}"
        )
        
        wait_for_enter()
    
    execute_with_exception_handling(_upload_backup_to_cloud, "Error uploading backup")


def download_backup_from_cloud() -> None:
    """Download a backup from a remote storage."""
    def _download_backup_from_cloud():
        rclone_manager = RcloneManager()
        config_manager = RcloneConfigManager()
        backup_integration = RcloneBackupIntegration()
        
        # Check if Rclone container is running
        if not handle_container_check(rclone_manager):
            return
        
        # Get list of remotes
        remotes = ensure_remotes_available(rclone_manager)
        if not remotes:
            return
        
        # Select remote using utility function
        selected_remote = select_remote(remotes, "Select source remote storage:", config_manager)
        if not selected_remote:
            return
        
        # List available websites in the backups folder
        base_path = "backups"
        websites = []
        
        try:
            # List contents of the backups directory
            base_files = rclone_manager.list_files(selected_remote, base_path)
            
            # Find directories (websites)
            websites = [f["Name"] for f in base_files if f.get("IsDir", False)]
        except Exception as e:
            debug(f"Error listing website directories: {str(e)}")
        
        # Website name for folder filtering
        if websites:
            website_choices = [{"name": website, "value": website} for website in websites]
            website_choices.append({"name": "Enter manually", "value": "manual"})
            website_choices.append({"name": "Show all backups", "value": ""})
            
            website_option = questionary.select(
                "Select website to download backups from:",
                choices=website_choices,
                style=custom_style
            ).ask()
            
            if website_option == "manual":
                website_name = questionary.text(
                    "Enter website name:",
                    style=custom_style
                ).ask() or None
            else:
                website_name = website_option
        else:
            website_name = questionary.text(
                "Enter website name to filter backups (leave empty for all):",
                style=custom_style
            ).ask() or None
        
        # List available backups
        remote_path = "backups"
        if website_name:
            remote_path = f"{remote_path}/{website_name}"
        
        info(f"\n🔍 Searching for backups in {selected_remote}:{remote_path}...")
        files = rclone_manager.list_files(selected_remote, remote_path)
        
        if not files:
            error(f"❌ No backups found in '{selected_remote}:{remote_path}'")
            wait_for_enter()
            return
        
        # Build backup file choices using the utility function
        file_choices = process_backup_files(files, remote_path, rclone_manager, selected_remote)
        
        if not file_choices:
            error(f"❌ No valid backup files found in '{selected_remote}:{remote_path}'")
            wait_for_enter()
            return
        
        file_choices.append({"name": "Enter path manually", "value": "manual"})
        file_choices.append({"name": "Cancel", "value": "cancel"})
        
        selected_backup = questionary.select(
            "Select backup to download:",
            choices=file_choices,
            style=custom_style
        ).ask()
        
        if selected_backup == "cancel":
            return
        
        if selected_backup == "manual":
            remote_file_path = questionary.text(
                f"Enter full backup path on '{selected_remote}':",
                style=custom_style
            ).ask()
            
            if not remote_file_path:
                return
            
            selected_backup = remote_file_path
        elif selected_backup.startswith("dir:"):
            # User selected a directory, let them pick a file
            dir_path = selected_backup[4:]  # Remove 'dir:' prefix
            subdir_files = rclone_manager.list_files(selected_remote, dir_path)
            
            if not subdir_files:
                error(f"❌ No files found in directory '{dir_path}'")
                wait_for_enter()
                return
            
            # Filter out directories and create choices
            subdir_choices = []
            for subfile in [f for f in subdir_files if not f.get("IsDir", False)]:
                subfile_name = subfile.get("Name", "Unknown")
                subfile_size = subfile.get("Size", 0)
                subsize_str = format_size(subfile_size)
                subfile_mod_time = subfile.get("ModTime", "Unknown")
                
                subdir_choices.append({
                    "name": f"📄 {subfile_name} ({subsize_str}) - {subfile_mod_time}",
                    "value": f"{dir_path}/{subfile_name}"
                })
            
            if not subdir_choices:
                error(f"❌ No files found in directory '{dir_path}'")
                wait_for_enter()
                return
                
            subdir_choices.append({"name": "Cancel", "value": "cancel"})
            
            subdir_selection = questionary.select(
                f"Select file from '{os.path.basename(dir_path)}':",
                choices=subdir_choices,
                style=custom_style
            ).ask()
            
            if subdir_selection == "cancel":
                return
            
            selected_backup = subdir_selection
        elif selected_backup.startswith("more:"):
            # User selected "more files", show the complete list
            dir_path = selected_backup[5:]  # Remove 'more:' prefix
            subdir_files = rclone_manager.list_files(selected_remote, dir_path)
            
            if not subdir_files:
                error(f"❌ No files found in directory '{dir_path}'")
                wait_for_enter()
                return
            
            # Filter out directories and create choices
            subdir_choices = []
            for subfile in [f for f in subdir_files if not f.get("IsDir", False)]:
                subfile_name = subfile.get("Name", "Unknown")
                subfile_size = subfile.get("Size", 0)
                subsize_str = format_size(subfile_size)
                subfile_mod_time = subfile.get("ModTime", "Unknown")
                
                subdir_choices.append({
                    "name": f"📄 {subfile_name} ({subsize_str}) - {subfile_mod_time}",
                    "value": f"{dir_path}/{subfile_name}"
                })
            
            if not subdir_choices:
                error(f"❌ No files found in directory '{dir_path}'")
                wait_for_enter()
                return
                
            subdir_choices.append({"name": "Cancel", "value": "cancel"})
            
            subdir_selection = questionary.select(
                f"Select file from '{os.path.basename(dir_path)}':",
                choices=subdir_choices,
                style=custom_style
            ).ask()
            
            if subdir_selection == "cancel":
                return
            
            selected_backup = subdir_selection
        
        # Determine a good default local path
        default_local_path = ""
        filename = os.path.basename(selected_backup)
        
        # Extract website name from path if not set
        if not website_name and selected_backup.startswith("backups/"):
            parts = selected_backup.split("/")
            if len(parts) > 1:
                website_name = parts[1]
        
        if website_name:
            sites_dir = env.get("SITES_DIR")
            if sites_dir and os.path.exists(os.path.join(sites_dir, website_name)):
                site_backups_dir = os.path.join(sites_dir, website_name, "backups")
                os.makedirs(site_backups_dir, exist_ok=True)
                default_local_path = os.path.join(site_backups_dir, filename)
        
        # Local destination path
        local_path = questionary.text(
            "Enter local destination path (absolute path):",
            default=default_local_path,
            style=custom_style
        ).ask()
        
        if not local_path:
            return
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Show summary and confirm
        info("\n📥 Download Summary:")
        info(f"  Source: {selected_remote}:{selected_backup}")
        info(f"  Destination: {local_path}")
        
        confirm = questionary.confirm(
            "Proceed with the download?",
            style=custom_style,
            default=True
        ).ask()
        
        if not confirm:
            return
        
        # Download the backup using execute_rclone_operation utility
        info(f"\n☁️  Downloading backup from '{selected_remote}:{selected_backup}'...")
        
        def download_operation():
            return backup_integration.restore_from_remote(
                selected_remote, selected_backup, local_path, website_name
            )
        
        success_result = execute_rclone_operation(
            download_operation,
            f"Backup successfully downloaded from {selected_remote}",
            f"Failed to download backup from {selected_remote}"
        )
        
        wait_for_enter()
    
    execute_with_exception_handling(_download_backup_from_cloud, "Error downloading backup")


def schedule_cloud_backup() -> None:
    """Schedule regular cloud backups using the cron system."""
    def _schedule_cloud_backup():
        rclone_manager = RcloneManager()
        config_manager = RcloneConfigManager()
        backup_integration = RcloneBackupIntegration()
        
        # Check if Rclone container is running
        if not handle_container_check(rclone_manager):
            return
        
        # Get list of remotes
        remotes = ensure_remotes_available(rclone_manager)
        if not remotes:
            return
        
        # Check if cron module is available
        try:
            from src.features.cron.manager import CronManager
        except ImportError:
            error("❌ Cron module not available. Cannot schedule backups.")
            wait_for_enter()
            return
        
        # Select remote using utility function
        selected_remote = select_remote(remotes, "Select remote storage for scheduled backups:", config_manager)
        if not selected_remote:
            return
        
        # Select website using utility function
        website_name = select_website("Select website to schedule backups for:")
        if not website_name:
            error("❌ Website name is required for scheduled backups")
            wait_for_enter(True)
            return
        
        # Schedule options with friendly descriptions
        schedule_choices = [
            {"name": "Daily (at 2:00 AM)", "value": "0 2 * * *"},
            {"name": "Weekly (Sunday at 3:00 AM)", "value": "0 3 * * 0"}, 
            {"name": "Monthly (1st day at 4:00 AM)", "value": "0 4 1 * *"},
            {"name": "Custom", "value": "custom"},
            {"name": "Cancel", "value": "cancel"},
        ]
        
        selected_schedule = questionary.select(
            "Select backup schedule:",
            choices=schedule_choices,
            style=custom_style
        ).ask()
        
        if selected_schedule == "cancel":
            return
        
        if selected_schedule == "custom":
            info("\n📋 Cron Schedule Format Help:")
            info("  ┌─────────── minute (0 - 59)")
            info("  │ ┌───────── hour (0 - 23)")
            info("  │ │ ┌─────── day of the month (1 - 31)")
            info("  │ │ │ ┌───── month (1 - 12)")
            info("  │ │ │ │ ┌─── day of the week (0 - 6) (Sunday to Saturday)")
            info("  │ │ │ │ │")
            info("  * * * * *")
            info("\nExamples:")
            info("  0 2 * * *     # Every day at 2:00 AM")
            info("  0 3 * * 0     # Every Sunday at 3:00 AM")
            info("  0 4 1 * *     # First day of each month at 4:00 AM")
            info("  */10 * * * *  # Every 10 minutes")
            
            custom_schedule = questionary.text(
                "Enter cron schedule expression:",
                style=custom_style
            ).ask()
            
            if not custom_schedule:
                return
            
            selected_schedule = custom_schedule
        
        # Show summary and confirm
        info("\n🕒 Backup Schedule Summary:")
        info(f"  Website: {website_name}")
        info(f"  Remote Storage: {selected_remote}")
        info(f"  Schedule: {selected_schedule}")
        
        # Try to make the schedule more human-readable
        if selected_schedule == "0 2 * * *":
            info("  Runs: Daily at 2:00 AM")
        elif selected_schedule == "0 3 * * 0":
            info("  Runs: Every Sunday at 3:00 AM")
        elif selected_schedule == "0 4 1 * *":
            info("  Runs: First day of each month at 4:00 AM")
        
        confirm = questionary.confirm(
            "Proceed with scheduling this backup?",
            style=custom_style,
            default=True
        ).ask()
        
        if not confirm:
            return
        
        # Schedule the backup using execute_rclone_operation utility
        info(f"\n🕒 Scheduling backup of '{website_name}' to '{selected_remote}'...")
        
        def schedule_operation():
            return backup_integration.schedule_remote_backup(
                selected_remote, website_name, selected_schedule
            )
        
        success_result = execute_rclone_operation(
            schedule_operation,
            f"Backup of {website_name} to {selected_remote} scheduled successfully with schedule: {selected_schedule}",
            f"Failed to schedule backup"
        )
        
        wait_for_enter()
    
    execute_with_exception_handling(_schedule_cloud_backup, "Error scheduling backup")


def prompt_backup_operations() -> None:
    """Display Rclone backup operations menu and handle user selection."""
    def _prompt_backup_operations():
        # Check if Rclone container is running
        rclone_manager = RcloneManager()
        if not handle_container_check(rclone_manager):
            return
        
        # Get list of remotes
        remotes = ensure_remotes_available(rclone_manager)
        if not remotes:
            return
        
        choices = [
            {"name": "1. List Remote Backups", "value": "1"},
            {"name": "2. Upload Backup to Cloud", "value": "2"},
            {"name": "3. Download Backup from Cloud", "value": "3"},
            {"name": "4. Schedule Cloud Backup", "value": "4"},
            {"name": "0. Back", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n☁️  Cloud Backup Operations:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "0":
            return
        elif answer == "1":
            list_remote_backups()
        elif answer == "2":
            upload_backup_to_cloud()
        elif answer == "3":
            download_backup_from_cloud()
        elif answer == "4":
            schedule_cloud_backup()
    
    execute_with_exception_handling(_prompt_backup_operations, "Error in backup operations menu")


def restart_rclone_container() -> None:
    """Restart the Rclone container."""
    def _restart_rclone_container():
        rclone_manager = RcloneManager()
        if rclone_manager.is_container_running():
            info("Restarting Rclone container...")
            if rclone_manager.restart_container():
                success("✅ Rclone container restarted successfully")
            else:
                error("❌ Failed to restart Rclone container")
        else:
            info("Starting Rclone container...")
            if rclone_manager.start_container():
                success("✅ Rclone container started successfully")
            else:
                error("❌ Failed to start Rclone container")
                
        wait_for_enter()
    
    execute_with_exception_handling(_restart_rclone_container, "Error restarting container")


def prompt_rclone_menu() -> None:
    """Display Rclone management menu and handle user selection."""
    try:
        choices = [
            {"name": "1. Manage Remotes", "value": "1"},
            {"name": "2. File Operations", "value": "2"},
            {"name": "3. Cloud Backup", "value": "3"},
            {"name": "4. Restart Rclone Container", "value": "4"},
            {"name": "0. Back to Main Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n☁️  Rclone Management:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "0":
            return
        elif answer == "1":
            prompt_manage_remotes()
        elif answer == "2":
            prompt_file_operations()
        elif answer == "3":
            prompt_backup_operations()
        elif answer == "4":
            restart_rclone_container()
    except Exception as e:
        error(f"Error in Rclone menu: {e}")
        wait_for_enter(True)