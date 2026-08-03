import csv
import time
import json
from contact_finder_sdk import ContactFinder


# 1. Define the callback function FIRST
def save_to_database(data):
    print("\n" + "="*50)
    print("✅ LIVE SUCCESS - FULL RESPONSE DATA:")
    print(json.dumps(data, indent=2))
    print("="*50 + "\n")

def read_csv(csv_path):
    with open(csv_path, mode="r", encoding="utf-8") as f:
        test_urls = [row["url"] for row in csv.DictReader(f) if row.get("url") and row["url"].strip()]
    return test_urls

if __name__ == "__main__":
    start = time.time()

    # Initialize the SDK
    finder = ContactFinder(api_key="your_rapidapi_key_here", concurrency=5, project_name="googlemaps")

    # define a url list manually
    # test_urls = ["https://www.mankindbarbersnyc.com", "https://rapidapi.com", "https://blueprintroofing.com"]

    # or read it from a file
    csv_path = "googlemaps_urls.csv"
    test_urls = read_csv(csv_path)
    test_urls = test_urls[:10]


    # 4. Run the scraper showing ALL possible parameters
    finder.run(
        # --- INPUT METHODS (Choose one) ---
        # urls=test_urls,                      # <-- ALTERNATIVE: Pass a list of URLs directly
        file_path=csv_path,                    # <-- ACTIVE: SDK reads this file directly

        # --- FILE SCHEMA (Only used if file_path is provided) ---
        url_field_name="url",                  # <-- ACTIVE: Looks for this column name in the CSV
        dedup_key="url",                       # <-- ACTIVE: Uses this key for deduplication

        # --- CORE BEHAVIOR ---
        parse_mode="raw",                      # <-- ACTIVE: Controls callback data ("raw", "contact", or "full")
        on_success=save_to_database,           # <-- ACTIVE: Callback function per successful URL
        auto_store=True,                      # <-- ACTIVE: Set to True to save outputs to disk

        # --- RAPIDAPI OVERRIDES (**api_kwargs) ---
        profile="true",                        # <-- ACTIVE: Example of overriding a default RapidAPI param
        # contact="false",                     # <-- ALTERNATIVE API KWARG
        # sources="false",                     # <-- ALTERNATIVE API KWARG
        # visuals="false",                     # <-- ALTERNATIVE API KWARG
        # meta="false"                         # <-- ALTERNATIVE API KWARG
    )

    print(f'Scraping ended in: {time.time() - start} sec..')
