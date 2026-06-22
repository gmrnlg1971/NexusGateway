import time
import uuid
import redis.asyncio as redis
from nexus_gateway.core.config import settings

class AsyncRateLimiter:
    """
    Asynchronous rate limiter to protect upstream APIs using Redis.
    """
    def __init__(self, redis_url: str) -> None:
        """
        Initializes the rate limiter with a Redis connection.
        
        Args:
            redis_url: Connection string for the Redis instance.
        """
        self.redis: redis.Redis = redis.from_url(redis_url, decode_responses=True)

    async def is_rate_limited(self, user_id: str, limit: int = 600, window: int = 60) -> bool:
        """
        Sliding window rate limiter using Redis sorted sets.
        O(log(N)) performance. Prevents proxy abuse.
        
        Args:
            user_id: Identifier of the client.
            limit: Maximum number of requests allowed in the window.
            window: Time window in seconds.
            
        Returns:
            True if the rate limit is exceeded, False otherwise.
        """
        current_time = int(time.time())
        key = f"rate_limit:{user_id}"

        async with self.redis.pipeline(transaction=True) as pipe:
            # Remove elements outside the current window
            pipe.zremrangebyscore(key, 0, current_time - window)
            # Add current request
            pipe.zadd(key, {f"{current_time}:{uuid.uuid4()}": current_time})
            # Count elements in window
            pipe.zcard(key)
            # Set expiry to prevent stale keys
            pipe.expire(key, window)
            
            results = await pipe.execute()
            request_count = results[2]

        return request_count > limit

limiter = AsyncRateLimiter(settings.redis_url)
