# OhMyScrapper Project Context

## 🎯 Project Overview
**OhMyScrapper** is a Python-based web scraping automation framework that combines web crawling, content sniffing, AI-enhanced data enrichment, and intelligent URL classification. It enables users to discover, categorize, and extract structured data from the web at scale.

---

## 🏗️ Architecture Overview

### **Core Modules**
| Module | Responsibility | Key File(s) |
|--------|----------------|-------------|
| **URL Database** | SQLite storage with management layer | `models/db.py`, `models/urls_manager.py` |
| **URL Loading** | Extract URLs from text files | `modules/load_txt.py` |
| **URL Sniffing** | Extract meta/body tags from pages | `modules/sniff_url.py` |
| **Scraping Engine** | orchestrates full scraping workflow | `modules/scrap_urls.py` |
| **Classification** | Groups URLs by prefix patterns | `modules/classify_urls.py` |
| **AI Processing** | Auto-enrich descriptions via LLMs | `modules/process_with_ai.py` |
| **Browser Manager** | Selenium WebDriver handling | `modules/browser.py` |
| **Export/Show** | CSV/HTML export & display | `modules/show.py`, `modules/merge_dbs.py` |

### **Project Structure**
```
ohmyscrapper/
├── ohmyscrapper/          # Main module
│   ├── models/            # SQLite database layer
│   │   ├── db.py
│   │   ├── urls_manager.py
│   │   └── urls.py
│   ├── modules/           # Feature modules
│   │   ├── load_txt.py
│   │   ├── sniff_url.py
│   │   ├── scrap_urls.py
│   │   ├── process_with_ai.py
│   │   ├── classify_urls.py
│   │   ├── browser.py
│   │   ├── merge_dbs.py
│   │   └── show.py
│   └── core/              # Configuration
│       ├── config.py
│       └── config_files.py
├── tests/                 # Test suite
│   ├── __init__.py
│   └── test_*.py
├── customize/             # Legacy folder (deprecated)
└── ohmyscrapper/          # Config files
    ├── config.yaml        # Main configuration
    ├── url_types.yaml     # URL prefix mappings
    └── url_sniffing.yaml  # Sniffing rules
```

---

## 🔄 Workflow Pipeline

### **1. Initialization**
```python
# Entry point: src/ohmyscrapper/__init__.py
1. seed() → Loads url_types.yaml into DB
2. load_txt() → Extracts URLs from text files
3. classify_urls() → Groups URLs by prefix
4. scrap_urls() → Scrapes and classifies each URL
5. process_with_ai() → Enriches with AI
6. export_urls() → Generates CSV reports
```

### **2. URL Loading**
- Reads URLs from `.txt` files in directory
- Extracts from raw text content
- Adds parent_url for hierarchy
- Stores in SQLite with UUIDs

### **3. URL Sniffing Pipeline**
```python
sniff_url(url):
├── Get page source (requests or Selenium)
├── Cache with unforgettable
├── Extract meta tags (og:title, description, etc.)
├── Extract body tags (h1, h2)
├── Extract all <a> links
├── Complement with count stats
└── Return JSON report
```

### **4. Classification Logic**
```python
# Groups URLs by prefix pattern
# Example:
# url_prefix: "https://example.com/category"
# url_type: "category-pages"
# All URLs with this prefix inherit this type
```

### **5. Scraping & Processing**
```python
scrap_url(url):
├── Detect URL type (generic or custom)
├── Sniff URL for content
├── Catch exceptions → Mark as error
├── Process_sniffed_url():
│   ├── Extract title, description, destiny
│   ├── Store in DB
│   ├── Add child links from description
│   └── Add child links from page <a> tags
└── Update database state
```

---

## 🧠 Key Data Models

### **URL Database Structure**
```sql
-- urls table (simplified)
CREATE TABLE urls (
    id TEXT PRIMARY KEY,           -- UUID
    url TEXT NOT NULL,             -- Original URL
    url_destiny TEXT,              -- First extracted link
    title TEXT,                    -- Page title
    description TEXT,              -- Meta/body content
    description_links TEXT,        -- Links found in description
    url_prefix TEXT,               -- Classification prefix
    url_type TEXT,                 -- Classification type (e.g., "blog-post")
    error TEXT,                    -- Error message if failed
    touched_at DATETIME,           -- Last touched timestamp
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ai_processed TEXT              -- AI processing result
)
```

---

## 🔑 Critical API Endpoints (Main Entry)

### **src/ohmyscrapper/__init__.py:main()**
```python
# Command-line interface with subprocess
python -m ohmyscrapper start              # Full workflow
python -m ohmyscrapper start -input <file> # Load from file
python -m ohmyscrapper start --ai         # With AI processing
python -m ohmyscrapper scrap-urls         # Manual scraping
python -m ohmyscrapper sniff-url <url>    # Single URL check
python -m ohmyscrapper seed               # Initialize DB
python -m ohmyscrapper seed --reset       # Reset all URLs
python -m ohmyscrapper export             # Download CSV
python -m ohmyscrapper show               # Display in terminal
python -m ohmyscrapper classify-urls      # Re-run classifier
python -m ohmyscrapper untouch-all       # Reset classifications
```

---

## 💪 AI Integration

Located in `modules/process_with_ai.py`:

### **Supported Models**
```python
# Google
google:gemini-2.5-flash
google:<model-name>

# OpenAI
openai:gpt-4o-mini
openai:<model-name>
gpt-<any>

# Ollama (local)
ollama:llama3.2
ollama/<model-name>
```

- Google remains the default provider for unprefixed non-OpenAI model names.
- OpenAI is selected by `openai:` / `openai/` prefixes or known OpenAI model prefixes like `gpt-`.
- Ollama is selected by `ollama:` / `ollama/` prefixes and calls the local Ollama API at `http://localhost:11434/api/generate`.
- Set `OLLAMA_HOST` to override the local Ollama host.

### **AI Workflow**
```python
process_with_ai():
├── Load prompt YAML
├── Build prompt with URL text
├── Detect provider from model string
├── Call Google, OpenAI, or local Ollama API
├── Parse XML-style response
├── Update DB with AI results
├── Mark URLs as processed
└── Recursively process if more URLs exist
```

---

## 🗄️ Database & Cache

### **SQLite Tables**
1. `urls` - Main URL list with all fields
2. `ai_log` - History of AI processing sessions
3. `url_types` - Prefix to type mappings (optional)

### **Caching Layer**
- Uses `unforgettable` library for HTTP caching
- Prefix: `sniff-urf:<url>`
- Stored in `./ohmyscrapper/cache/`

---

## ⚙️ Configuration System

### **config.yaml** (Customization)
```yaml
default_dirs:
  db: ./ohmyscrapper/db
  cache: ./ohmyscrapper/cache
  output: ./ohmyscrapper/output
  input: ./ohmyscrapper/input
  prompts: ./ohmyscrapper/prompts
  report: ./ohmyscrapper/report
ai:
  api_key: ""          # LLM API key
  default_model: "gemini-2.5-flash"
  default_prompt_file: prompt.yaml
sniffing:
  use-browser: "no"
  timeout: 10
  browser-waiting-time: 2
round-sleeping: 7
```

### **url_types.yaml** (Auto-generated)
```yaml
<category>: <prefix-example>
```

### **url_sniffing.yaml** (Auto-generated)
```yaml
<type>:
  metatags:
    og:title: title
    og:description: description
  bodytags:
    h1: title
```

---

## 🛠️ Key Functions Reference

### **Core Functions**
| Function | Location | Description |
|----------|----------|-------------|
| `scrap_urls()` | `modules/scrap_urls.py` | Orchestrates scraping pipeline |
| `scrap_url()` | `modules/scrap_urls.py` | Process single URL |
| `sniff_url()` | `modules/sniff_url.py` | Extract content from URL |
| `classify_urls()` | `modules/classify_urls.py` | Group URLs by prefix |
| `process_with_ai()` | `modules/process_with_ai.py` | LLM-based enrichment |
| `load_txt()` | `modules/load_txt.py` | Load URLs from files |
| `export_urls()` | `modules/show.py` | CSV export |

### **Database Manager** (`models/urls_manager.py`)
```python
# Available methods
- get_untouched_urls()          # Get URLs to process
- set_url_error()               # Mark as failed
- set_url_title()               # Set page title
- set_url_description()         # Set description
- add_url()                     # Add new URL
- set_url_ai_processed()        # Store AI result
- get_urls_valid_prefix()       # Get URL types
- get_url_like_unclassified()   # Find similar URLs
- merge_dbs()                   # Merge multiple DBs
```

---

## ⚠️ Known Behaviors & Edge Cases

### **1. Error Handling**
- Failures caught in `scrap_url()` → Marked with error message
- Verbose mode prints suggestions
- Users can run `untouch-errors` to retry

### **2. Classification Timing**
- `classify_urls()` runs at start of session
- May need re-run if new URLs added
- Recursive mode sleeps 10s between rounds

### **3. AI Budget Control**
- Max 5 iterations by default
- Use `--i-am-rich` to bypass
- Prevents excessive API costs

### **4. Browser Fallback**
- If Selenium fails, falls back to `requests.get()`
- Configurable in `config.yaml`

---

## 🔐 Security Notes

- **API Keys** stored in `~/.env` (not shown in code)
- **Model providers** detected via string prefix
- **Timeout settings** prevent hanging requests

---

## 📄 File Output

| Output File | Description |
|-------------|-------------|
| `urls.csv` | Full data (title, description, links, etc.) |
| `urls-simplified.csv` | Compact version (only URL, title, domain) |
| `report.csv` | URLs with errors or warnings |
| `*-preview.html` | HTML preview with styling |

---

## 🚀 Performance Optimizations

1. **Caching**: `unforgettable` caches HTTP responses
2. **Batch Processing**: AI runs on multiple URLs simultaneously
3. **Recursive Scraping**: Discovers child links automatically
4. **Browser Wait**: Configurable delays to respect servers

---

## 🧪 Testing Framework

Located in `tests/`:
- `__init__.py` - Test configuration
- `test_*.py` - Individual test cases

---

## 📚 External Dependencies

| Package | Purpose |
|---------|---------|
| `selenium` | Browser automation |
| `beautifulsoup4` | HTML parsing |
| `unforgettable` | Custom caching |
| `pydantic` | Data validation |
| `pyyaml` | Config loading |
| `requests` | HTTP requests and local Ollama API calls |
| `google-genai` | Google models |
| `openai` | GPT models |

---

## 🌟 Future Enhancement Ideas

1. **Web Dashboard**: Streamlit or React UI
2. **Task Queue**: Celery + Redis for distributed scraping
3. **Browser Pool**: Multiple WebDriver instances
4. **Proxy Rotation**: Avoid IP bans
5. **Headless Mode**: Docker/Kubernetes support
6. **API Endpoint**: FastAPI wrapper for programmatic access

---

## 🤔 Potential Enhancements

1. Rate Limiting: Add configurable delays between requests
2. Error Handling: Better retry logic for failed scrapes
3. Progress Tracking: Visual progress bars for long runs
4. Cloud Integration: Deploy to AWS Lambda/GCP
5. Dashboard: Web UI to monitor scraping jobs

---
## 🧑‍💻 Development Tips

### **Adding New URL Types**
1. Edit `url_types.yaml`
2. Define new prefix/type mapping
3. `scrap-urls` will auto-categorize

### **Custom Sniffing Rules**
1. Edit `url_sniffing.yaml`
2. Add meta/body tags to extract
3. Use `+` prefix for fallback values

### **Debugging Tips**
- Use `--verbose` flag for detailed logs
- Check `cache/` folder for stale cached data
- Run `cleancache` to clear all cache

---

## 📖 Quick Start Cheat Sheet

```bash
# 1. Initialize
python -m ohmyscrapper seed

# 2. Prepare input
echo "https://example.com/page1
https://example.com/page2" > input.txt

# 3. Run scraper
python -m ohmyscrapper start -input input.txt

# 4. View results
python -m ohmyscrapper show

# 5. Export
python -m ohmyscrapper export
```

---

## 📝 Git Notes

- Check `src/` for latest code
- `customize/` is deprecated in favor of `ohmyscrapper/`
- Config files in `ohmyscrapper/` are auto-generated unless edited

---

**Last Updated**: May 2026
**Version**: 0.10.0
**Author**: @bouli
