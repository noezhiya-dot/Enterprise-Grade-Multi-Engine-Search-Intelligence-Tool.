"""Dorker - Enterprise Multi-Search Engine Dorking Tool."""

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "Enterprise-grade tool for performing Google dork queries across multiple search engines"

from .core import DorkerEngine
from .models import SearchResult, DorkQuery
from .output import OutputFormatter
from .cli import DorkerCLI, main

__all__ = [
    "DorkerEngine",
    "SearchResult",
    "DorkQuery",
    "OutputFormatter",
    "DorkerCLI",
    "main",
    "__version__",
]
