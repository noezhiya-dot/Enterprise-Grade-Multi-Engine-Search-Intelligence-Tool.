"""Base search engine class."""

import asyncio
import aiohttp
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List

from ..models import SearchResult
from ..utils import RateLimiter, UserAgentRotator, ProxyRotator

logger = logging.getLogger(__name__)


class SearchEngine(ABC):
    """Abstract base class for search engines."""
    
    name: str = "base"
    
    def __init__(
        self, 
        rate_limiter: RateLimiter, 
        ua_rotator: UserAgentRotator, 
        proxy_rotator: ProxyRotator, 
        config: Dict[str, Any] = None
    ):
        """Initialize search engine.
        
        Args:
            rate_limiter: Rate limiter instance
            ua_rotator: User-agent rotator instance
            proxy_rotator: Proxy rotator instance
            config: Configuration dictionary
        """
        self.rate_limiter = rate_limiter
        self.ua_rotator = ua_rotator
        self.proxy_rotator = proxy_rotator
        self.config = config or {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for request.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "User-Agent": self.ua_rotator.get(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    async def fetch(self, url: str, params: Dict = None) -> Optional[str]:
        """Fetch URL with retry logic and rate limiting.
        
        Args:
            url: URL to fetch
            params: Query parameters
            
        Returns:
            Response text or None on failure
        """
        await self.rate_limiter.wait(self.name)
        
        proxy = self.proxy_rotator.get_proxy()
        headers = self.get_headers()
        
        for attempt in range(3):
            try:
                async with self.session.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=30),
                    ssl=False
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:
                        wait_time = (attempt + 1) * 5
                        logger.warning(f"{self.name}: Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.warning(f"{self.name}: HTTP {response.status}")
                        return None
            except asyncio.TimeoutError:
                logger.warning(f"{self.name}: Timeout on attempt {attempt + 1}")
            except Exception as e:
                logger.warning(f"{self.name}: Error - {e}")
                await asyncio.sleep(2)
        
        return None
    
    @abstractmethod
    async def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search for query results.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        pass
