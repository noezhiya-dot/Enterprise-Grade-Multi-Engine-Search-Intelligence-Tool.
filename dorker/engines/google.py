"""Google search engine implementations."""

import json
import logging
from typing import List
from bs4 import BeautifulSoup

from ..models import SearchResult
from .base import SearchEngine

logger = logging.getLogger(__name__)


class GoogleEngine(SearchEngine):
    """Google search engine with multiple search methods."""
    
    name = "google"
    
    async def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search Google for results using available method.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        # Try SerpAPI if available
        if self.config.get("serpapi_key"):
            results = await self._search_serpapi(query, limit, self.config.get("serpapi_key"))
            if results:
                return results
        
        # Try Custom API if available
        if self.config.get("google_api_key"):
            results = await self._search_custom_api(query, limit)
            if results:
                return results
        
        # Fallback to scraping
        return await self._search_scrape(query, limit)
    
    async def _search_serpapi(self, query: str, limit: int, api_key: str) -> List[SearchResult]:
        """Search using SerpAPI.
        
        Args:
            query: Search query
            limit: Maximum results to return (ignored, fetches all available)
            api_key: SerpAPI key
            
        Returns:
            List of search results
        """
        results = []
        url = "https://serpapi.com/search"
        rank_counter = 1
        page = 1
        max_empty_pages = 0
        max_pages = 5  # Limit to 5 pages to prevent excessive requests and costs
        
        # Keep fetching pages until no more results or max pages reached
        while max_empty_pages < 2 and page <= max_pages:
            params = {
                "q": query,
                "api_key": api_key,
                "engine": "google",
                "page": page,
                "num": 100  # Request max per page
            }
            
            try:
                html = await self.fetch(url, params)
                if html:
                    data = json.loads(html)
                    organic_results = data.get("organic_results", [])
                    
                    if not organic_results:
                        logger.debug(f"No results on page {page}")
                        max_empty_pages += 1
                        page += 1
                        continue
                    
                    max_empty_pages = 0  # Reset counter if we got results
                    page_count = len(organic_results)
                    for result in organic_results:
                        url_value = result.get("link", "")
                        if url_value:
                            results.append(SearchResult(
                                title=result.get("title", ""),
                                url=url_value,
                                description=result.get("snippet", ""),
                                engine=self.name,
                                rank=rank_counter
                            ))
                            rank_counter += 1
                    
                    logger.debug(f"Page {page}: {page_count} results, total: {len(results)}")
                    page += 1
                else:
                    logger.warning(f"No response from SerpAPI on page {page}")
                    break
                    
            except Exception as e:
                logger.error(f"Google SerpAPI error on page {page}: {e}")
                break
        
        logger.info(f"SerpAPI returned {len(results)} results for '{query}'")
        return results
    
    async def _search_custom_api(self, query: str, limit: int) -> List[SearchResult]:
        """Search using Google Custom Search API.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        results = []
        api_key = self.config.get("google_api_key")
        cx = self.config.get("google_cx")
        
        if not api_key or not cx:
            logger.warning("Google Custom Search requires API key and CX")
            return results
        
        url = "https://www.googleapis.com/customsearch/v1"
        
        for start in range(1, limit + 1, 10):
            params = {
                "key": api_key,
                "cx": cx,
                "q": query,
                "start": start,
                "num": min(10, limit - start + 1)
            }
            
            try:
                html = await self.fetch(url, params)
                if html:
                    data = json.loads(html)
                    for rank, result in enumerate(data.get("items", []), start):
                        results.append(SearchResult(
                            title=result.get("title", ""),
                            url=result.get("link", ""),
                            description=result.get("snippet", ""),
                            engine=self.name,
                            rank=rank
                        ))
            except Exception as e:
                logger.error(f"Google Custom Search API error: {e}")
                break
            
            if len(results) >= limit:
                break
        
        return results[:limit]
    
    async def _search_scrape(self, query: str, limit: int) -> List[SearchResult]:
        """Search by scraping Google results.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        results = []
        url = "https://www.google.com/search"
        
        # Calculate number of pages needed
        pages_needed = (limit + 9) // 10  # Round up division
        rank_counter = 1
        failed_pages = 0
        
        for page in range(pages_needed):
            if len(results) >= limit or failed_pages >= 2:
                break
            
            await self.rate_limiter.wait(self.name)  # Rate limit each page
                
            start = page * 10
            params = {
                "q": query,
                "start": start,
                "num": 10,
                "hl": "en"
            }
            
            html = await self.fetch(url, params)
            if not html:
                failed_pages += 1
                continue
            
            soup = BeautifulSoup(html, "html.parser")
            page_results = 0
            
            for div in soup.select("div.g"):
                if len(results) >= limit:
                    break
                    
                try:
                    title_elem = div.select_one("h3")
                    link_elem = div.select_one("a[href^='http']")
                    desc_elem = div.select_one("div[data-sncf], span.aCOpRe, div.VwiC3b")
                    
                    if title_elem and link_elem:
                        results.append(SearchResult(
                            title=title_elem.get_text(strip=True),
                            url=link_elem.get("href", ""),
                            description=desc_elem.get_text(strip=True) if desc_elem else "",
                            engine=self.name,
                            rank=rank_counter
                        ))
                        rank_counter += 1
                        page_results += 1
                except Exception:
                    continue
            
            # If no results found on this page, stop trying
            if page_results == 0:
                failed_pages += 1
        
        return results[:limit]
