"""Yandex search engine implementation."""

import logging
from typing import List
from bs4 import BeautifulSoup

from ..models import SearchResult
from .base import SearchEngine

logger = logging.getLogger(__name__)


class YandexEngine(SearchEngine):
    """Yandex search engine implementation."""
    
    name = "yandex"
    
    async def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search Yandex for results.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        results = []
        url = "https://yandex.com/search/"
        
        rank_counter = 1
        for page in range(0, (limit + 9) // 10):  # Get up to 10 per page
            if len(results) >= limit:
                break
                
            params = {
                "text": query,
                "p": page,
                "numdoc": 10,
                "lr": 84  # English results
            }
            
            html = await self.fetch(url, params)
            if not html:
                break
            
            soup = BeautifulSoup(html, "html.parser")
            page_results = 0
            
            for li in soup.select("li.serp-item"):
                if len(results) >= limit:
                    break
                    
                try:
                    title_elem = li.select_one("h2 a, a.organic__url")
                    desc_elem = li.select_one("div.organic__text, span.organic__content-wrapper")
                    
                    if title_elem:
                        href = title_elem.get("href", "")
                        if href and not href.startswith("//yandex"):
                            results.append(SearchResult(
                                title=title_elem.get_text(strip=True),
                                url=href if href.startswith("http") else f"https:{href}",
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
