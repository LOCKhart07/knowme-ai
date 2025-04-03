import os
from typing import List, Optional
import time
from dotenv import load_dotenv
from .redis_service import RedisService

load_dotenv()


class APIKeyBalancer:
    def __init__(self, redis_service: RedisService):
        self.redis_service = redis_service
        self.api_keys = self._get_api_keys()
        self.rate_limit_window = 60  # 1 minute window
        self.max_requests_per_window = 60  # 60 requests per minute per key
        self._current_key_index = 0
        self._last_key_time = 0

    def _get_api_keys(self) -> List[str]:
        """Get API keys from environment variables"""
        api_keys_str = os.getenv("GOOGLE_API_KEYS", "")
        if not api_keys_str:
            # Fallback to single key for backward compatibility
            single_key = os.getenv("GOOGLE_API_KEY")
            return [single_key] if single_key else []

        # Split by comma and strip whitespace
        return [key.strip() for key in api_keys_str.split(",") if key.strip()]

    def _get_key_usage_key(self, api_key: str) -> str:
        """Get Redis key for tracking API key usage"""
        return f"api_key_usage:{api_key}"

    def _get_key_errors_key(self, api_key: str) -> str:
        """Get Redis key for tracking API key errors"""
        return f"api_key_errors:{api_key}"

    def _get_next_available_key(self) -> Optional[str]:
        """Get the next available key in round-robin fashion"""
        if not self.api_keys:
            return None

        current_time = int(time.time())
        window_start = current_time - self.rate_limit_window

        # Try each key in sequence until we find an available one
        for _ in range(len(self.api_keys)):
            # Get next key in round-robin
            self._current_key_index = (self._current_key_index + 1) % len(self.api_keys)
            api_key = self.api_keys[self._current_key_index]

            # Check if key is marked as failed
            if self.redis_service.get(self._get_key_errors_key(api_key)):
                continue

            # Get usage count for the current window
            usage_key = self._get_key_usage_key(api_key)
            timestamps = self.redis_service.get(usage_key) or []
            if isinstance(timestamps, str):
                timestamps = timestamps.split(",")
            usage_count = len(
                [ts for ts in timestamps if window_start <= int(ts) <= current_time]
            )

            # If key is within rate limit, use it
            if usage_count < self.max_requests_per_window:
                return api_key

        return None

    def get_next_key(self) -> Optional[str]:
        """Get the next available API key using round-robin distribution"""
        if not self.api_keys:
            return None

        current_time = int(time.time())
        api_key = self._get_next_available_key()

        if api_key:
            # Record the usage
            usage_key = self._get_key_usage_key(api_key)
            current_timestamps = self.redis_service.get(usage_key) or ""
            if current_timestamps:
                current_timestamps = f"{current_timestamps},{current_time}"
            else:
                current_timestamps = str(current_time)
            self.redis_service.set(
                usage_key, current_timestamps, expire=self.rate_limit_window
            )

            # Clean up old entries
            timestamps = current_timestamps.split(",")
            valid_timestamps = [
                ts
                for ts in timestamps
                if int(ts) >= current_time - self.rate_limit_window
            ]
            if valid_timestamps:
                self.redis_service.set(
                    usage_key, ",".join(valid_timestamps), expire=self.rate_limit_window
                )
            else:
                self.redis_service.delete(usage_key)

        return api_key

    def mark_key_failed(self, api_key: str, error_message: str):
        """Mark an API key as failed and store the error message"""
        error_key = self._get_key_errors_key(api_key)
        self.redis_service.set(
            error_key, error_message, expire=300
        )  # Mark as failed for 5 minutes

    def clear_key_errors(self, api_key: str):
        """Clear error status for an API key"""
        error_key = self._get_key_errors_key(api_key)
        self.redis_service.delete(error_key)
