"""
Rclone management menu prompt module.

This module provides the user interface for Rclone management functinons.
"""

import os
import datetime
import questionary
from questionary import Style, prompt
from typing import Dict, List, Optional, Tuple, Any

from src.common.logging import info, error, debug, success
from src.common.utils.environment import env
from src.features.rclone.manager import RcloneManager
from src.features.rclone.config.manager import RcloneConfigManager
from src.features.rclone.backup_integration import RcloneBackupIntegration

# Custom style for the menu
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:cyan bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:green bold'),
    ('selected', 'fg:green bold'),
    ('separator', 'fg:cyan'),
    ('instruction', 'fg:gray'),
    ('text', ''),
    ('disabled', 'fg:gray italic'),
])

def get_remote_type_display_name(remote_type: str) -> str:
    """Get a user-friendly display name for a remote type.
    
    Args:
        remote_type: The internal type name used by rclone
        
    Returns:
        str: A user-friendly display name
    """
    display_names = {
        "s3": "Amazon S3 / Wasabi / DO Spaces",
        "drive": "Google Drive",
        "dropbox": "Dropbox",
        "onedrive": "Microsoft OneDrive",
        "b2": "Backblaze B2",
        "box": "Box",
        "sftp": "SFTP",
        "ftp": "FTP",
        "webdav": "WebDAV",
        "azureblob": "Azure Blob Storage",
        "mega": "Mega.nz",
        "pcloud": "pCloud",
        "swift": "OpenStack Swift",
        "yandex": "Yandex Disk",
        "local": "Local Disk"
    }
    return display_names.get(remote_type, remote_type.capitalize())

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
            from src.common.utils.editor import choose_editor
            
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

def prompt_manage_remotes() -> None:
    """Display Rclone remotes management menu and handle user selection."""
    rclone_manager = RcloneManager()
    config_manager = RcloneConfigManager()
    
    try:
        # Check if Rclone container is running
        if not rclone_manager.is_container_running():
            info("Starting Rclone container...")
            if not rclone_manager.start_container():
                error("❌ Failed to start Rclone container. Please check your Docker configuration.")
                input("Press Enter to continue...")
                return
        
        # Get list of remotes
        remotes = rclone_manager.list_remotes()
        
        choices = [
            {"name": "1. List Remotes", "value": "1"},
            {"name": "2. Add Remote", "value": "2"},
            {"name": "3. Remove Remote", "value": "3"},
            {"name": "4. View Remote Configuration", "value": "4"},
            {"name": "0. Back", "value": "0"},
        ]
        
        while True:
            answer = questionary.select(
                "\n🛰️  Rclone Remotes Management:",
                choices=choices,
                style=custom_style
            ).ask()
            
            if answer == "0":
                break
            elif answer == "1":
                # List remotes
                remotes = rclone_manager.list_remotes()
                if remotes:
                    info("\n📋 Configured Remotes:")
                    for i, remote in enumerate(remotes, 1):
                        # Get remote type for more detailed display
                        remote_config = config_manager.get_remote_config(remote)
                        remote_type = remote_config.get("type", "unknown") if remote_config else "unknown"
                        display_type = get_remote_type_display_name(remote_type)
                        
                        info(f"{i}.i {remote} ({display_type})")
                else:
                    info("No remotes configured yet.")
                input("\nPress Enter to continue...")
            
            elif answer == "2":
                # Add remote
                remote_name = questionary.text(
                    "Enter name for the new remote:",
                    style=custom_style
                ).ask()
                
                if not remote_name:
                    continue
                
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
                    continue
                
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
                
                input("\nPress Enter to continue...")
            
            elif answer == "3":
                # Remove remote
                remotes = rclone_manager.list_remotes()
                if not remotes:
                    info("No remotes configured yet.")
                    input("\nPress Enter to continue...")
                    continue
                
                remote_choices = []
                for remote in remotes:
                    # Get remote type for more informative display
                    config = config_manager.get_remote_config(remote)
                    remote_type = config.get("type", "unknown") if config else "unknown"
                    display_type = get_remote_type_display_name(remote_type)
                    remote_choices.append({"name": f"{remote} ({display_type})", "value": remote})
                
                remote_choices.append({"name": "Cancel", "value": "cancel"})
                
                remote_to_remove = questionary.select(
                    "Select remote to remove:",
                    choices=remote_choices,
                    style=custom_style
                ).ask()
                
                if remote_to_remove != "cancel":
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
                        success_result = rclone_manager.remove_remote(remote_to_remove)
                        if success_result:
                            success(f"✅ Remote '{remote_to_remove}' removed successfully")
                        else:
                            error(f"❌ Failed to remove remote '{remote_to_remove}'")
                
                input("\nPress Enter to continue...")
            
            elif answer == "4":
                # View remote configuration
                remotes = rclone_manager.list_remotes()
                if not remotes:
                    info("No remotes configured yet.")
                    input("\nPress Enter to continue...")
                    continue
                
                remote_choices = []
                for remote in remotes:
                    # Get remote type for more informative display
                    config = config_manager.get_remote_config(remote)
                    remote_type = config.get("type", "unknown") if config else "unknown"
                    display_type = get_remote_type_display_name(remote_type)
                    remote_choices.append({"name": f"{remote} ({display_type})", "value": remote})
                
                remote_choices.append({"name": "Cancel", "value": "cancel"})
                
                selected_remote = questionary.select(
                    "Select remote to view:",
                    choices=remote_choices,
                    style=custom_style
                ).ask()
                
                if selected_remote != "cancel":
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
                
                input("\nPress Enter to continue...")
            
    
    except Exception as e:
        error(f"Error in remotes management menu: {e}")
        input("Press Enter to continue...")

def prompt_file_operations() -> None:
    """Display Rclone file operations menu and handle user selection."""
    rclone_manager = RcloneManager()
    
    try:
        # Check if Rclone container is running
        if not rclone_manager.is_container_running():
            info("Starting Rclone container...")
            if not rclone_manager.start_container():
                error("❌ Failed to start Rclone container. Please check your Docker configuration.")
                input("Press Enter to continue...")
                return
        
        # Get list of remotes
        remotes = rclone_manager.list_remotes()
        if not remotes:
            error("❌ No remotes configured. Please add a remote first.")
            input("Press Enter to continue...")
            return
        
        choices = [
            {"name": "1. List Files/Directories", "value": "1"},
            {"name": "2. Sync Directories", "value": "2"},
            {"name": "3. Copy Files", "value": "3"},
            {"name": "0. Back", "value": "0"},
        ]
        
        while True:
            answer = questionary.select(
                "\n📁 Rclone File Operations:",
                choices=choices,
                style=custom_style
            ).ask()
            
            if answer == "0":
                break
            
            elif answer == "1":
                # List files/directories
                remote_choices = [{"name": remote, "value": remote} for remote in remotes]
                remote_choices.append({"name": "Cancel", "value": "cancel"})
                
                selected_remote = questionary.select(
                    "Select remote:",
                    choices=remote_choices,
                    style=custom_style
                ).ask()
                
                if selected_remote == "cancel":
                    continue
                
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
                        size_str = f"{file_size/1024/1024:.2f} MB" if file_size > 1024*1024 else f"{file_size/1024:.2f} KB"
                        info(f"{i}. {file_type} {file_name} ({size_str})")
                else:
                    info(f"No files found in '{selected_remote}:{remote_path}'")
                
                input("\nPress Enter to continue...")
            
            elif answer == "2":
                # Sync directories
                remote_choices = [{"name": remote, "value": remote} for remote in remotes]
                remote_choices.append({"name": "Local directory", "value": "local"})
                remote_choices.append({"name": "Cancel", "value": "cancel"})
                
                source_type = questionary.select(
                    "Select source type:",
                    choices=remote_choices,
                    style=custom_style
                ).ask()
                
                if source_type == "cancel":
                    continue
                
                if source_type == "local":
                    # Local source, remote destination
                    source_path = questionary.text(
                        "Enter local source directory (absolute path):",
                        style=custom_style
                    ).ask()
                    
                    if not source_path:
                        continue
                    
                    # Validate source path exists
                    if not os.path.exists(source_path):
                        error(f"❌ Source path '{source_path}' does not exist")
                        input("Press Enter to continue...")
                        continue
                    
                    # Select remote destination
                    remaining_remotes = [r for r in remotes]
                    dest_choices = [{"name": remote, "value": remote} for remote in remaining_remotes]
                    dest_choices.append({"name": "Cancel", "value": "cancel"})
                    
                    dest_remote = questionary.select(
                        "Select destination remote:",
                        choices=dest_choices,
                        style=custom_style
                    ).ask()
                    
                    if dest_remote == "cancel":
                        continue
                    
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
                    
                    dest_type = questionary.select(
                        "Select destination type:",
                        choices=dest_choices,
                        style=custom_style
                    ).ask()
                    
                    if dest_type == "cancel":
                        continue
                    
                    if dest_type == "local":
                        # Local destination
                        destination = questionary.text(
                            "Enter local destination directory (absolute path):",
                            style=custom_style
                        ).ask()
                        
                        if not destination:
                            continue
                        
                        # Ensure destination directory exists
                        os.makedirs(os.path.dirname(destination), exist_ok=True)
                    
                    else:
                        # Remote destination
                        remaining_remotes = [r for r in remotes if r != source_type]
                        dest_remote_choices = [{"name": remote, "value": remote} for remote in remaining_remotes]
                        dest_remote_choices.append({"name": "Cancel", "value": "cancel"})
                        
                        dest_remote = questionary.select(
                            "Select destination remote:",
                            choices=dest_remote_choices,
                            style=custom_style
                        ).ask()
                        
                        if dest_remote == "cancel":
                            continue
                        
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
                info(f"\n🔄 Syncing from {source_path} to {destination}...")
                if source_type == "local":
                    success_result, message = rclone_manager.sync(source_path, destination, flags)
                else:
                    success_result, message = rclone_manager.sync(source, destination, flags)
                
                if success_result:
                    success("✅ Sync operation completed successfully")
                    info(message)
                else:
                    error(f"❌ Sync operation failed: {message}")
                
                input("\nPress Enter to continue...")
            
            elif answer == "3":
                # Copy files
                remote_choices = [{"name": remote, "value": remote} for remote in remotes]
                remote_choices.append({"name": "Local file", "value": "local"})
                remote_choices.append({"name": "Cancel", "value": "cancel"})
                
                source_type = questionary.select(
                    "Select source type:",
                    choices=remote_choices,
                    style=custom_style
                ).ask()
                
                if source_type == "cancel":
                    continue
                
                if source_type == "local":
                    # Local source, remote destination
                    source_path = questionary.text(
                        "Enter local source file path (absolute path):",
                        style=custom_style
                    ).ask()
                    
                    if not source_path:
                        continue
                    
                    # Validate source file exists
                    if not os.path.exists(source_path):
                        error(f"❌ Source file '{source_path}' does not exist")
                        input("Press Enter to continue...")
                        continue
                    
                    # Select remote destination
                    dest_choices = [{"name": remote, "value": remote} for remote in remotes]
                    dest_choices.append({"name": "Cancel", "value": "cancel"})
                    
                    dest_remote = questionary.select(
                        "Select destination remote:",
                        choices=dest_choices,
                        style=custom_style
                    ).ask()
                    
                    if dest_remote == "cancel":
                        continue
                    
                    dest_path = questionary.text(
                        "Enter destination path on remote (including filename):",
                        style=custom_style
                    ).ask() or os.path.basename(source_path)
                    
                    # Prepare destination
                    if not dest_remote.endswith(':'):
                        dest_remote = f"{dest_remote}:"
                    destination = f"{dest_remote}{dest_path}"
                    
                    # Convert source to container path
                    container_source = source_path
                    
                else:
                    # Remote source
                    source_remote = source_type
                    
                    # List files on remote to select
                    remote_path = questionary.text(
                        f"Enter directory path on '{source_remote}' to list files:",
                        style=custom_style
                    ).ask() or ""
                    
                    files = rclone_manager.list_files(source_remote, remote_path)
                    
                    if not files:
                        error(f"❌ No files found in '{source_remote}:{remote_path}'")
                        input("Press Enter to continue...")
                        continue
                    
                    # Filter out directories
                    files = [f for f in files if not f.get("IsDir", False)]
                    
                    if not files:
                        error(f"❌ No files (non-directories) found in '{source_remote}:{remote_path}'")
                        input("Press Enter to continue...")
                        continue
                    
                    file_choices = [{"name": f["Name"], "value": f["Name"]} for f in files]
                    file_choices.append({"name": "Enter path manually", "value": "manual"})
                    file_choices.append({"name": "Cancel", "value": "cancel"})
                    
                    selected_file = questionary.select(
                        "Select file to copy:",
                        choices=file_choices,
                        style=custom_style
                    ).ask()
                    
                    if selected_file == "cancel":
                        continue
                    
                    if selected_file == "manual":
                        source_file_path = questionary.text(
                            f"Enter full file path on '{source_remote}':",
                            style=custom_style
                        ).ask()
                        
                        if not source_file_path:
                            continue
                    else:
                        source_file_path = f"{remote_path}/{selected_file}" if remote_path else selected_file
                    
                    # Prepare source
                    if not source_remote.endswith(':'):
                        source_remote = f"{source_remote}:"
                    source = f"{source_remote}{source_file_path}"
                    
                    # Select destination type
                    dest_choices = [
                        {"name": "Local file", "value": "local"},
                        {"name": "Another remote", "value": "remote"},
                        {"name": "Cancel", "value": "cancel"},
                    ]
                    
                    dest_type = questionary.select(
                        "Select destination type:",
                        choices=dest_choices,
                        style=custom_style
                    ).ask()
                    
                    if dest_type == "cancel":
                        continue
                    
                    if dest_type == "local":
                        # Local destination
                        local_file_name = os.path.basename(source_file_path)
                        destination = questionary.text(
                            "Enter local destination path (absolute path, including filename):",
                            default=local_file_name,
                            style=custom_style
                        ).ask()
                        
                        if not destination:
                            continue
                        
                        # Ensure destination directory exists
                        os.makedirs(os.path.dirname(destination), exist_ok=True)
                    
                    else:
                        # Remote destination
                        remaining_remotes = [r for r in remotes if r != source_type]
                        dest_remote_choices = [{"name": remote, "value": remote} for remote in remaining_remotes]
                        dest_remote_choices.append({"name": "Cancel", "value": "cancel"})
                        
                        dest_remote = questionary.select(
                            "Select destination remote:",
                            choices=dest_remote_choices,
                            style=custom_style
                        ).ask()
                        
                        if dest_remote == "cancel":
                            continue
                        
                        remote_file_name = os.path.basename(source_file_path)
                        dest_path = questionary.text(
                            "Enter destination path on remote (including filename):",
                            default=remote_file_name,
                            style=custom_style
                        ).ask() or remote_file_name
                        
                        # Prepare destination
                        if not dest_remote.endswith(':'):
                            dest_remote = f"{dest_remote}:"
                        destination = f"{dest_remote}{dest_path}"
                
                # Configure copy flags
                flags = ["--progress"]
                
                if questionary.confirm(
                    "Add --dry-run flag to simulate the operation without actually transferring files?",
                    style=custom_style
                ).ask():
                    flags.append("--dry-run")
                
                # Perform copy operation
                info(f"\n📋 Copying {'from local file' if source_type == 'local' else 'from remote'} to {'local file' if dest_type == 'local' else 'remote'}...")
                
                if source_type == "local":
                    command = ["copy", source_path, destination] + flags
                else:
                    command = ["copy", source, destination] + flags
                
                success_result, message = rclone_manager.execute_command(command)
                
                if success_result:
                    success("✅ Copy operation completed successfully")
                else:
                    error(f"❌ Copy operation failed: {message}")
                
                input("\nPress Enter to continue...")
    
    except Exception as e:
        error(f"Error in file operations menu: {e}")
        input("Press Enter to continue...")

def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/1024/1024:.2f} MB"
    else:
        return f"{size_bytes/1024/1024/1024:.2f} GB"

def prompt_backup_operations() -> None:
    """Display Rclone backup operations menu and handle user selection."""
    rclone_manager = RcloneManager()
    config_manager = RcloneConfigManager()
    backup_integration = RcloneBackupIntegration()
    
    try:
        # Check if Rclone container is running
        if not rclone_manager.is_container_running():
            info("Starting Rclone container...")
            if not rclone_manager.start_container():
                error("❌ Failed to start Rclone container. Please check your Docker configuration.")
                input("Press Enter to continue...")
                return
        
        # Get list of remotes
        remotes = rclone_manager.list_remotes()
        if not remotes:
            error("❌ No remotes configured. Please add a remote first.")
            input("Press Enter to continue...")
            return
        
        choices = [
            {"name": "1. List Remote Backups", "value": "1"},
            {"name": "2. Upload Backup to Cloud", "value": "2"},
            {"name": "3. Download Backup from Cloud", "value": "3"},
            {"name": "4. Schedule Cloud Backup", "value": "4"},
            {"name": "0. Back", "value": "0"},
        ]
        
        while True:
            answer = questionary.select(
                "\n☁️  Cloud Backup Operations:",
                choices=choices,
                style=custom_style
            ).ask()
            
            if answer == "0":
                break
            
            elif answer == "1":
                # List remote backups
                remote_choices = []
                for remote in remotes:
                    # Get remote type for more informative display
                    config = config_manager.get_remote_config(remote)
                    remote_type = config.get("type", "unknown") if config else "unknown"
                    display_type = get_remote_type_display_name(remote_type)
                    remote_choices.append({"name": f"{remote} ({display_type})", "value": remote})
                
                remote_choices.append({"name": "Cancel", "value": "cancel"})
                
                selected_remote = questionary.select(
                    "Select remote storage:",
                    choices=remote_choices,
                    style=custom_style
                ).ask()
                
                if selected_remote == "cancel":
                    continue
                
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
                
                input("\nPress Enter to continue...")
            
            elif answer == "2":
                # Upload backup to cloud
                remote_choices = []
                for remote in remotes:
                    # Get remote type for more informative display
                    config = config_manager.get_remote_config(remote)
                    remote_type = config.get("type", "unknown") if config else "unknown"
                    display_type = get_remote_type_display_name(remote_type)
                    remote_choices.append({"name": f"{remote} ({display_type})", "value": remote})
                
                remote_choices.append({"name": "Cancel", "value": "cancel"})
                
                selected_remote = questionary.select(
                    "Select destination remote storage:",
                    choices=remote_choices,
                    style=custom_style
                ).ask()
                
                if selected_remote == "cancel":
                    continue
                
                # Website name
                # Check if SITES_DIR exists and has subdirectories
                sites_dir = env.get("SITES_DIR")
                available_domains = []
                
                if sites_dir and os.path.exists(sites_dir):
                    available_domains = [d for d in os.listdir(sites_dir) 
                                        if os.path.isdir(os.path.join(sites_dir, d))]
                
                if available_domains:
                    # Create choices including a custom option
                    domain_choices = [{"name": domain, "value": domain} for domain in available_domains]
                    domain_choices.append({"name": "Enter custom domain name", "value": "custom"})
                    
                    domain_selection = questionary.select(
                        "Select website to backup:",
                        choices=domain_choices,
                        style=custom_style
                    ).ask()
                    
                    if domain_selection == "custom":
                        website_name = questionary.text(
                            "Enter website name (used for remote folder structure):",
                            style=custom_style
                        ).ask()
                    else:
                        website_name = domain_selection
                else:
                    # No domains found, ask for manual entry
                    website_name = questionary.text(
                        "Enter website name (used for remote folder structure):",
                        style=custom_style
                    ).ask()
                
                if not website_name:
                    error("❌ Website name is required for backup organization")
                    input("Press Enter to continue...")
                    continue
                
                # Default backup location based on website name
                default_path = ""
                if sites_dir and os.path.exists(os.path.join(sites_dir, website_name)):
                    site_backups_dir = os.path.join(sites_dir, website_name, "backups")
                    if os.path.exists(site_backups_dir):
                        # List backup files in the backups directory
                        backup_files = [f for f in os.listdir(site_backups_dir) 
                                      if os.path.isfile(os.path.join(site_backups_dir, f)) and 
                                      (f.endswith('.zip') or f.endswith('.tar.gz') or f.endswith('.sql'))]
                        
                        if backup_files:
                            # Sort by modification time, newest first
                            backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(site_backups_dir, x)), 
                                            reverse=True)
                            
                            # Create list of files with dates
                            backup_choices = []
                            for f in backup_files:
                                mtime = os.path.getmtime(os.path.join(site_backups_dir, f))
                                date_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                                size = os.path.getsize(os.path.join(site_backups_dir, f))
                                size_str = format_size(size)
                                backup_choices.append({
                                    "name": f"{f} ({size_str}, {date_str})",
                                    "value": os.path.join(site_backups_dir, f)
                                })
                            
                            # Add manual option
                            backup_choices.append({"name": "Enter path manually", "value": "manual"})
                            
                            backup_selection = questionary.select(
                                "Select backup file to upload:",
                                choices=backup_choices,
                                style=custom_style
                            ).ask()
                            
                            if backup_selection == "manual":
                                backup_path = questionary.text(
                                    "Enter local backup file path (absolute path):",
                                    style=custom_style
                                ).ask()
                            else:
                                backup_path = backup_selection
                        else:
                            default_path = site_backups_dir
                            backup_path = questionary.text(
                                "Enter local backup file path (absolute path):",
                                default=default_path,
                                style=custom_style
                            ).ask()
                    else:
                        backup_path = questionary.text(
                            "Enter local backup file path (absolute path):",
                            style=custom_style
                        ).ask()
                else:
                    backup_path = questionary.text(
                        "Enter local backup file path (absolute path):",
                        style=custom_style
                    ).ask()
                
                if not backup_path:
                    continue
                
                # Validate backup file exists
                if not os.path.exists(backup_path):
                    error(f"❌ Backup file '{backup_path}' does not exist")
                    input("Press Enter to continue...")
                    continue
                
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
                    continue
                
                # Upload the backup
                info(f"\n☁️  Uploading backup to '{selected_remote}' storage...")
                success_result, message = backup_integration.backup_to_remote(
                    selected_remote, website_name, backup_path
                )
                
                if success_result:
                    success(f"✅ {message}")
                else:
                    error(f"❌ {message}")
                
                input("\nPress Enter to continue...")
            
            elif answer == "3":
                # Download backup from cloud
                remote_choices = []
                for remote in remotes:
                    # Get remote type for more informative display
                    config = config_manager.get_remote_config(remote)
                    remote_type = config.get("type", "unknown") if config else "unknown"
                    display_type = get_remote_type_display_name(remote_type)
                    remote_choices.append({"name": f"{remote} ({display_type})", "value": remote})
                
                remote_choices.append({"name": "Cancel", "value": "cancel"})
                
                selected_remote = questionary.select(
                    "Select source remote storage:",
                    choices=remote_choices,
                    style=custom_style
                ).ask()
                
                if selected_remote == "cancel":
                    continue
                
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
                    input("\nPress Enter to continue...")
                    continue
                
                # Filter out directories unless they contain backups
                file_choices = []
                
                # First add files directly in the directory
                direct_files = [f for f in files if not f.get("IsDir", False)]
                for file_info in direct_files:
                    file_name = file_info.get("Name", "Unknown")
                    file_size = file_info.get("Size", 0)
                    size_str = format_size(file_size)
                    mod_time = file_info.get("ModTime", "Unknown")
                    
                    file_choices.append({
                        "name": f"📄 {file_name} ({size_str}) - {mod_time}",
                        "value": f"{remote_path}/{file_name}"
                    })
                
                # Then check subdirectories
                for file_info in files:
                    if file_info.get("IsDir", False):
                        # For directories, check if they contain backup files
                        subdir_path = f"{remote_path}/{file_info['Name']}"
                        subdir_files = rclone_manager.list_files(selected_remote, subdir_path)
                        
                        if subdir_files:
                            # Add directory as a choice
                            file_choices.append({
                                "name": f"📁 {file_info['Name']}/ (directory with {len(subdir_files)} items)",
                                "value": "dir:" + subdir_path
                            })
                            
                            # Add direct files from the subdirectory
                            non_dir_files = [f for f in subdir_files if not f.get("IsDir", False)]
                            for subfile in non_dir_files[:3]:  # Show only the first 3 files
                                subfile_name = subfile.get("Name", "Unknown")
                                subfile_size = subfile.get("Size", 0)
                                subsize_str = format_size(subfile_size)
                                subfile_mod_time = subfile.get("ModTime", "Unknown")
                                
                                file_choices.append({
                                    "name": f"  └─ 📄 {subfile_name} ({subsize_str}) - {subfile_mod_time}",
                                    "value": f"{subdir_path}/{subfile_name}"
                                })
                            
                            # If there are more files, show a count
                            if len(non_dir_files) > 3:
                                file_choices.append({
                                    "name": f"  └─ ... {len(non_dir_files) - 3} more files",
                                    "value": "more:" + subdir_path
                                })
                
                if not file_choices:
                    error(f"❌ No valid backup files found in '{selected_remote}:{remote_path}'")
                    input("\nPress Enter to continue...")
                    continue
                
                file_choices.append({"name": "Enter path manually", "value": "manual"})
                file_choices.append({"name": "Cancel", "value": "cancel"})
                
                selected_backup = questionary.select(
                    "Select backup to download:",
                    choices=file_choices,
                    style=custom_style
                ).ask()
                
                if selected_backup == "cancel":
                    continue
                
                if selected_backup == "manual":
                    remote_file_path = questionary.text(
                        f"Enter full backup path on '{selected_remote}':",
                        style=custom_style
                    ).ask()
                    
                    if not remote_file_path:
                        continue
                    
                    selected_backup = remote_file_path
                elif selected_backup.startswith("dir:"):
                    # User selected a directory, let them pick a file
                    dir_path = selected_backup[4:]  # Remove 'dir:' prefix
                    subdir_files = rclone_manager.list_files(selected_remote, dir_path)
                    
                    if not subdir_files:
                        error(f"❌ No files found in directory '{dir_path}'")
                        input("\nPress Enter to continue...")
                        continue
                    
                    # Filter out directories
                    subdir_files = [f for f in subdir_files if not f.get("IsDir", False)]
                    
                    if not subdir_files:
                        error(f"❌ No files found in directory '{dir_path}'")
                        input("\nPress Enter to continue...")
                        continue
                    
                    # Create choices for files in this directory
                    subdir_choices = []
                    for subfile in subdir_files:
                        subfile_name = subfile.get("Name", "Unknown")
                        subfile_size = subfile.get("Size", 0)
                        subsize_str = format_size(subfile_size)
                        subfile_mod_time = subfile.get("ModTime", "Unknown")
                        
                        subdir_choices.append({
                            "name": f"📄 {subfile_name} ({subsize_str}) - {subfile_mod_time}",
                            "value": f"{dir_path}/{subfile_name}"
                        })
                    
                    subdir_choices.append({"name": "Cancel", "value": "cancel"})
                    
                    subdir_selection = questionary.select(
                        f"Select file from '{os.path.basename(dir_path)}':",
                        choices=subdir_choices,
                        style=custom_style
                    ).ask()
                    
                    if subdir_selection == "cancel":
                        continue
                    
                    selected_backup = subdir_selection
                elif selected_backup.startswith("more:"):
                    # User selected "more files", show the complete list
                    dir_path = selected_backup[5:]  # Remove 'more:' prefix
                    subdir_files = rclone_manager.list_files(selected_remote, dir_path)
                    
                    if not subdir_files:
                        error(f"❌ No files found in directory '{dir_path}'")
                        input("\nPress Enter to continue...")
                        continue
                    
                    # Filter out directories
                    subdir_files = [f for f in subdir_files if not f.get("IsDir", False)]
                    
                    if not subdir_files:
                        error(f"❌ No files found in directory '{dir_path}'")
                        input("\nPress Enter to continue...")
                        continue
                    
                    # Create choices for files in this directory
                    subdir_choices = []
                    for subfile in subdir_files:
                        subfile_name = subfile.get("Name", "Unknown")
                        subfile_size = subfile.get("Size", 0)
                        subsize_str = format_size(subfile_size)
                        subfile_mod_time = subfile.get("ModTime", "Unknown")
                        
                        subdir_choices.append({
                            "name": f"📄 {subfile_name} ({subsize_str}) - {subfile_mod_time}",
                            "value": f"{dir_path}/{subfile_name}"
                        })
                    
                    subdir_choices.append({"name": "Cancel", "value": "cancel"})
                    
                    subdir_selection = questionary.select(
                        f"Select file from '{os.path.basename(dir_path)}':",
                        choices=subdir_choices,
                        style=custom_style
                    ).ask()
                    
                    if subdir_selection == "cancel":
                        continue
                    
                    selected_backup = subdir_selection
                
                # Determine a good default local path
                default_local_path = ""
                filename = os.path.basename(selected_backup)
                
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
                    continue
                
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
                    continue
                
                # Download the backup
                info(f"\n☁️  Downloading backup from '{selected_remote}:{selected_backup}'...")
                success_result, message = backup_integration.restore_from_remote(
                    selected_remote, selected_backup, local_path, website_name
                )
                
                if success_result:
                    success(f"✅ {message}")
                else:
                    error(f"❌ {message}")
                
                input("\nPress Enter to continue...")
            
            elif answer == "4":
                # Schedule cloud backup
                try:
                    # Check if cron module is available
                    from src.features.cron.manager import CronManager
                    
                    # Remote selection
                    remote_choices = []
                    for remote in remotes:
                        # Get remote type for more informative display
                        config = config_manager.get_remote_config(remote)
                        remote_type = config.get("type", "unknown") if config else "unknown"
                        display_type = get_remote_type_display_name(remote_type)
                        remote_choices.append({"name": f"{remote} ({display_type})", "value": remote})
                    
                    remote_choices.append({"name": "Cancel", "value": "cancel"})
                    
                    selected_remote = questionary.select(
                        "Select remote storage for scheduled backups:",
                        choices=remote_choices,
                        style=custom_style
                    ).ask()
                    
                    if selected_remote == "cancel":
                        continue
                    
                    # Check if SITES_DIR exists and has subdirectories for website selection
                    sites_dir = env.get("SITES_DIR")
                    available_domains = []
                    
                    if sites_dir and os.path.exists(sites_dir):
                        available_domains = [d for d in os.listdir(sites_dir) 
                                           if os.path.isdir(os.path.join(sites_dir, d))]
                    
                    if available_domains:
                        # Create choices including a custom option
                        domain_choices = [{"name": domain, "value": domain} for domain in available_domains]
                        domain_choices.append({"name": "Enter custom domain name", "value": "custom"})
                        
                        domain_selection = questionary.select(
                            "Select website to schedule backups for:",
                            choices=domain_choices,
                            style=custom_style
                        ).ask()
                        
                        if domain_selection == "custom":
                            website_name = questionary.text(
                                "Enter website name:",
                                style=custom_style
                            ).ask()
                        else:
                            website_name = domain_selection
                    else:
                        # No domains found, ask for manual entry
                        website_name = questionary.text(
                            "Enter website name to schedule backups for:",
                            style=custom_style
                        ).ask()
                    
                    if not website_name:
                        error("❌ Website name is required for scheduled backups")
                        input("Press Enter to continue...")
                        continue
                    
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
                        continue
                    
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
                            continue
                        
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
                        continue
                    
                    # Schedule the backup
                    info(f"\n🕒 Scheduling backup of '{website_name}' to '{selected_remote}'...")
                    success_result, message = backup_integration.schedule_remote_backup(
                        selected_remote, website_name, selected_schedule
                    )
                    
                    if success_result:
                        success(f"✅ {message}")
                    else:
                        error(f"❌ {message}")
                    
                except ImportError:
                    error("❌ Cron module not available. Cannot schedule backups.")
                
                input("\nPress Enter to continue...")
    
    except Exception as e:
        error(f"Error in backup operations menu: {e}")
        input("Press Enter to continue...")

def prompt_rclone_menu() -> None:
    """Display Rclone management menu and handle user selection."""
    try:
        # Display the main Rclone management menu
        choices = [
            {"name": "1. Manage Remotes", "value": "1"},
            {"name": "2. File Operations", "value": "2"},
            {"name": "3. Cloud Backup", "value": "3"},
            {"name": "4. Restart Rclone Container", "value": "4"},
            {"name": "0. Back to Main Menu", "value": "0"},
        ]
        
        while True:
            answer = questionary.select(
                "\n☁️  Rclone Management:",
                choices=choices,
                style=custom_style
            ).ask()
            
            if answer == "0":
                break
            elif answer == "1":
                prompt_manage_remotes()
            elif answer == "2":
                prompt_file_operations()
            elif answer == "3":
                prompt_backup_operations()
            elif answer == "4":
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
                
                input("\nPress Enter to continue...")
    except Exception as e:
        error(f"Error in Rclone menu: {e}")
        input("Press Enter to continue...")