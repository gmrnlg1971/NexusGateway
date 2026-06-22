import time
import redis.asyncio as redis
from nexus_gateway.core.config import settings

class AsyncRateLimiter:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def is_rate_limited(self, user_id: str, limit: int = 600, window: int = 60) -> bool:
        """
        Sliding window rate limiter using Redis sorted sets.
        O(log(N)) performance. Prevents proxy abuse.
        """
        current_time = int(time.time())
        key = f"rate_limit:{user_id}"

        async with self.redis.pipeline(transaction=True) as pipe:
            # Remove elements outside the current window
            pipe.zremrangebyscore(key, 0, current_time - window)
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            # Count elements in window
            pipe.zcard(key)
            # Set expiry to prevent stale keys
            pipe.expire(key, window)
            
            results = await pipe.execute()
            request_count = results[2]

        return request_count > limit

limiter = AsyncRateLimiter(settings.redis_url)
