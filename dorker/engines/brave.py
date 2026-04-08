"""Brave search engine implementation."""

import logging
from typing import List
from bs4 import BeautifulSoup

from ..models import SearchResult
from .base import SearchEngine

logger = logging.getLogger(__name__)


class BraveEngine(SearchEngine):
    """Brave search engine implementation."""
    
    name = "brave"
    
    async def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search Brave for results.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        api_key = self.config.get("brave_api_key")
        
        if api_key:
            return await self._search_api(query, limit, api_key)
        else:
            return await self._search_scrape(query, limit)
    
    async def _search_api(self, query: str, limit: int, api_key: str) -> List[SearchResult]:
        """Search using Brave API.
        
        Args:
            query: Search query
            limit: Maximum results to return
            api_key: Brave API key
            
        Returns:
            List of search results
        """
        results = []
        url = "https://api.search.brave.com/res/v1/web/search"
        
        headers = self.get_headers()
        headers["X-Subscription-Token"] = api_key
        headers["Accept"] = "application/json"
        
        params = {
            "q": query,
            "count": min(limit, 100)
        }
        
        try:
            await self.rate_limiter.wait(self.name)
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    rank_counter = 1
                    for result in data.get("web", {}).get("results", []):
                        if len(results) >= limit:
                            break
                            
                        results.append(SearchResult(
                            title=result.get("title", ""),
                            url=result.get("url", ""),
                            description=result.get("description", ""),
                            engine=self.name,
                            rank=rank_counter
                        ))
                        rank_counter += 1
        except Exception as e:
            logger.error(f"Brave API error: {e}")
        
        return results[:limit]
    
    async def _search_scrape(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search by scraping Brave results.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        results = []
        url = "https://search.brave.com/search"
        
        params = {
            "q": query,
            "source": "web"
        }
        
        html = await self.fetch(url, params)
        if not html:
            return results
        
        soup = BeautifulSoup(html, "html.parser")
        
        rank_counter = 1
        for div in soup.select("div.snippet"):
            if len(results) >= limit:
                break
                
            try:
                title_elem = div.select_one("a.result-header")
                desc_elem = div.select_one("p.snippet-description")
                
                if title_elem:
                    results.append(SearchResult(
                        title=title_elem.get_text(strip=True),
                        url=title_elem.get("href", ""),
                        description=desc_elem.get_text(strip=True) if desc_elem else "",
                        engine=self.name,
                        rank=rank_counter
                    ))
                    rank_counter += 1
            except Exception:
                continue
        
        return results[:limit]
