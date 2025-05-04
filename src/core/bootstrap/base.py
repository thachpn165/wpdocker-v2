"""
Base bootstrap module.

This module provides the abstract base class for all bootstrap components.
"""

from abc import ABC, abstractmethod
from src.common.logging import Debug, log_call


class BaseBootstrap(ABC):
    """
    Abstract base class for all bootstrappers.
    
    This implements the Template Method pattern for bootstrap operations,
    ensuring consistent initialization and error handling across all
    bootstrap components.
    """
    
    def __init__(self, name: str) -> None:
        """
        Initialize the bootstrap component.
        
        Args:
            name: Name of the bootstrap component
        """
        self.debug = Debug(name)
        
    @log_call
    def bootstrap(self) -> bool:
        """
        Run the bootstrap process.
        
        This is the main template method that orchestrates the bootstrap process:
        1. Check if bootstrap is already completed
        2. Check prerequisites
        3. Execute the bootstrap
        4. Mark as complete
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.debug.info(f"Starting bootstrap")
        
        # Skip if already bootstrapped
        if self.is_bootstrapped():
            self.debug.info("Already bootstrapped, skipping")
            return True
            
        # Check prerequisites
        if not self.check_prerequisites():
            self.debug.error("Prerequisites not met, bootstrap aborted")
            return False
            
        # Execute bootstrap
        try:
            result = self.execute_bootstrap()
            if result:
                self.mark_bootstrapped()
                self.debug.success("Bootstrap completed successfully")
            else:
                self.debug.error("Bootstrap failed")
            return result
        except Exception as e:
            self.debug.error(f"Bootstrap failed with exception: {e}")
            return False
    
    @abstractmethod
    def is_bootstrapped(self) -> bool:
        """
        Check if this component is already bootstrapped.
        
        Returns:
            bool: True if already bootstrapped, False otherwise
        """
        pass
        
    @abstractmethod
    def check_prerequisites(self) -> bool:
        """
        Check if prerequisites for bootstrap are met.
        
        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        pass
        
    @abstractmethod
    def execute_bootstrap(self) -> bool:
        """
        Execute the bootstrap process.
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
        
    @abstractmethod
    def mark_bootstrapped(self) -> None:
        """Mark this component as bootstrapped."""
        pass