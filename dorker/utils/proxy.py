"""Proxy rotation utility."""

from typing import List, Optional


class ProxyRotator:
    """Manages proxy rotation across requests."""
    
    def __init__(self, proxies: List[str] = None):
        """Initialize proxy rotator.
        
        Args:
            proxies: List of proxy URLs to rotate through
        """
        self.proxies = proxies or []
        self.index = 0
    
    def get_proxy(self) -> Optional[str]:
        """Get next proxy from rotation.
        
        Returns:
            Proxy URL or None if no proxies configured
        """
        if not self.proxies:
            return None
        proxy = self.proxies[self.index % len(self.proxies)]
        self.index += 1
        return proxy
