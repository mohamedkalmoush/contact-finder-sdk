# 🕵️ Contact Finder SDK

[![PyPI version](https://img.shields.io/pypi/v/contact-finder-sdk.svg)](https://pypi.org/project/contact-finder-sdk/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust, high-concurrency async Python SDK for the **Website Contact Finder API**. Effortlessly scrape emails, phone numbers, social media links, and rich company metadata from thousands of websites.

## ✨ Key Features

* 🚀 **Async & High Concurrency:** Processes hundreds of URLs simultaneously using `asyncio` and `aiohttp`.
* 🛡️ **Crash-Proof Resumability:** Caches raw API responses locally. If your script crashes, it resumes exactly where it left off without wasting your API credits.
* 🔄 **Self-Healing Storage:** Automatically detects missing files and rebuilds them. If you delete a CSV, it rebuilds it from the JSONL. If you delete the JSONL, it rebuilds it from the CSV.
* 📊 **Dynamic CSV Headers:** Uses atomic file rewrites to dynamically add new columns if the API returns unexpected fields, without corrupting existing data.
* 🗂️ **Multi-Project Isolation:** Run multiple scrapers at once. Each `project_name` gets its own isolated data folder.
* 🧠 **Smart Callback Routing:** Triggers your `on_success` callbacks instantly for cached URLs without making redundant API calls.

---

## 📦 Installation

```bash
pip install contact-finder-sdk
```

## 🔑 Prerequisites & API Key Setup

You can use this SDK with our **Direct Website API** (recommended) or via **RapidAPI**. 

### Option 1: Direct Website API (Fastest)
Skip the RapidAPI dashboard entirely. You can get a key directly from our website.
1. Visit **[scrapeeg.org/signup](https://scrapeeg.org/signup)** to create a free account.
2. You get **250 free credits** instantly (no credit card required).
3. Go to your Dashboard, click **"Create API key"**, and copy the key.

---

### Option 2: RapidAPI
This SDK also connects to the [**Website Contact Finder**](https://rapidapi.com/scrapeeg/api/website-contact-finder) API hosted on RapidAPI.

**1. Subscribe to the Free Plan**
Visit our [RapidAPI Pricing Page](https://rapidapi.com/scrapeeg/api/website-contact-finder/pricing).
* Click **"Subscribe"** or **"Start Free Plan"**.
* Log in to RapidAPI (using "Continue with Google" is the fastest).
* Select the **Free Plan** (usually the first one on the left) and click **"Subscribe"** in the top right corner. *(No credit card required!)*

**2. Copy Your API Key**
Once subscribed, go to the **Endpoints** tab on the API dashboard. Click on any endpoint, and look at the code snippet on the right side of the screen. Copy the long string value for `x-rapidapi-key`.

> 💡 **Need help?** If you get stuck or have questions about the API, message me directly on [WhatsApp](https://api.whatsapp.com/send?phone=201141843921) or [Telegram](https://t.me/MohamedKalmoush) and I'll walk you through it personally!

---

## 🚀 Quick Start (Zero Configuration Required)

We designed this SDK to get out of your way. You don't need to write loops, handle callbacks, or manually parse and save files. 

Just pass your URLs, and the SDK automatically scrapes, extracts emails/phones/socials, and drops perfectly formatted files into a folder named after your project.

```python
from contact_finder_sdk import ContactFinder

target_urls = ["https://rapidapi.com", "https://github.com"]

# Option 1: Using the Direct Website API (Default)
finder = ContactFinder(api_key="sk_live_YOUR_WEBSITE_KEY", source="website", concurrency=5, project_name="my_first_scrape")

# Option 2: Using RapidAPI (Uncomment to use)
# finder = ContactFinder(api_key="YOUR_RAPIDAPI_KEY", source="rapidapi", concurrency=5, project_name="my_first_scrape")

# Pass the URLs. The SDK handles everything else automatically.
finder.run(urls=target_urls)
```

---

## 📁 Understanding Your Output Files

As soon as the Quick Start finishes, you will notice a new folder in your directory: `./data/my_first_scrape/`. 

Because `auto_store=True` by default, the SDK automatically generates the following beautifully structured files:

| File | Description |
| :--- | :--- |
| `full.jsonl` | **The Master Database.** Contains all parsed, flattened records. |
| `raw.jsonl` | **The Cache.** Raw API responses used to prevent re-scraping. |
| `full.csv` | A spreadsheet version of the master database. |
| `contact.csv`| A lightweight spreadsheet with only core contact info (Emails, Phones, Socials). |
| `failed.log` | A log of URLs that failed to scrape, with error reasons and timestamps. |

### 🛡️ Data Safety & Resumability
You don't need to worry about data corruption or crashing scripts:
1. **Auto-Rebuilding:** If you accidentally delete `full.csv`, the SDK detects it on the next run and automatically rebuilds it from `full.jsonl`. If you delete the JSONL, it rebuilds it from the CSV.
2. **Dynamic Headers:** If the API returns a brand new field that wasn't in your original CSV header, the SDK uses atomic file rewrites to dynamically add the new column without corrupting your existing rows.
3. **Resumability:** If your script crashes halfway through, simply run it again. It reads `raw.jsonl`, skips the URLs it already finished, and picks up exactly where it left off.

---

## 📂 Reading from a CSV or TXT File

If you have a massive list of URLs, you don't need to load them into a Python list first. Just pass a `.csv` or `.txt` file. The SDK will automatically read the file, extract the URLs, and process them.

```python
finder.run(
    file_path="my_urls.csv",    # Path to your CSV or TXT file
    url_field_name="url",       # The name of the column containing the URLs
)
```

---

## 🗂️ Multi-Project Isolation

One of the most powerful features is **Project Isolation**. If you are managing multiple clients or campaigns, simply assign a different `project_name` to each instance. 

The SDK will automatically create separate, isolated folders for each project inside a local `./data/` directory. Their caches, CSVs, and logs will never mix.

```python
# Instance 1: Client A
finder_a = ContactFinder(api_key="YOUR_KEY", project_name="client_A")
finder_a.run(urls=["https://client-a.com"])
# Automatically saves to: ./data/client_A/

# Instance 2: Client B
finder_b = ContactFinder(api_key="YOUR_KEY", project_name="client_B")
finder_b.run(urls=["https://client-b.com"])
# Automatically saves to: ./data/client_B/
```

---

## 🪝 Real-time Callbacks & Data Parsing

Want to save data directly to your database as it arrives? Pass an `on_success` callback. 

**Smart Routing:** If the SDK finds a URL in its local cache, it *skips the API call* (saving your API credits) but **still instantly triggers your callback** with the cached data!

```python
def save_to_my_db(data):
    print(f"✅ Scraped {data.get('domain')}")
    print(f"📧 Emails: {data.get('emails')}")

finder.run(
    urls=["https://rapidapi.com"],
    parse_mode="contact",       # Controls what data is passed to your callback
    on_success=save_to_my_db    # Triggered for BOTH new and cached URLs
)
```

### 🔍 Parse Modes Explained
* **`"contact"`**: Returns a flattened dictionary containing only core contact info (Emails, Phones, Social Media links). *Highly recommended for `on_success` callbacks.*
* **`"full"`**: Returns a massive flattened dictionary containing Contact info + Company Profile + Visuals + Meta tags.
* **`"raw"` (Default)**: Returns the exact, untouched JSON dictionary from the API response.

---

## ⚡ Advanced: Streaming Data & Payload Optimization

By default, `auto_store=True` and all API extraction flags (`profile`, `visuals`, `meta`) are set to `"true"`. This fetches *everything* and safely writes it to local CSV/JSONL files, which is the recommended approach for most users.

However, if you are building a high-volume pipeline and only need to stream data directly into your database via `on_success`, you can optimize your workflow in two ways:

**💡 Pro-Tip for High-Volume Pipelines:**
1. **Speed up your local workflow:** Set `auto_store=False`. Bypassing local file generation eliminates disk I/O, significantly speeding up your Python script's execution when you only need the `on_success` callback.
2. **Reduce payload size & save bandwidth:** Change the extraction flags (`profile`, `visuals`, `meta`) to `"false"`. This tells the API to skip heavy extraction, drastically reducing the API response payload size and saving massive amounts of **bandwidth** when processing millions of requests. *(Note: This reduces network transfer size, but does not significantly speed up the API's internal scraping time).*

```python
finder.run(
    urls=target_urls,
    on_success=save_to_my_db,   # Process data in real-time
    auto_store=True,            # Default: True. Set to False to skip disk I/O and speed up execution.
    parse_mode="contact",       # Default: "raw". Use "contact" for emails/phones.
    
    # API Overrides (Defaults are all "true" to fetch complete data for auto_store)
    # Change these to "false" to reduce response payload size and save bandwidth:
    profile="true",             # Default: "true". Set to "false" to skip company profile extraction.
    visuals="true",             # Default: "true". Set to "false" to skip image/logo extraction.
    meta="true"                 # Default: "true". Set to "false" to skip meta tag extraction.
)
```

---

## ⚙️ Complete Configuration Reference

The Quick Start uses smart defaults that work perfectly for 95% of use cases. But if you want granular control, `finder.run()` accepts the following parameters:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `urls` | `list[str]` | `None` | A direct list of URLs to scrape. |
| `file_path` | `str` | `None` | Path to a `.csv`, `.tsv`, `.txt`, `.json`, or `.jsonl` file containing URLs. |
| `url_field_name` | `str` | `"auto"` | The name of the column holding URLs. If omitted, the SDK tries to detect it automatically. |
| `dedup_key` | `str` | `"url"` | The key used to check for duplicates. |
| `parse_mode` | `str` | `"raw"` | How to format the callback data (`"raw"`, `"contact"`, or `"full"`). |
| `on_success` | `Callable`| `None` | A function to execute immediately when a URL succeeds. |
| `auto_store` | `bool` | `True` | If `True`, automatically saves outputs to local files. |
| `**api_kwargs` | `kwargs` | `{}` | Override default API params (e.g., `profile="false"`). |

*(Note: `api_key` and `source` (choose `"website"` or `"rapidapi"`) are passed to the `ContactFinder()` constructor, not `finder.run()`).*

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
