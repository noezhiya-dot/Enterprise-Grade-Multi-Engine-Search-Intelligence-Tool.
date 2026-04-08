"""DuckDuckGo search engine implementation."""

import asyncio
import logging
from typing import List

from ..models import SearchResult
from .base import SearchEngine

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

logger = logging.getLogger(__name__)


class DuckDuckGoEngine(SearchEngine):
    """DuckDuckGo search engine implementation."""
    
    name = "duckduckgo"
    
    async def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search DuckDuckGo for results.
        
        Args:
            query: Search query
            limit: Maximum results to return (ignored, fetches all available)
            
        Returns:
            List of search results
        """
        if DDGS is None:
            logger.error("DuckDuckGo search library not installed")
            return []
        
        await self.rate_limiter.wait(self.name)
        
        loop = asyncio.get_event_loop()
        try:
            # Request unlimited results (very high number)
            results = await loop.run_in_executor(None, self._search_sync, query, 10000)
            return results
        except Exception as e:
            logger.error(f"DuckDuckGo error: {e}")
            return []
    
    def _search_sync(self, query: str, limit: int) -> List[SearchResult]:
        """Synchronous search helper for DuckDuckGo.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        results = []
        try:
            with DDGS() as ddgs:
                search_results = list(ddgs.text(query, max_results=limit))
                
                for rank, result in enumerate(search_results, 1):
                    results.append(SearchResult(
                        title=result.get("title", ""),
                        url=result.get("href", ""),
                        description=result.get("body", ""),
                        engine=self.name,
                        rank=rank
                    ))
        except Exception as e:
            logger.error(f"DuckDuckGo sync error: {e}")
        
        return results
