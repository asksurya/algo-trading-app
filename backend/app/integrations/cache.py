"""
Redis cache wrapper for Alpaca API responses.
Provides async caching with TTL management.
"""
import json
import logging
from typing import Any, Optional, Callable
from functools import wraps
import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Async Redis cache manager for Alpaca API responses.
    Implements cache-aside pattern with automatic TTL management.
    """
    
    _instance: Optional['CacheManager'] = None
    _redis_client: Optional[redis.Redis] = None
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """Initialize Redis connection."""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                )
                # Test connection
                await self._redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache: {e}")
                self._redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if self._redis_client is None:
            await self.initialize()
            if self._redis_client is None:
                return None
        
        try:
            value = await self._redis_client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (default: 5 minutes)
        """
        if self._redis_client is None:
            await self.initialize()
            if self._redis_client is None:
                return
        
        try:
            serialized = json.dumps(value, default=str)
            await self._redis_client.setex(key, ttl, serialized)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
    
    async def delete(self, key: str):
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        if self._redis_client is None:
            return
        
        try:
            await self._redis_client.delete(key)
            logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
    
    async def clear_pattern(self, pattern: str):
        """
        Clear all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "alpaca:*")
        """
        if self._redis_client is None:
            return
        
        try:
            cursor = 0
            while True:
                cursor, keys = await self._redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                if keys:
                    await self._redis_client.delete(*keys)
                    logger.debug(f"Cache cleared {len(keys)} keys matching {pattern}")
                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
    
    async def close(self):
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
            logger.info("Redis cache connection closed")


# Global cache instance
_cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    return _cache_manager


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        
    Usage:
        @cached(ttl=60, key_prefix="alpaca:account")
        async def get_account(user_id: str):
            return await fetch_account(user_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and args
            cache_key_parts = [key_prefix or func.__name__]
            
            # Add positional args to key
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    cache_key_parts.append(str(arg))
            
            # Add keyword args to key
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    cache_key_parts.append(f"{k}:{v}")
            
            cache_key = ":".join(cache_key_parts)
            
            # Try to get from cache
            cache = get_cache_manager()
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator