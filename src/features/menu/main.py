"""
Main menu for the WP Docker application.

This module provides the main menu system for the application,
allowing users to navigate between different features.
"""

import os
import sys
from typing import List, Dict, Any, Optional, Callable

from rich.console import Console
from rich.text import Text
import questionary
from questionary import Style

from src.common.logging import info, error, debug, success

# Console for rich output
console = Console()

# Custom style for the menu
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:cyan bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:green bold'),
    ('selected', 'fg:green bold'),
    ('separator', 'fg:cyan'),
    ('instruction', 'fg:bright_black'),
    ('text', ''),
    ('disabled', 'fg:bright_black italic'),
])


class MenuItem:
    """
    Represents a menu item with an ID, label, and action.
    
    Attributes:
        id: Unique identifier for the menu item
        label: Display text for the menu item
        action: Function to call when this item is selected
    """
    
    def __init__(self, id: str, label: str, action: Optional[Callable[[], None]]) -> None:
        """
        Initialize a menu item.
        
        Args:
            id: Unique identifier for the menu item
            label: Display text for the menu item
            action: Function to call when this item is selected
        """
        self.id = id
        self.label = label
        self.action = action


class Menu:
    """
    Represents a menu with a title and list of menu items.
    
    Attributes:
        title: Title of the menu
        items: List of menu items
        back_id: ID of the item that returns to the previous menu
    """
    
    def __init__(self, title: str, items: List[MenuItem], back_id: str) -> None:
        """
        Initialize a menu.
        
        Args:
            title: Title of the menu
            items: List of menu items
            back_id: ID of the item that returns to the previous menu
        """
        self.title = title
        self.items = items
        self.back_id = back_id
    
    def display(self) -> None:
        """Display the menu and handle user selection."""
        choices = [{"name": f"{item.id}. {item.label}", "value": item.id} for item in self.items]
        
        answer = questionary.select(
            self.title,
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == self.back_id:
            return
        
        for item in self.items:
            if item.id == answer and item.action:
                item.action()
                break


class MainMenu:
    """Main menu system for the application."""
    
    def __init__(self):
        """Initialize the main menu."""
        self.exit_requested = False
    
    def run(self) -> None:
        """Run the main menu loop."""
        while not self.exit_requested:
            self._show_main_menu()
    
    def _show_main_menu(self) -> None:
        """Show the main menu and handle selection."""
        # Display banner
        self._display_banner()
        
        # Create menu using Menu class
        menu = Menu(
            title="\n📋 Select a function:",
            items=[
                MenuItem("1", "Website Management", self._handle_website_menu),
                MenuItem("2", "SSL Certificates", self._handle_ssl_menu),
                MenuItem("3", "System Tools", self._handle_system_menu),
                MenuItem("4", "RClone Management", self._handle_cloud_menu),
                MenuItem("5", "WordPress Tools", self._handle_wordpress_menu),
                MenuItem("6", "Backup Management", self._handle_backup_menu),
                MenuItem("7", "WP Cache Setup", self._handle_wp_cache_menu),
                MenuItem("8", "PHP Management", self._handle_php_menu),
                MenuItem("9", "MySQL Management", self._handle_mysql_menu),
                MenuItem("10", "Check & Update WP Docker", self._handle_update_menu),
                MenuItem("0", "Exit", self._handle_exit)
            ],
            back_id="0"
        )
        
        # Display the menu
        menu.display()
    
    def _display_banner(self) -> None:
        """Display application banner."""
        # Clear screen
        os.system('clear' if os.name != 'nt' else 'cls')
        
        # Display ASCII banner
        header = Text("""

        ██╗    ██╗██████╗     ██████╗  ██████╗  ██████╗██╗  ██╗███████╗██████╗ 
        ██║    ██║██╔══██╗    ██╔══██╗██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
        ██║ █╗ ██║██████╔╝    ██████╔╝██║   ██║██║     █████╔╝ █████╗  ██████╔╝
        ██║███╗██║██╔═══╝     ██╔═══╝ ██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
        ╚███╔███╔╝██║         ██║     ╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║
         ╚══╝╚══╝ ╚═╝         ╚═╝      ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
        ═══════════════════════════════════════════════════════════════════════════════
        """, style="cyan")
        console.print(header)
    
    def _handle_exit(self) -> None:
        """Handle exit menu option."""
        self.exit_requested = True
        success("Exiting WP Docker. Goodbye!")
    
    # Module-specific menu handlers
    def _handle_website_menu(self) -> None:
        """Handle website management menu."""
        try:
            menu = Menu(
                title="\n🌐 Website Management:",
                items=[
                    MenuItem("1", "Create Website", self._not_implemented),
                    MenuItem("2", "Delete Website", self._not_implemented),
                    MenuItem("3", "List Websites", self._handle_list_websites),
                    MenuItem("4", "Restart Website", self._not_implemented),
                    MenuItem("5", "View Website Logs", self._not_implemented),
                    MenuItem("6", "View Website Info", self._not_implemented),
                    MenuItem("7", "Migrate Data to WP Docker", self._not_implemented),
                    MenuItem("0", "Back to Main Menu", None)
                ],
                back_id="0"
            )
            menu.display()
        except Exception as e:
            error(f"Error in website menu: {e}")
            input("Press Enter to continue...")
    
    def _handle_ssl_menu(self) -> None:
        """Handle SSL certificates menu."""
        try:
            menu = Menu(
                title="\n🔒 SSL Certificate Management:",
                items=[
                    MenuItem("1", "Create Self-Signed Certificate", self._not_implemented),
                    MenuItem("2", "Create Let's Encrypt Certificate", self._not_implemented),
                    MenuItem("3", "Install Custom Certificate", self._not_implemented),
                    MenuItem("4", "Check Certificate Info", self._not_implemented),
                    MenuItem("5", "Edit Current Certificate", self._not_implemented),
                    MenuItem("0", "Back to Main Menu", None)
                ],
                back_id="0"
            )
            menu.display()
        except Exception as e:
            error(f"Error in SSL menu: {e}")
            input("Press Enter to continue...")
    
    def _handle_system_menu(self) -> None:
        """Handle system tools menu."""
        try:
            menu = Menu(
                title="\n⚙️ System Tools:",
                items=[
                    MenuItem("1", "Rebuild Core Containers", self._not_implemented),
                    MenuItem("2", "Update WP Docker Version", self._not_implemented),
                    MenuItem("3", "View System Information", self._not_implemented),
                    MenuItem("4", "Change Language", self._not_implemented),
                    MenuItem("5", "Change Version Channel", self._not_implemented),
                    MenuItem("6", "Clean Docker", self._not_implemented),
                    MenuItem("7", "Manage Scheduled Tasks", self._handle_cron_menu),
                    MenuItem("0", "Back to Main Menu", None)
                ],
                back_id="0"
            )
            menu.display()
        except Exception as e:
            error(f"Error in system menu: {e}")
            input("Press Enter to continue...")
    
    def _handle_cron_menu(self) -> None:
        """Handle cron job management menu."""
        try:
            menu = Menu(
                title="\n⏱️ Scheduled Task Management:",
                items=[
                    MenuItem("1", "List Tasks", self._not_implemented),
                    MenuItem("2", "Enable/Disable Task", self._not_implemented),
                    MenuItem("3", "Delete Task", self._not_implemented),
                    MenuItem("4", "Run Task Now", self._not_implemented),
                    MenuItem("0", "Back to System Menu", None)
                ],
                back_id="0"
            )
            menu.display()
        except Exception as e:
            error(f"Error in cron menu: {e}")
            input("Press Enter to continue...")
    
    def _handle_cloud_menu(self) -> None:
        """Handle cloud storage menu."""
        try:
            from src.features.rclone.prompts.rclone_prompt import prompt_rclone_menu
            prompt_rclone_menu()
        except ImportError:
            menu = Menu(
                title="\n📦 RClone Management:",
                items=[
                    MenuItem("1", "Manage RClone", self._not_implemented),
                    MenuItem("0", "Back to Main Menu", None)
                ],
                back_id="0"
            )
            menu.display()
    
    def _handle_backup_menu(self) -> None:
        """Handle backup and restore menu."""
        try:
            from src.features.backup.prompts.prompt_backup_website import prompt_backup_website
            
            menu = Menu(
                title="\n💾 Backup Management:",
                items=[
                    MenuItem("1", "Create Website Backup", lambda: prompt_backup_website()),
                    MenuItem("2", "Restore Backup", self._not_implemented),
                    MenuItem("3", "List Backups", self._not_implemented),
                    MenuItem("4", "Delete Backup", self._not_implemented),
                    MenuItem("5", "Schedule Automatic Backup", self._not_implemented),
                    MenuItem("6", "Cloud Backup with RClone", self._handle_cloud_backup),
                    MenuItem("0", "Back to Main Menu", None)
                ],
                back_id="0"
            )
            menu.display()
        except ImportError:
            error("Backup module not fully implemented yet")
            input("Press Enter to continue...")
    
    def _handle_cloud_backup(self) -> None:
        """Handle cloud backup menu."""
        try:
            from src.features.backup.prompts.prompt_cloud_backup import prompt_cloud_backup
            prompt_cloud_backup()
        except ImportError:
            error("Cloud backup not implemented yet")
            input("Press Enter to continue...")
    
    def _handle_wordpress_menu(self) -> None:
        """Handle WordPress tools menu."""
        menu = Menu(
            title="\n🔌 WordPress Tools:",
            items=[
                MenuItem("1", "Install WordPress", self._not_implemented),
                MenuItem("2", "Manage Plugins", self._not_implemented),
                MenuItem("3", "Manage Themes", self._not_implemented),
                MenuItem("4", "Change WordPress Settings", self._not_implemented),
                MenuItem("0", "Back to Main Menu", None)
            ],
            back_id="0"
        )
        menu.display()
    
    def _handle_wp_cache_menu(self) -> None:
        """Handle WP cache setup menu."""
        menu = Menu(
            title="\n⚡ WP Cache Setup:",
            items=[
                MenuItem("1", "Install W3 Total Cache", self._not_implemented),
                MenuItem("2", "Install WP Fastest Cache", self._not_implemented),
                MenuItem("3", "Install WP Super Cache", self._not_implemented),
                MenuItem("4", "Configure FastCGI Cache", self._not_implemented),
                MenuItem("0", "Back to Main Menu", None)
            ],
            back_id="0"
        )
        menu.display()
    
    def _handle_php_menu(self) -> None:
        """Handle PHP management menu."""
        menu = Menu(
            title="\n🐘 PHP Management:",
            items=[
                MenuItem("1", "Change PHP Version", self._not_implemented),
                MenuItem("2", "Edit PHP Configuration", self._not_implemented),
                MenuItem("3", "Install PHP Extension", self._not_implemented),
                MenuItem("0", "Back to Main Menu", None)
            ],
            back_id="0"
        )
        menu.display()
    
    def _handle_mysql_menu(self) -> None:
        """Handle MySQL management menu."""
        menu = Menu(
            title="\n🗄️ MySQL Management:",
            items=[
                MenuItem("1", "Edit MySQL Configuration", self._not_implemented),
                MenuItem("2", "Restore Database", self._not_implemented),
                MenuItem("0", "Back to Main Menu", None)
            ],
            back_id="0"
        )
        menu.display()
    
    def _handle_update_menu(self) -> None:
        """Handle update menu."""
        menu = Menu(
            title="\n🔄 Check & Update WP Docker:",
            items=[
                MenuItem("1", "Check for Updates", self._not_implemented),
                MenuItem("2", "Update to Latest Version", self._not_implemented),
                MenuItem("3", "View Changelog", self._not_implemented),
                MenuItem("0", "Back to Main Menu", None)
            ],
            back_id="0"
        )
        menu.display()
    
    def _handle_list_websites(self) -> None:
        """Handle website listing."""
        try:
            from src.features.website.cli.list import list_websites
            list_websites()
        except ImportError:
            self._not_implemented()
    
    def _not_implemented(self) -> None:
        """Handle not implemented features."""
        error("🚧 Feature not implemented yet")
        input("Press Enter to continue...")