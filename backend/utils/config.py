"""
Environment Configuration
Controls feature flags and environment-specific behavior
"""

import os
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Config:
    """Application configuration based on environment"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables"""
        env_name = os.environ.get("APP_ENV", "production").lower()
        
        try:
            self.environment = Environment(env_name)
        except ValueError:
            logger.warning(f"Unknown environment '{env_name}', defaulting to production")
            self.environment = Environment.PRODUCTION
        
        # Feature flags
        self.notifications_enabled = os.environ.get("NOTIFICATIONS_ENABLED", "true").lower() == "true"
        self.whatsapp_enabled = os.environ.get("WHATSAPP_ENABLED", "true").lower() == "true"
        self.email_enabled = os.environ.get("EMAIL_ENABLED", "true").lower() == "true"
        
        # Override for development
        if self.environment == Environment.DEVELOPMENT:
            # Disable external notifications in dev unless explicitly enabled
            if os.environ.get("FORCE_NOTIFICATIONS") != "true":
                self.whatsapp_enabled = False
                self.email_enabled = False
                logger.info("Development mode: External notifications disabled")
        
        # Logging configuration
        self.log_level = os.environ.get("LOG_LEVEL", "INFO")
        self.log_retention_days = int(os.environ.get("LOG_RETENTION_DAYS", "30"))
        
        # Performance settings
        self.api_cache_ttl = int(os.environ.get("API_CACHE_TTL", "60"))  # seconds
        self.max_upload_size_mb = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "50"))
        
        logger.info(f"Configuration loaded for environment: {self.environment.value}")
    
    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_staging(self) -> bool:
        return self.environment == Environment.STAGING
    
    def should_send_whatsapp(self) -> bool:
        """Check if WhatsApp notifications should be sent"""
        return self.notifications_enabled and self.whatsapp_enabled
    
    def should_send_email(self) -> bool:
        """Check if email notifications should be sent"""
        return self.notifications_enabled and self.email_enabled
    
    def get_log_config(self) -> dict:
        """Get logging configuration"""
        return {
            "level": self.log_level,
            "retention_days": self.log_retention_days,
            "async_logging": True
        }


# Singleton accessor
_config: Optional[Config] = None


def get_config() -> Config:
    """Get application configuration"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def is_notifications_enabled() -> bool:
    """Quick check if notifications are enabled"""
    return get_config().notifications_enabled


def is_whatsapp_enabled() -> bool:
    """Quick check if WhatsApp is enabled"""
    return get_config().should_send_whatsapp()


def is_email_enabled() -> bool:
    """Quick check if email is enabled"""
    return get_config().should_send_email()
