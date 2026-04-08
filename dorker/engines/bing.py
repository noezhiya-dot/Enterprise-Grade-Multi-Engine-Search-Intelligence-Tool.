"""Bing search engine implementation."""

import logging
from typing import List
from bs4 import BeautifulSoup

from ..models import SearchResult
from .base import SearchEngine

logger = logging.getLogger(__name__)


class BingEngine(SearchEngine):
    """Bing search engine implementation."""
    
    name = "bing"
    
    async def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search Bing for results.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        api_key = self.config.get("bing_api_key")
        
        if api_key:
            return await self._search_api(query, limit, api_key)
        else:
            return await self._search_scrape(query, limit)
    
    async def _search_api(self, query: str, limit: int, api_key: str) -> List[SearchResult]:
        """Search using Bing API.
        
        Args:
            query: Search query
            limit: Maximum results to return
            api_key: Bing API key
            
        Returns:
            List of search results
        """
        results = []
        url = "https://api.bing.microsoft.com/v7.0/search"
        
        headers = self.get_headers()
        headers["Ocp-Apim-Subscription-Key"] = api_key
        
        rank_counter = 1
        for page in range(0, (limit + 49) // 50):  # Get up to 50 per page
            if len(results) >= limit:
                break
                
            offset = page * 50
            params = {
                "q": query,
                "count": min(50, limit - len(results)),
                "offset": offset,
                "mkt": "en-US"
            }
            
            try:
                await self.rate_limiter.wait(self.name)
                async with self.session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        web_pages = data.get("webPages", {}).get("value", [])
                        
                        if not web_pages:
                            break
                        
                        for result in web_pages:
                            if len(results) >= limit:
                                break
                            results.append(SearchResult(
                                title=result.get("name", ""),
                                url=result.get("url", ""),
                                description=result.get("snippet", ""),
                                engine=self.name,
                                rank=rank_counter
                            ))
                            rank_counter += 1
            except Exception as e:
                logger.error(f"Bing API error: {e}")
                break
        
        return results[:limit]
    
    async def _search_scrape(self, query: str, limit: int) -> List[SearchResult]:
        """Search by scraping Bing results.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        results = []
        url = "https://www.bing.com/search"
        
        rank_counter = 1
        failed_pages = 0
        for page in range(0, (limit + 9) // 10):  # Get up to 10 per page
            if len(results) >= limit or failed_pages >= 2:
                break
                
            first = page * 10 + 1
            params = {
                "q": query,
                "first": first,
                "count": 10
            }
            
            await self.rate_limiter.wait(self.name)
            html = await self.fetch(url, params)
            if not html:
                failed_pages += 1
                continue
            
            soup = BeautifulSoup(html, "html.parser")
            page_results = 0
            
            # Try multiple selectors for compatibility
            search_items = soup.select("li.b_algo") or soup.select("li[data-bm]") or soup.select("div.b_rich")
            
            for item in search_items:
                if len(results) >= limit:
                    break
                    
                try:
                    title_elem = item.select_one("h2 a") or item.select_one("a.result_title")
                    desc_elem = item.select_one("p, .b_caption p, div.b_caption")
                    
                    if title_elem:
                        url_text = title_elem.get("href", "")
                        if url_text:
                            results.append(SearchResult(
                                title=title_elem.get_text(strip=True),
                                url=url_text,
                                description=desc_elem.get_text(strip=True) if desc_elem else "",
                                engine=self.name,
                                rank=rank_counter
                            ))
                            rank_counter += 1
                            page_results += 1
                except Exception as e:
                    continue
            
            # If no results on this page, increment failed counter
            if page_results == 0:
                failed_pages += 1
        
        return results[:limit]
