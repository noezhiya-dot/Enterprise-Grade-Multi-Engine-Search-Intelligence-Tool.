from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class SearchResult:

    title: str
    url: str
    description: str
    engine: str
    rank: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __hash__(self):
        return hash(self.url)
    
    def __eq__(self, other):
        if isinstance(other, SearchResult):
            return self.url == other.url
        return False


@dataclass
class DorkQuery:
    query: str
    engines: List[str]
    limit: int = 50
    timeout: int = 30
