import os
import csv
from contact_finder_sdk.config import config

class URLManager:
    def __init__(self, urls_file_path: str = None, field_name: str = "url", project_config=None):
        self.config = project_config if project_config is not None else config
        self.urls_file_path = urls_file_path
        self.field_name = field_name.lower()

    def normalize_url(self, url: str) -> str:
        if not url: return ""
        url = url.strip().lower().split("://", 1)[-1].rstrip("/")
        return url[4:] if url.startswith("www.") else url

    def load_urls(self, path: str = None) -> list[str]:
        path = path or self.urls_file_path or self.config.URLS_FILE_PATH
        if not path: return []

        # CRITICAL FIX: Resolve to absolute path to prevent working directory bugs
        abs_path = os.path.abspath(path)
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"SDK cannot find file: {abs_path}")
        path = abs_path

        # Fix 1: Use 'with' for .txt files
        if path.endswith(".txt"):
            with open(path, encoding="utf-8") as f:
                return [l.strip() for l in f if l.strip()]

        # Fix 2: Use 'with' for .csv files (utf-8-sig handles Excel BOM)
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))

        if not rows: return []

        header = [h.strip().lower() for h in rows[0]]
        field = self.field_name
        col = header.index(field) if field in header else 0
        body = rows[1:] if field in header else rows
        return [r[col].strip() for r in body if len(r) > col and r[col].strip()]

    def ensure_data_dir(self) -> None:
        os.makedirs(self.config.DATA_DIR, exist_ok=True)
        # os.makedirs(self.config.URLS_DIR, exist_ok=True)

    @staticmethod
    def remove_duplicates(items: list[str]) -> list[str]:
        """Removes exact duplicate strings while preserving original order."""
        return list(dict.fromkeys(i for i in items if i))
