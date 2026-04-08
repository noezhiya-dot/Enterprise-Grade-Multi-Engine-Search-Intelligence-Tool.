"""Ask search engine implementation."""

import logging
from typing import List
from bs4 import BeautifulSoup

from ..models import SearchResult
from .base import SearchEngine

logger = logging.getLogger(__name__)


class AskEngine(SearchEngine):
    """Ask search engine implementation."""
    
    name = "ask"
    
    async def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search Ask for results.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        results = []
        url = "https://www.ask.com/web"
        
        rank_counter = 1
        for page in range(1, (limit + 9) // 10 + 2):  # Get up to 10 per page
            if len(results) >= limit:
                break
                
            params = {
                "q": query,
                "page": page
            }
            
            html = await self.fetch(url, params)
            if not html:
                break
            
            soup = BeautifulSoup(html, "html.parser")
            page_results = 0
            
            for div in soup.select("div.PartialSearchResults-item"):
                if len(results) >= limit:
                    break
                    
                try:
                    title_elem = div.select_one("a.PartialSearchResults-item-title-link")
                    desc_elem = div.select_one("p.PartialSearchResults-item-abstract")
                    
                    if title_elem:
                        results.append(SearchResult(
                            title=title_elem.get_text(strip=True),
                            url=title_elem.get("href", ""),
                            description=desc_elem.get_text(strip=True) if desc_elem else "",
                            engine=self.name,
                            rank=rank_counter
                        ))
                        rank_counter += 1
                        page_results += 1
                except Exception:
                    continue
            
            # If no results on this page, stop trying
            if page_results == 0:
                break
        
        return results[:limit]
