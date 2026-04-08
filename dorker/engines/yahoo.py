"""Yahoo search engine implementation."""

import logging
from typing import List
from bs4 import BeautifulSoup

from ..models import SearchResult
from .base import SearchEngine

logger = logging.getLogger(__name__)


class YahooEngine(SearchEngine):
    """Yahoo search engine implementation."""
    
    name = "yahoo"
    
    async def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search Yahoo for results.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        results = []
        url = "https://search.yahoo.com/search"
        
        rank_counter = 1
        failed_pages = 0
        for page in range(0, (limit + 9) // 10):  # Get up to 10 per page
            if len(results) >= limit or failed_pages >= 2:
                break
                
            start = page * 10 + 1
            params = {
                "p": query,
                "b": start,
                "pz": 10
            }
            
            await self.rate_limiter.wait(self.name)
            html = await self.fetch(url, params)
            if not html:
                failed_pages += 1
                continue
            
            soup = BeautifulSoup(html, "html.parser")
            page_results = 0
            
            # Try multiple selectors for compatibility
            divs = soup.select("div.algo, div.dd.algo") or soup.select("div.s") or soup.select("li.searchResult")
            
            for div in divs:
                if len(results) >= limit:
                    break
                    
                try:
                    title_elem = div.select_one("h3 a, a.ac-algo") or div.select_one("a.title")
                    desc_elem = div.select_one("p.fz-ms, div.compText, span.s")
                    
                    if title_elem:
                        href = title_elem.get("href", "")
                        if href and "yahoo.com/search" not in href:
                            results.append(SearchResult(
                                title=title_elem.get_text(strip=True),
                                url=href,
                                description=desc_elem.get_text(strip=True) if desc_elem else "",
                                engine=self.name,
                                rank=rank_counter
                            ))
                            rank_counter += 1
                            page_results += 1
                except Exception:
                    continue
            
            # If no results on this page, increment failed counter
            if page_results == 0:
                failed_pages += 1
        
        return results[:limit]
