"""
In-Memory Cache Service
Short-term caching (30-60 seconds) for frequently accessed data
"""

import asyncio
import logging
from typing import Any, Optional, Callable
from datetime import datetime, timezone
from functools import wraps
import hashlib
import json

logger = logging.getLogger(__name__)


class CacheEntry:
    """Single cache entry with expiration"""
    
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expires_at = datetime.now(timezone.utc).timestamp() + ttl_seconds
    
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc).timestamp() > self.expires_at


class InMemoryCache:
    """
    Simple in-memory cache with TTL support.
    Designed for short-term caching of frequently accessed data.
    """
    
    def __init__(self):
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task = None
    
    async def start_cleanup(self):
        """Start background cleanup task"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Cache cleanup task started")
    
    async def stop_cleanup(self):
        """Stop background cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_loop(self):
        """Periodically clean up expired entries"""
        while True:
            try:
                await asyncio.sleep(30)  # Run cleanup every 30 seconds
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    async def _cleanup_expired(self):
        """Remove expired entries from cache"""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() 
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        async with self._lock:
            entry = self._cache.get(key)
            if entry and not entry.is_expired():
                return entry.value
            elif entry:
                # Remove expired entry
                del self._cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 30):
        """Set value in cache with TTL"""
        async with self._lock:
            self._cache[key] = CacheEntry(value, ttl_seconds)
    
    async def delete(self, key: str):
        """Delete key from cache"""
        async with self._lock:
            self._cache.pop(key, None)
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching a pattern (prefix match)"""
        async with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys() 
                if key.startswith(pattern)
            ]
            for key in keys_to_delete:
                del self._cache[key]
            
            if keys_to_delete:
                logger.debug(f"Invalidated {len(keys_to_delete)} cache entries matching '{pattern}'")
    
    async def clear(self):
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    def stats(self) -> dict:
        """Get cache statistics"""
        return {
            "total_entries": len(self._cache),
            "active_entries": sum(
                1 for entry in self._cache.values() 
                if not entry.is_expired()
            )
        }


# Singleton instance
cache = InMemoryCache()


# Cache decorator for async functions
def cached(ttl_seconds: int = 30, key_prefix: str = ""):
    """
    Decorator to cache async function results.
    
    Usage:
        @cached(ttl_seconds=60, key_prefix="projects")
        async def get_projects(user_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl_seconds)
            logger.debug(f"Cache miss, stored: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


# Specific cache helpers
async def get_cached_projects(user_id: str, is_owner: bool) -> Optional[list]:
    """Get cached projects list"""
    key = f"projects:{user_id}:{is_owner}"
    return await cache.get(key)


async def set_cached_projects(user_id: str, is_owner: bool, projects: list, ttl: int = 30):
    """Cache projects list"""
    key = f"projects:{user_id}:{is_owner}"
    await cache.set(key, projects, ttl)


async def invalidate_projects_cache(user_id: str = None):
    """Invalidate projects cache for a user or all users"""
    if user_id:
        await cache.invalidate_pattern(f"projects:{user_id}")
    else:
        await cache.invalidate_pattern("projects:")


async def get_cached_drawings(project_id: str) -> Optional[list]:
    """Get cached drawings for a project"""
    key = f"drawings:{project_id}"
    return await cache.get(key)


async def set_cached_drawings(project_id: str, drawings: list, ttl: int = 30):
    """Cache drawings for a project"""
    key = f"drawings:{project_id}"
    await cache.set(key, drawings, ttl)


async def invalidate_drawings_cache(project_id: str):
    """Invalidate drawings cache for a project"""
    await cache.invalidate_pattern(f"drawings:{project_id}")


async def get_cached_roles() -> Optional[list]:
    """Get cached roles list"""
    return await cache.get("roles:all")


async def set_cached_roles(roles: list, ttl: int = 60):
    """Cache roles list (longer TTL as roles rarely change)"""
    await cache.set("roles:all", roles, ttl)


async def get_cached_user(user_id: str) -> Optional[dict]:
    """Get cached user data"""
    return await cache.get(f"user:{user_id}")


async def set_cached_user(user_id: str, user: dict, ttl: int = 60):
    """Cache user data"""
    await cache.set(f"user:{user_id}", user, ttl)


async def invalidate_user_cache(user_id: str):
    """Invalidate user cache"""
    await cache.delete(f"user:{user_id}")
