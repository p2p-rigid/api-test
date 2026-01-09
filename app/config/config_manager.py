"""
Configuration manager for handling different environments and settings validation.
"""
from typing import Dict, Any
from app.config.settings import Settings, settings
import os


class ConfigManager:
    """
    Configuration manager for handling different environments and settings validation.
    """
    
    def __init__(self, settings_instance: Settings = None):
        self.settings = settings_instance or settings
        self._validate_settings()
    
    def _validate_settings(self) -> None:
        """
        Perform additional runtime validation of settings.
        """
        # Check if required environment variables are set
        required_vars = []
        if not self.settings.database_url:
            required_vars.append("DATABASE_URL")
        
        if required_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(required_vars)}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration parameters.
        
        Returns:
            Dictionary containing database configuration parameters
        """
        return {
            "pool_size": self.settings.database_pool_size,
            "max_overflow": self.settings.database_max_overflow,
            "pool_pre_ping": True,
            "echo": self.settings.debug,
        }
    
    def get_app_config(self) -> Dict[str, Any]:
        """
        Get application configuration parameters.
        
        Returns:
            Dictionary containing application configuration parameters
        """
        return {
            "debug": self.settings.debug,
            "app_name": self.settings.app_name,
        }
    
    def is_production(self) -> bool:
        """
        Check if the application is running in production environment.
        
        Returns:
            True if in production environment, False otherwise
        """
        env = os.getenv("ENVIRONMENT", "development").lower()
        return env in ["prod", "production"]
    
    def is_development(self) -> bool:
        """
        Check if the application is running in development environment.
        
        Returns:
            True if in development environment, False otherwise
        """
        env = os.getenv("ENVIRONMENT", "development").lower()
        return env in ["dev", "development"]
    
    def is_testing(self) -> bool:
        """
        Check if the application is running in testing environment.
        
        Returns:
            True if in testing environment, False otherwise
        """
        env = os.getenv("ENVIRONMENT", "development").lower()
        return env in ["test", "testing"]


# Global configuration manager instance
config_manager = ConfigManager()