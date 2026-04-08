"""Rate limiting utility for throttling requests."""

import time
import random
import asyncio
from typing import Dict


class RateLimiter:
    """Rate limiter to control request frequency per search engine."""
    
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Initialize rate limiter with delay range.
        
        Args:
            min_delay: Minimum delay between requests in seconds
            max_delay: Maximum delay between requests in seconds
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request: Dict[str, float] = {}
    
    async def wait(self, engine: str):
        """Wait appropriate amount of time based on last request.
        
        Args:
            engine: Name of the search engine
        """
        now = time.time()
        if engine in self.last_request:
            elapsed = now - self.last_request[engine]
            delay = random.uniform(self.min_delay, self.max_delay)
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
        self.last_request[engine] = time.time()
