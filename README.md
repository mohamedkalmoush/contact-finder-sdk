# 🕵️ Contact Finder SDK

[![PyPI version](https://img.shields.io/badge/pypi-v1.0.0-blue.svg)](https://pypi.org/project/contact-finder-sdk/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust, high-concurrency async Python SDK for the **Website Contact Finder API**. Effortlessly scrape emails, phone numbers, social media links, and rich company metadata from thousands of websites.

## ✨ Key Features

* 🚀 **Async & High Concurrency:** Processes hundreds of URLs simultaneously using `asyncio` and `aiohttp`.
* 🗂️ **Multi-Project Isolation:** Run multiple scrapers at once. Each `project_name` gets its own isolated data folder.
* 🔄 **Smart Deduplication & Caching:** Automatically skips URLs it has already scraped and resumes where it left off.
* 💾 **Auto-Storage:** Automatically saves results to structured `.jsonl` and `.csv` files.
* 🪝 **Real-time Callbacks:** Pass an `on_success` function to process data instantly as it arrives.

---

## 📦 Installation

```bash
pip install contact-finder-sdk
```

## 🔑 Prerequisites

You need a RapidAPI key to use this SDK.
1. Go to the [Website Contact Finder API on RapidAPI](https://rapidapi.com/).
2. Subscribe to the API and copy your `X-RapidAPI-Key`.

---

## 🚀 Quick Start (The Simplest Way)

The easiest way to use the SDK is to pass a Python list of URLs directly.

```python
from contact_finder_sdk import ContactFinder

# Define what happens when a URL is successfully scraped
def handle_result(data):
    url = data.get("url") or data.get("data", {}).get("url")
    print(f"✅ Successfully scraped: {url}")

# Initialize the SDK
finder = ContactFinder(
    api_key="YOUR_RAPIDAPI_KEY_HERE", 
    project_name="quick_test"
)

# Run the scraper
finder.run(
    urls=["https://rapidapi.com", "https://github.com"],
    parse_mode="contact",       # Extracts emails, phones, and socials
    on_success=handle_result,   # Triggered for every success
    auto_store=True             # Saves results to a local 'data/' folder
)
```

---

## 📂 Reading from a CSV File

If you have a large list of URLs, pass a CSV file instead. The SDK will automatically read the file, extract the URLs, and process them.

```python
finder.run(
    file_path="my_urls.csv",    # Path to your CSV file
    url_field_name="url",       # The name of the column containing the URLs
    parse_mode="full",          # Gets contact + profile + visuals + meta
    auto_store=True
)
```

---

## 🗂️ Multi-Project Isolation

One of the most powerful features is **Project Isolation**. If you are managing multiple clients or campaigns, simply assign a different `project_name` to each instance. 

The SDK will automatically create separate, isolated folders for each project inside a local `data/` directory. Their caches, CSVs, and logs will never mix.

```python
# Instance 1: Client A
finder_a = ContactFinder(api_key="YOUR_KEY", project_name="client_A")
finder_a.run(urls=["https://client-a.com"], auto_store=True)
# Saves to: ./data/client_A/

# Instance 2: Client B
finder_b = ContactFinder(api_key="YOUR_KEY", project_name="client_B")
finder_b.run(urls=["https://client-b.com"], auto_store=True)
# Saves to: ./data/client_B/
```

---

## ⚙️ Configuration Parameters

When calling `finder.run()`, you can customize the behavior:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `urls` | `list[str]` | `None` | A direct list of URLs to scrape. |
| `file_path` | `str` | `None` | Path to a `.csv` or `.txt` file containing URLs. |
| `url_field_name`| `str` | `"url"` | The column name to look for if using a CSV file. |
| `dedup_key` | `str` | `"url"` | The key used to check for duplicates. |
| `parse_mode` | `str` | `"raw"` | How to format the callback data (`"raw"`, `"contact"`, or `"full"`). |
| `on_success` | `Callable`| `None` | A function to execute immediately when a URL succeeds. |
| `auto_store` | `bool` | `True` | If `True`, saves outputs to local `.jsonl` and `.csv` files. |
| `**api_kwargs` | `kwargs` | `{}` | Override default RapidAPI params (e.g., `profile="false"`). |

### 🔍 Parse Modes Explained

* **`"raw"`**: Returns the exact, untouched JSON dictionary from the RapidAPI response.
* **`"contact"`**: Returns a flattened dictionary containing only core contact info (Emails, Phones, Social Media links).
* **`"full"`**: Returns a massive flattened dictionary containing Contact info + Company Profile + Visuals + Meta tags.

---

## 💾 Output Files

When `auto_store=True`, the SDK generates a `data/<project_name>/` folder containing:

| File | Description |
| :--- | :--- |
| `full.jsonl` | The master database of all parsed, flattened records. |
| `raw.jsonl` | A cache of the raw API responses (used to prevent re-scraping). |
| `full.csv` | A spreadsheet version of the master database. |
| `contact.csv`| A lightweight spreadsheet with only contact info. |
| `failed.log` | A log of URLs that failed to scrape, with error reasons. |

*Note: The SDK is resumable. If your script crashes, simply run it again. It will read `raw.jsonl`, skip the URLs it already finished, and pick up exactly where it left off!*

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
