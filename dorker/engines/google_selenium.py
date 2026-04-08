"""Google search engine implementation using Selenium."""

import logging
import asyncio
from typing import List
from urllib.parse import urlencode

from ..models import SearchResult
from .base import SearchEngine

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

logger = logging.getLogger(__name__)


class GoogleSeleniumEngine(SearchEngine):
    """Google search engine using Selenium for better results and bypassing rate limits."""
    
    name = "google_selenium"
    
    def __init__(self, *args, **kwargs):
        """Initialize Google Selenium engine."""
        super().__init__(*args, **kwargs)
        self.driver = None
    
    async def search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search Google using Selenium.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        if not HAS_SELENIUM:
            logger.error("Selenium not installed. Install with: pip install selenium")
            return []
        
        await self.rate_limiter.wait(self.name)
        
        # Run in executor since selenium is blocking
        loop = asyncio.get_event_loop()
        try:
            results = await loop.run_in_executor(None, self._search_sync, query, limit)
            return results
        except Exception as e:
            logger.error(f"Google Selenium error: {e}")
            return []
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
    
    def _search_sync(self, query: str, limit: int) -> List[SearchResult]:
        """Synchronous search using Selenium.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of search results
        """
        results = []
        
        try:
            # Setup Chrome options
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument(f"user-agent={self.ua_rotator.get()}")
            
            # Headless mode (set to False untuk testing/debugging)
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images for faster loading
            
            # Initialize driver - use system chromedriver
            from selenium.webdriver.chrome.service import Service
            
            # Use system chromedriver (already at version 144)
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Variables for pagination
            rank_counter = 1
            start = 0
            
            while len(results) < limit:
                # Build URL dengan pagination
                url = f"https://www.google.com/search?q={query.replace(' ', '+')}&start={start}"
                
                logger.info(f"Fetching: {url}")
                self.driver.get(url)
                
                # Wait untuk page load dengan multiple retries
                import time
                time.sleep(3)  # Static wait untuk Google load properly
                
                # Try multiple selectors untuk results
                search_results = []
                try:
                    search_results = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
                except:
                    pass
                
                if not search_results:
                    try:
                        search_results = self.driver.find_elements(By.CSS_SELECTOR, "div[data-sokoban-container]")
                    except:
                        pass
                
                if not search_results:
                    logger.info("No results found on this page")
                    break
                
                page_results = 0
                
                for result_elem in search_results:
                    if len(results) >= limit:
                        break
                    
                    try:
                        # Try to extract title
                        title = ""
                        try:
                            title_elem = result_elem.find_element(By.CSS_SELECTOR, "h3")
                            title = title_elem.text
                        except:
                            pass
                        
                        # Try to extract URL
                        url_text = ""
                        try:
                            link_elem = result_elem.find_element(By.CSS_SELECTOR, "a[href^='http']")
                            url_text = link_elem.get_attribute("href")
                        except:
                            pass
                        
                        # Try to extract description
                        desc = ""
                        try:
                            desc_elem = result_elem.find_element(
                                By.CSS_SELECTOR, 
                                "div.VwiC3b, span.aCOpRe, div[data-sncf]"
                            )
                            desc = desc_elem.text
                        except:
                            pass
                        
                        # Validate result
                        if title and url_text and "http" in url_text:
                            # Filter out redirects and ads
                            if "google.com" not in url_text or "url?q=" in url_text:
                                # Clean URL if it's a redirect
                                if "url?q=" in url_text:
                                    try:
                                        url_text = url_text.split("url?q=")[1].split("&")[0]
                                    except:
                                        pass
                                
                                results.append(SearchResult(
                                    title=title,
                                    url=url_text,
                                    description=desc,
                                    engine=self.name,
                                    rank=rank_counter
                                ))
                                rank_counter += 1
                                page_results += 1
                    
                    except Exception as e:
                        logger.debug(f"Error extracting result: {e}")
                        continue
                
                # Check if we got valid results
                if page_results == 0:
                    logger.info("No valid results extracted from page")
                    break
                
                logger.info(f"Extracted {page_results} results, total: {len(results)}")
                
                # Next page
                start += 10
        
        except Exception as e:
            logger.error(f"Selenium error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
        
        return results[:limit]
