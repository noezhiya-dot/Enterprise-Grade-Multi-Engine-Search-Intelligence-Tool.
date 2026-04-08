"""Search engine registry and exports."""

from .base import SearchEngine
from .google import GoogleEngine
from .bing import BingEngine
from .duckduckgo import DuckDuckGoEngine
from .yahoo import YahooEngine
from .yandex import YandexEngine
from .brave import BraveEngine
from .ask import AskEngine

try:
    from .google_selenium import GoogleSeleniumEngine
    HAS_GOOGLE_SELENIUM = True
except ImportError:
    HAS_GOOGLE_SELENIUM = False
    GoogleSeleniumEngine = None

__all__ = [
    "SearchEngine",
    "GoogleEngine",
    "BingEngine",
    "DuckDuckGoEngine",
    "YahooEngine",
    "YandexEngine",
    "BraveEngine",
    "AskEngine",
]

ENGINES_MAP = {
    "google": GoogleEngine,
    "bing": BingEngine,
    "duckduckgo": DuckDuckGoEngine,
    "yahoo": YahooEngine,
    "yandex": YandexEngine,
    "brave": BraveEngine,
    "ask": AskEngine,
}

# Add Google Selenium if available
if HAS_GOOGLE_SELENIUM:
    ENGINES_MAP["google_selenium"] = GoogleSeleniumEngine
    __all__.append("GoogleSeleniumEngine")

