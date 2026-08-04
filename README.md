# 🕵️ Contact Finder SDK

[![PyPI version](https://img.shields.io/badge/pypi-v1.0.0-blue.svg)](https://pypi.org/project/contact-finder-sdk/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust, high-concurrency async Python SDK for the **Website Contact Finder API**. Effortlessly scrape emails, phone numbers, social media links, and rich company metadata from thousands of websites.

## ✨ Key Features

* 🚀 **Async & High Concurrency:** Processes hundreds of URLs simultaneously using `asyncio` and `aiohttp`.
* 🗂️ **Multi-Project Isolation:** Run multiple scrapers at once. Each `project_name` gets its own isolated data folder.
* 🔄 **Smart Deduplication & Caching:** Automatically skips URLs it has already scraped and resumes where it left off.
* 💾 **Batteries-Included Auto-Storage:** Automatically saves results to beautifully structured `.json` and `.csv` files.
* 🪝 **Real-time Callbacks:** Pass an `on_success` function to process data instantly as it arrives (if you want to).

---

## 📦 Installation

```bash
pip install contact-finder-sdk
```

## 🔑 Prerequisites & API Key Setup

This SDK connects to the [**Website Contact Finder**](https://rapidapi.com/scrapeeg/api/website-contact-finder) API hosted on RapidAPI. You will need an API key to start scraping.

**1. Subscribe to the Free Plan**
Visit our [RapidAPI Pricing Page](https://rapidapi.com/scrapeeg/api/website-contact-finder/pricing).
* Click **"Subscribe"** or **"Start Free Plan"**.
* Log in to RapidAPI (using "Continue with Google" is the fastest).
* Select the **Free Plan** (usually the first one on the left) and click **"Subscribe"** in the top right corner. *(No credit card required!)*

**2. Copy Your API Key**
Once subscribed, go to the **Endpoints** tab on the API dashboard. Click on any endpoint, and look at the code snippet on the right side of the screen. Copy the long string value for `x-rapidapi-key`.

> 💡 **Need help?** If you get stuck or have questions about the API, message me directly on [WhatsApp](https://api.whatsapp.com/send?phone=201141843921) or [Telegram](https://t.me/MohamedKalmoush) and I'll walk you through it personally!

---

## 🚀 Quick Start (The "WTF, Is That It?" Way)

We believe the best SDKs get out of your way. You don't need to write loops, handle callbacks, or manually parse and save files. 

Just pass your URLs, and the SDK automatically scrapes, extracts emails/phones/socials, and drops perfectly formatted `.csv` and `.json` files into a folder named after your project.

```python
from contact_finder_sdk import ContactFinder

target_urls = ["https://rapidapi.com", "https://github.com"]

# 1. Initialize with your credentials and project name
finder = ContactFinder(api_key="YOUR_RAPIDAPI_KEY", concurrency=5, project_name="my_first_scrape")

# 2. Pass the URLs. The SDK does everything else.
finder.run(urls=target_urls)
```

> 🎉 **That's really it.** Under the hood, the SDK handles high-concurrency async scraping, deduplication, and automatically generates `contacts.csv`, `contacts.json`, and a raw cache inside a local `./my_first_scrape/` directory.

---

## 📂 Reading from a CSV File

If you have a massive list of URLs, you don't need to load them into a Python list first. Just pass a CSV file. The SDK will automatically read the file, extract the URLs, and process them.

```python
finder.run(
    urls=None,                  # Not needed when using a file
    file_path="my_urls.csv",    # Path to your CSV file
    url_field_name="url",       # The name of the column containing the URLs
    parse_mode="full",          # Gets contact + profile + visuals + meta
)
```

---

## 🗂️ Multi-Project Isolation

One of the most powerful features is **Project Isolation**. If you are managing multiple clients or campaigns, simply assign a different `project_name` to each instance. 

The SDK will automatically create separate, isolated folders for each project inside a local directory. Their caches, CSVs, and logs will never mix.

```python
# Instance 1: Client A
finder_a = ContactFinder(api_key="YOUR_KEY", project_name="client_A")
finder_a.run(urls=["https://client-a.com"])
# Automatically saves to: ./client_A/

# Instance 2: Client B
finder_b = ContactFinder(api_key="YOUR_KEY", project_name="client_B")
finder_b.run(urls=["https://client-b.com"])
# Automatically saves to: ./client_B/
```

---

## ⚙️ Advanced Configuration

The Quick Start uses smart defaults. But if you want more control over the output and behavior, `finder.run()` accepts several optional parameters:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `urls` | `list[str]` | `None` | A direct list of URLs to scrape. |
| `file_path` | `str` | `None` | Path to a `.csv` or `.txt` file containing URLs. |
| `url_field_name`| `str` | `"url"` | The column name to look for if using a CSV file. |
| `dedup_key` | `str` | `"url"` | The key used to check for duplicates. |
| `parse_mode` | `str` | `"contact"`| How to format the callback data (`"raw"`, `"contact"`, or `"full"`). |
| `on_success` | `Callable`| `None` | A function to execute immediately when a URL succeeds. |
| `auto_store` | `bool` | `True` | If `True`, automatically saves outputs to local files. |
| `**api_kwargs` | `kwargs` | `{}` | Override default RapidAPI params (e.g., `profile="false"`). |

### 🔍 Parse Modes Explained

* **`"contact"` (Default)**: Returns a flattened dictionary containing only core contact info (Emails, Phones, Social Media links).
* **`"full"`**: Returns a massive flattened dictionary containing Contact info + Company Profile + Visuals + Meta tags.
* **`"raw"`**: Returns the exact, untouched JSON dictionary from the RapidAPI response.

---

## 💾 Output Files

When `auto_store=True` (which is the default), the SDK generates a `<project_name>/` folder containing:

| File | Description |
| :--- | :--- |
| `contacts.json` | The master database of all parsed, flattened records. |
| `raw.jsonl` | A cache of the raw API responses (used to prevent re-scraping). |
| `contacts.csv` | A spreadsheet version of the master database. |
| `failed.log` | A log of URLs that failed to scrape, with error reasons. |

*Note: The SDK is resumable. If your script crashes, simply run it again. It will read the cache, skip the URLs it already finished, and pick up exactly where it left off!*

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
