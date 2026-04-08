# Selenium Google Search Setup Guide

## 🚀 Installation

### 1. Install Selenium dan dependencies
```bash
pip install selenium webdriver-manager
```

### 2. Install ChromeDriver
**Option A: Automatic (Recommended)**
```bash
pip install webdriver-manager
# ChromeDriver akan di-download otomatis saat pertama kali run
```

**Option B: Manual**
- Download dari https://chromedriver.chromium.org/
- Extract dan add ke PATH

### 3. Verifikasi Installation
```bash
python -c "from selenium import webdriver; print('Selenium ready!')"
```

---

## 📖 Usage

### Command Line
```bash
# Basic search dengan Google Selenium
dorker -d "site:github.com" -e google_selenium -l 50

# Compare dengan DuckDuckGo
dorker -d "site:github.com" -e duckduckgo -l 50

# Multiple engines
dorker -d "inurl:admin" -e google_selenium,duckduckgo -l 100

# Output to JSON
dorker -d "intitle:index.of" -e google_selenium --output json --file results.json
```

### Python Script
```python
import asyncio
from dorker import DorkerEngine

async def main():
    dorker = DorkerEngine()
    
    # Search dengan Google Selenium
    results = await dorker.search(
        query="site:github.com",
        engines=["google_selenium"],
        limit=50
    )
    
    for result in results.get("google_selenium", []):
        print(f"{result.url}")

asyncio.run(main())
```

---

## ⚙️ Configuration

### Optional: Use Google Selenium by default
Edit `config.yaml`:
```yaml
default_engines:
  - google_selenium
  - duckduckgo

# Rate limiting (Google Selenium needs more delay)
min_delay: 3.0
max_delay: 5.0
```

### Set default limit
```yaml
default_limit: 100
```

---

## ⚡ Performance Tips

### Speed Optimization
```bash
# Use headless mode (enabled by default, faster)
# Reduce limit if you just need quick results
dorker -d "query" -e google_selenium -l 20
```

### Resource Optimization
```bash
# Don't run too many concurrent searches
# Use single engine at a time
dorker -d "query" -e google_selenium --limit 100
```

---

## 🐛 Troubleshooting

### "selenium not installed"
```bash
pip install selenium webdriver-manager
```

### "ChromeDriver not found"
```bash
# Auto-download with webdriver-manager
pip install webdriver-manager
```

### "Connection refused"
- Make sure no other Chrome process is running
- Try restarting your system

### "Timeout waiting for results"
- Google might be blocking the request
- Try increasing delay in config
- Or switch to DuckDuckGo

### Results are empty
- Google may have rate-limited or blocked the bot
- Check if Chrome window opens (if debugging)
- Try different search query

---

## 📊 Comparison: Google Selenium vs Others

| Feature | Google Selenium | DuckDuckGo | Google Scraping |
|---------|-----------------|------------|-----------------|
| **Speed** | 🐌 Slow (5-30s) | ⚡ Fast (<1s) | ⚡⚡ Medium |
| **Bypass Rate Limit** | ✅ Yes | ✅ Yes (built-in) | ❌ No |
| **Results** | 100+ | 30+ | Limited |
| **Resource Usage** | 💾💾💾 High | 💾 Low | 💾 Low |
| **Setup** | Complex | Simple | Simple |
| **Cost** | Free | Free | Free |
| **Reliability** | ⚠️ Medium | ✅ High | ⚠️ Low |

---

## 🎯 When to Use Google Selenium

**Use when:**
- ✅ Need many Google results (100+)
- ✅ Want bypass rate limiting
- ✅ Running small-scale dorking
- ✅ Development/testing

**Don't use when:**
- ❌ Need fast results
- ❌ Large-scale operations
- ❌ Limited resources (VPS/cloud)
- ❌ Just quick lookups (use DuckDuckGo instead)

---

## 🔗 Resources

- Selenium Docs: https://www.selenium.dev/documentation/
- ChromeDriver: https://chromedriver.chromium.org/
- webdriver-manager: https://github.com/SergeyPirogov/webdriver_manager
- Dorker: [README.md](README.md)

---

## ℹ️ Note

Google Selenium engine adalah **alternative** ke scraping dan API. Untuk production use:
- Consider API services (SerpAPI, ScraperAPI)
- Or stick with DuckDuckGo (gratis, reliable, cepat)

Selenium is best untuk **testing/development** atau **small-scale research**.
