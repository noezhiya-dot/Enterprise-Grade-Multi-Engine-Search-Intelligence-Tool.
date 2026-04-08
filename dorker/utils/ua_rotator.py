"""User-Agent rotation utility."""

import random
from typing import Optional

try:
    from fake_useragent import UserAgent
except ImportError:
    UserAgent = None


class UserAgentRotator:
    """Manages user-agent rotation to avoid detection."""
    
    def __init__(self):
        """Initialize user-agent rotator with fallback agents."""
        try:
            self.ua = UserAgent()
        except:
            self.ua = None
        
        self.fallback_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ]
    
    def get(self) -> str:
        """Get a random user-agent string.
        
        Returns:
            Random user-agent string from library or fallback list
        """
        if self.ua:
            try:
                return self.ua.random
            except:
                pass
        return random.choice(self.fallback_agents)
