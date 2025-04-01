from typing import Optional, Any
import json
import redis
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class RedisService:
    """
    Service for handling Redis caching operations.

    This service provides methods to interact with Redis for caching
    resume-related information.
    """

    def __init__(self):
        """Initialize Redis connection."""
        try:
            redis_kwargs = {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": int(os.getenv("REDIS_PORT", 6379)),
                "db": int(os.getenv("REDIS_DB", 0)),
                "decode_responses": True,
            }
            if os.getenv("REDIS_USERNAME") and os.getenv("REDIS_PASSWORD"):
                redis_kwargs["username"] = os.getenv("REDIS_USERNAME")
                redis_kwargs["password"] = os.getenv("REDIS_PASSWORD")

            self.redis_client = redis.Redis(**redis_kwargs)
            # Test connection
            self.redis_client.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis cache.

        Args:
            key (str): Cache key

        Returns:
            Optional[Any]: Cached value if exists, None otherwise
        """
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Error getting value from Redis: {str(e)}")
            return None

    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """
        Set value in Redis cache with expiration.

        Args:
            key (str): Cache key
            value (Any): Value to cache
            expire (int): Expiration time in seconds (default: 1 hour)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return self.redis_client.setex(key, expire, json.dumps(value))
        except Exception as e:
            logger.error(f"Error setting value in Redis: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete value from Redis cache.

        Args:
            key (str): Cache key

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting value from Redis: {str(e)}")
            return False

    def clear_all(self) -> bool:
        """
        Clear all keys from Redis cache.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return self.redis_client.flushdb()
        except Exception as e:
            logger.error(f"Error clearing Redis cache: {str(e)}")
            return False
