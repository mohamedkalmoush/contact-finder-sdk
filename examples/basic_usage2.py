import csv
import time
import json
from contact_finder_sdk import ContactFinder

# ── SIMPLE API KEY SETUP ─────────────────────────────────────────────────────
# 1. To test locally: Paste your REAL key here, save, and run the script.
API_KEY = "YOUR_RAPIDAPI_KEY_HERE"

# ── LIST A (15 URLs) ─────────────────────────────────────────────────────────
urls_a = [
    "https://www.aaastandardroofing.com", "https://str8aboveroofing.com",
    "https://aceroofingsf.com", "http://www.barnhouseexteriors.com",
    "http://www.isaacsroofing.com", "http://a-classroofrepairs.com",
    "https://www.abetterroofing.com", "https://roofmaxx.com/find-a-dealer/california/poway",
    "https://agroofmiami.com/locations/miami", "https://bastosroofing.com",
    "https://blueprintroofing.com", "http://www.camachocontractors.com",
    "https://www.atlantametroroofing.com", "https://www.craddockroofing.com",
    "https://atlanticexproofing.com/locations/miami",
]

# ── LIST B (15 URLs) ─────────────────────────────────────────────────────────
urls_b = [
    "http://www.eliteroofingservices.com", "http://www.exceptionalexteriorsil.com",
    "http://www.capstoneroofingaz.com", "https://ar1roofing.com/location/miami",
    "http://www.rtiservicesinc.com", "https://www.commercialroofinglosangeles.net",
    "https://www.rencoroofing.com", "https://www.myftconstruction.com",
    "https://www.realroofingofficial.com", "https://vertexroofing.com",
    "https://www.advancedroofinghouston.com", "https://tims-emergency-roofing-houston.ueniweb.com",
    "https://hermeticaroofing.com", "https://sundanceroofingofsfl.com/locations/miami",
    "https://stellarroofingandsolar.com",
]

CSV_A_PATH = "urls_project_a.csv"
CSV_B_PATH = "urls_project_b.csv"

# ── CHOOSE WHAT TO TEST: "lists", "csv", or "both" ───────────────────────────
TEST_MODE = "both"

def write_csv(path, urls):
    """Creates a CSV file with a 'url' header column."""
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url"])
        for u in urls:
            writer.writerow([u])
    print(f"📄 Created {path} with {len(urls)} urls")

def read_csv(csv_path):
    with open(csv_path, mode="r", encoding="utf-8") as f:
        return [row["url"] for row in csv.DictReader(f) if row.get("url") and row["url"].strip()]

def save_to_database(data):
    url = (data or {}).get("url") or ((data or {}).get("data") or {}).get("url", "unknown")
    print(f"✅ LIVE SUCCESS: {url}")

if __name__ == "__main__":
    start = time.time()

    # 1. Auto-generate the two CSV files on disk
    write_csv(CSV_A_PATH, urls_a)
    write_csv(CSV_B_PATH, urls_b)

    # Sanity check
    print(f"read_csv check → A: {len(read_csv(CSV_A_PATH))} urls | B: {len(read_csv(CSV_B_PATH))} urls\n")

    # 2. TEST WITH MANUAL LISTS
    if TEST_MODE in ("lists", "both"):
        print("\n--- TEST 1: MANUAL LISTS (project_A + project_B) ---")
        finder_a = ContactFinder(api_key=API_KEY, concurrency=5, project_name="project_A")
        finder_a.run(urls=urls_a, parse_mode="raw", on_success=save_to_database, auto_store=True, profile="true")
        print(f"📂 project_A master file: {finder_a.storage.jsonl_path}")

        finder_b = ContactFinder(api_key=API_KEY, concurrency=5, project_name="project_B")
        finder_b.run(urls=urls_b, parse_mode="raw", on_success=save_to_database, auto_store=True, profile="true")
        print(f"📂 project_B master file: {finder_b.storage.jsonl_path}")

    # 3. TEST WITH CSV FILES
    if TEST_MODE in ("csv", "both"):
        print("\n--- TEST 2: CSV FILES (project_C + project_D) ---")
        finder_c = ContactFinder(api_key=API_KEY, concurrency=5, project_name="project_C")
        finder_c.run(file_path=CSV_A_PATH, url_field_name="url", dedup_key="url",
                     parse_mode="raw", on_success=save_to_database, auto_store=True, profile="true")
        print(f"📂 project_C master file: {finder_c.storage.jsonl_path}")

        finder_d = ContactFinder(api_key=API_KEY, concurrency=5, project_name="project_D")
        finder_d.run(file_path=CSV_B_PATH, url_field_name="url", dedup_key="url",
                     parse_mode="raw", on_success=save_to_database, auto_store=True, profile="true")
        print(f"📂 project_D master file: {finder_d.storage.jsonl_path}")

    print(f'\nTotal test time: {time.time() - start:.2f} sec..')
