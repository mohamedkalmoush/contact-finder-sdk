import os
import aiohttp


# ── RapidAPI SDK Settings (For your users) ──────────────────────────────────
RAPIDAPI_HOST = "website-contact-finder.p.rapidapi.com"
RAPIDAPI_URL = f"https://{RAPIDAPI_HOST}/"

# RapidAPI expects string "false"/"false" for these params -- currently not being used
RAPIDAPI_DEFAULT_PARAMS = {
    "contact": "true",
    "sources": "true",
    "profile": "true",
    "visuals": "true",
    "meta": "true"
}

# ── Concurrency & Retry Settings ─────────────────────────────────────────────
CONCURRENCY = 30
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 2
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)
TRANSIENT_ERROR_PHRASES = ["timeout", "rate limit", "too many requests", "service unavailable", "502", "503", "504"]


# --- DYNAMIC PATHS (The Class) ---
class Config:
    def __init__(self):
        # self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.BASE_DIR = os.getcwd()
        self.PROJECT_NAME = "default_project"
        self._update_paths()
        # self.PROJECT_NAME = None


    def _update_paths(self):
        self.DATA_DIR = os.path.join(self.BASE_DIR, "data", self.PROJECT_NAME)
        # os.makedirs(self.DATA_DIR, exist_ok=True)
        self.FULL_JSONL_PATH = os.path.join(self.DATA_DIR, "full.jsonl")
        self.RAW_JSONL_PATH = os.path.join(self.DATA_DIR, "raw.jsonl")
        self.FULL_CSV_PATH = os.path.join(self.DATA_DIR, "full.csv")
        self.CONTACT_CSV_PATH = os.path.join(self.DATA_DIR, "contact.csv")
        self.FAILED_LOG_PATH = os.path.join(self.DATA_DIR, "failed.log")

        # Input file config (MOVED HERE so it updates when project changes)
        self.URLS_DIR = os.path.join(self.BASE_DIR, "urls", self.PROJECT_NAME)
        # os.makedirs(self.URLS_DIR, exist_ok=True)
        self.URLS_FILE_PATH = os.path.join(self.URLS_DIR, "urls.csv")
        self.URL_FIELD_NAME = "url"
        self.DEDUP_KEY = "url"

    def set_project(self, name: str):
        name = name or "default_project"
        if self.PROJECT_NAME != name:  # Only update if it's actually a new project
            self.PROJECT_NAME = name
            self._update_paths()


# Instantiate it so other files can import it
config = Config()
