"""
Terminal menu components.

This module provides classes for creating interactive terminal menus.
"""

from typing import List, Callable, Any, Optional

import questionary
from rich.console import Console

from src.common.logging import Debug, log_call


class MenuItem:
    """
    Represents a single menu item.
    
    Attributes:
        id: Unique identifier for the item
        label: Display text for the item
        action: Function to call when item is selected
    """
    
    def __init__(self, id: str, label: str, action: Callable[[], Any]) -> None:
        """
        Initialize a menu item.
        
        Args:
            id: Unique identifier for the item
            label: Display text for the item
            action: Function to call when item is selected
        """
        self.id = id
        self.label = label
        self.action = action
        
    def __str__(self) -> str:
        """
        Get string representation of the menu item.
        
        Returns:
            str: Formatted string for display
        """
        return f"⏎ {self.label}" if self.id == "0" else f"[{self.id}] {self.label}"


class Menu:
    """
    Interactive terminal menu.
    
    Attributes:
        title: Menu title
        items: List of menu items
        back_id: ID of the "back" menu item
    """
    
    def __init__(self, title: str, items: List[MenuItem], back_id: str = "0") -> None:
        """
        Initialize a menu.
        
        Args:
            title: Menu title
            items: List of menu items
            back_id: ID of the "back" menu item
        """
        self.title = title
        self.items = items
        self.back_id = back_id
        self.console = Console()
        self.debug = Debug("Menu")
        
    @log_call
    def display(self) -> None:
        """Display and handle the menu interactions."""
        while True:
            choices = [str(item) for item in self.items]
            self.debug.debug(f"Displaying menu: {self.title}")
            
            answer = questionary.select(
                self.title,
                choices=choices
            ).ask()
            
            if answer is None:  # User pressed Ctrl+C
                self.debug.debug("Menu selection cancelled")
                return
                
            selected_item = next((item for item in self.items if str(item) == answer), None)
            if not selected_item:
                self.debug.warn(f"Invalid selection: {answer}")
                return
                
            if selected_item.id == self.back_id:
                self.debug.debug("Selected back option")
                return  # Exit immediately
                
            self.debug.info(f"Selected: {selected_item.label}")
            self.console.print(f"👉 [yellow]You selected:[/] {selected_item.label}")
            
            if callable(selected_item.action):
                try:
                    result = selected_item.action()
                    # Always show Enter to continue prompt to view logs
                    input("\n⏎ Press Enter to continue...")
                except Exception as e:
                    self.debug.error(f"Error executing action for {selected_item.label}: {e}")
                    self.console.print(f"[red]Error:[/] {e}")
                    input("\n⏎ Press Enter to continue...")
                
    @classmethod
    def create_with_back(cls, title: str, items: List[MenuItem]) -> 'Menu':
        """
        Create a menu with a back option already added.
        
        Args:
            title: Menu title
            items: List of menu items (without back option)
            
        Returns:
            Menu: New menu with back option added
        """
        back_item = MenuItem("0", "Back", lambda: None)
        return cls(title, items + [back_item])