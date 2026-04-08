"""Core dorking engine orchestrator."""

import asyncio
import hashlib
import logging
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urlparse

from ..models import SearchResult
from ..utils import RateLimiter, UserAgentRotator, ProxyRotator
from ..engines import ENGINES_MAP

logger = logging.getLogger(__name__)


class DorkerEngine:
    """Main orchestrator for multi-engine dorking operations."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize dorker engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.rate_limiter = RateLimiter(
            min_delay=self.config.get("min_delay", 1.0),
            max_delay=self.config.get("max_delay", 3.0)
        )
        self.ua_rotator = UserAgentRotator()
        self.proxy_rotator = ProxyRotator(self.config.get("proxies", []))
        self.results_cache: Dict[str, List[SearchResult]] = {}
    
    def get_engine(self, name: str):
        """Get search engine instance by name.
        
        Args:
            name: Engine name (lowercase)
            
        Returns:
            Search engine instance or None if not found
        """
        engine_class = ENGINES_MAP.get(name.lower())
        if engine_class:
            return engine_class(
                self.rate_limiter, 
                self.ua_rotator, 
                self.proxy_rotator, 
                self.config
            )
        return None
    
    def _get_cache_key(self, query: str, engine: str) -> str:
        """Generate cache key for query and engine combination.
        
        Args:
            query: Search query
            engine: Engine name
            
        Returns:
            Cache key hash
        """
        return hashlib.md5(f"{query}:{engine}".encode()).hexdigest()
    
    async def search(
        self, 
        query: str, 
        engines: List[str] = None, 
        limit: int = 50
    ) -> Dict[str, List[SearchResult]]:
        """Execute search across multiple engines.
        
        Args:
            query: Search query
            engines: List of engine names to search (defaults to all)
            limit: Maximum results per engine
            
        Returns:
            Dictionary mapping engine names to their results
        """
        engines = engines or list(ENGINES_MAP.keys())
        results: Dict[str, List[SearchResult]] = {}
        
        tasks = []
        engine_names = []
        
        for engine_name in engines:
            cache_key = self._get_cache_key(query, engine_name)
            if cache_key in self.results_cache:
                results[engine_name] = self.results_cache[cache_key]
                continue
            
            engine = self.get_engine(engine_name)
            if engine:
                tasks.append(self._search_with_engine(engine, query, limit))
                engine_names.append(engine_name)
        
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for engine_name, result in zip(engine_names, task_results):
                if isinstance(result, Exception):
                    logger.error(f"Error with {engine_name}: {result}")
                    results[engine_name] = []
                else:
                    results[engine_name] = result
                    cache_key = self._get_cache_key(query, engine_name)
                    self.results_cache[cache_key] = result
        
        return results
    
    async def _search_with_engine(
        self, 
        engine, 
        query: str, 
        limit: int
    ) -> List[SearchResult]:
        """Execute search with a specific engine.
        
        Args:
            engine: Search engine instance
            query: Search query
            limit: Maximum results
            
        Returns:
            List of search results
        """
        async with engine:
            return await engine.search(query, limit)
    
    def aggregate_results(
        self, 
        results: Dict[str, List[SearchResult]], 
        dedupe: bool = True
    ) -> List[SearchResult]:
        """Aggregate results from multiple engines.
        
        Args:
            results: Dictionary of engine results
            dedupe: Whether to deduplicate URLs
            
        Returns:
            Aggregated list of results
        """
        all_results: List[SearchResult] = []
        seen_urls: Set[str] = set()
        
        max_results = max(len(r) for r in results.values()) if results else 0
        
        for i in range(max_results):
            for engine_name, engine_results in results.items():
                if i < len(engine_results):
                    result = engine_results[i]
                    if dedupe:
                        normalized_url = urlparse(result.url)._replace(fragment="").geturl()
                        if normalized_url not in seen_urls:
                            seen_urls.add(normalized_url)
                            all_results.append(result)
                    else:
                        all_results.append(result)
        
        return all_results
