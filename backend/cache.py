"""
Cache module for performance optimization
Caches static/semi-static data to reduce database calls
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

# In-memory cache with TTL
_cache: Dict[str, Dict[str, Any]] = {}
DEFAULT_TTL_MINUTES = 10


def get_cached(key: str) -> Optional[Any]:
    """Get cached value if exists and not expired"""
    if key in _cache:
        entry = _cache[key]
        if datetime.now(timezone.utc) < entry['expires_at']:
            return entry['value']
        else:
            # Expired, remove from cache
            del _cache[key]
    return None


def set_cached(key: str, value: Any, ttl_minutes: int = DEFAULT_TTL_MINUTES):
    """Set cache value with TTL"""
    _cache[key] = {
        'value': value,
        'expires_at': datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes),
        'created_at': datetime.now(timezone.utc)
    }


def invalidate_cache(key: str = None):
    """Invalidate specific key or all cache"""
    global _cache
    if key:
        _cache.pop(key, None)
    else:
        _cache = {}


def get_cache_stats() -> Dict:
    """Get cache statistics"""
    now = datetime.now(timezone.utc)
    valid_entries = sum(1 for e in _cache.values() if now < e['expires_at'])
    return {
        "total_entries": len(_cache),
        "valid_entries": valid_entries,
        "expired_entries": len(_cache) - valid_entries
    }


# Pre-loaded configuration (loaded once at startup)
class AppConfig:
    """Application configuration loaded once at startup"""
    
    _instance = None
    _loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not AppConfig._loaded:
            self._load_config()
            AppConfig._loaded = True
    
    def _load_config(self):
        """Load all environment variables once"""
        import os
        
        # Database
        self.MONGO_URL = os.environ.get('MONGO_URL')
        self.DB_NAME = os.environ.get('DB_NAME', 'architecture_firm')
        
        # JWT
        self.JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
        self.JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
        self.JWT_EXPIRE_MINUTES = int(os.environ.get('JWT_EXPIRE_MINUTES', 10080))
        
        # App URL
        self.APP_URL = os.environ.get('REACT_APP_BACKEND_URL', '')
        
        # Twilio
        self.TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
        self.TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
        self.TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER')
        self.TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
        
        # SendGrid
        self.SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
        self.SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'contact@4thdimensionarchitect.com')
        
        # File storage
        self.MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 524288000))
        
        logger.info("Application configuration loaded")
    
    def reload(self):
        """Force reload configuration"""
        AppConfig._loaded = False
        self._load_config()


# Singleton instance
config = AppConfig()
