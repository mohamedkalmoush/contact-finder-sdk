import os
import csv
import json
import tempfile
import time
from contact_finder_sdk.config import config
from contact_finder_sdk.parsers import ResponseParser
from contact_finder_sdk.utils import URLManager

url_mgr = URLManager()

class DummyCSVWriter:
    """No-op writer used when auto_store=False."""
    def writerow(self, row: dict) -> None:
        pass

# ── CSV helpers ───────────────────────────────────────────────────────────────
class CSVWriter:
    def __init__(self, path: str, csv_fields: list[str] = None):
        self.path = path
        self.csv_fields = csv_fields or []
        self.header = self._load_or_init_header()

    def _load_or_init_header(self) -> list[str]:
        if not os.path.isfile(self.path):
            self._write_fresh_header(); return list(self.csv_fields)
        with open(self.path, newline="", encoding="utf-8") as f:
            header = list(next(csv.reader(f), None) or [])
        new_fields = [k for k in self.csv_fields if k not in header]
        if new_fields: header.extend(new_fields); self._atomic_rewrite(header)
        return header

    def _write_fresh_header(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, mode="w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(self.csv_fields)

    def _atomic_rewrite(self, header: list[str]) -> None:
        rows = []
        if os.path.isfile(self.path):
            with open(self.path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        dir_name = os.path.dirname(self.path) or "."
        with tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8", dir=dir_name, delete=False, suffix=".tmp") as tmp:
            tmp_path = tmp.name
            writer = csv.DictWriter(tmp, fieldnames=header, extrasaction="ignore")
            writer.writeheader(); writer.writerows(rows)
        os.replace(tmp_path, self.path)

    def writerow(self, row: dict) -> None:
        new_fields = [k for k in row if k not in self.header]
        if new_fields:
            self.header.extend(new_fields); self._atomic_rewrite(self.header)
        with open(self.path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.header, extrasaction="ignore", restval="")
            writer.writerow(row); f.flush()

# ── Storage Manager Class ─────────────────────────────────────────────────────
class StorageManager:
    def __init__(self, dedup_key: str = "url", auto_store=True, project_config=None):
        self.auto_store = auto_store
        self.dedup_key = dedup_key.lower()

        cfg = project_config if project_config is not None else config

        # Dynamically fetch the LIVE paths from the config object
        self.jsonl_path = cfg.FULL_JSONL_PATH
        self.raw_jsonl_path = cfg.RAW_JSONL_PATH
        self.full_csv_path = cfg.FULL_CSV_PATH
        self.contact_csv_path = cfg.CONTACT_CSV_PATH
        self.failed_log_path = cfg.FAILED_LOG_PATH


    def read_jsonl(self, file_path: str = None) -> list[dict]:
        """Reads a JSONL file. Defaults to main JSONL, but accepts a custom path (like raw_jsonl_path)."""
        path = file_path or self.jsonl_path
        if not self.auto_store: return []
        if not os.path.isfile(path): return []
        records: list[dict] = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                stripped_line: str = line.strip()
                if not stripped_line: continue
                try: records.append(json.loads(stripped_line))
                except json.JSONDecodeError: continue
        return records

    def append_to_jsonl(self, record: dict, file_path: str = None) -> None:
        """Append one record as a JSON line. Defaults to main JSONL, but accepts a custom path."""
        path = file_path or self.jsonl_path
        if not self.auto_store: return
        with open(path, mode="a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n"); f.flush()

    def log_failed_url(self, url: str, reason: str) -> None:
        if not self.auto_store: return
        with open(self.failed_log_path, mode="a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{url}\t{reason}\n"); f.flush()

    # ── Startup: mutual rebuild between JSONL and CSV ─────────────────────────────
    def build_seen_and_sync_files(self, full_csv_fields: list[str], contact_csv_fields: list[str]) -> tuple[set, CSVWriter, CSVWriter]:
        if not self.auto_store:
            return set(), DummyCSVWriter(), DummyCSVWriter()
        jsonl_exists = os.path.isfile(self.jsonl_path)
        full_csv_exists = os.path.isfile(self.full_csv_path)
        contact_csv_exists = os.path.isfile(self.contact_csv_path)
        seen = set()

        full_writer = CSVWriter(path=self.full_csv_path, csv_fields=full_csv_fields)
        contact_writer = CSVWriter(path=self.contact_csv_path, csv_fields=contact_csv_fields)

        # ── Case 1: Master JSONL exists (Nuke and Rebuild CSVs for perfect sync) ──
        if jsonl_exists:
            records = list({url_mgr.normalize_url(r.get(self.dedup_key, "")): r for r in self.read_jsonl() if r.get(self.dedup_key) and not r.get("error")}.values())
            seen = {url_mgr.normalize_url(record[self.dedup_key]) for record in records}

            # Delete existing CSVs to guarantee 100% sync
            if full_csv_exists: os.remove(self.full_csv_path)
            if contact_csv_exists: os.remove(self.contact_csv_path)

            # Re-initialize writers with fresh, empty files
            full_writer = CSVWriter(path=self.full_csv_path, csv_fields=full_csv_fields)
            contact_writer = CSVWriter(path=self.contact_csv_path, csv_fields=contact_csv_fields)

            if records:
                print(f"Regenerating CSVs from master JSONL ({len(records)} records)...")
                for record in records:
                    full_writer.writerow(record)
                    contact_row = {k: v for k, v in record.items() if k in contact_csv_fields}
                    contact_writer.writerow(contact_row)
                print("CSVs ready.")

            return seen, full_writer, contact_writer


        # ── Case 2: JSONL missing, but full.csv exists → rebuild JSONL from full.csv ───────────
        if full_csv_exists:
            print("Master JSONL missing — rebuilding from full.csv...")
            with open(self.full_csv_path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            for row in rows:
                clean_row = {k: v for k, v in row.items() if v != ""}
                self.append_to_jsonl(clean_row)
            print(f"JSONL rebuilt ({len(rows)} records).")
            seen = {url_mgr.normalize_url(value) for record in self.read_jsonl() if (value := record.get(self.dedup_key))}

            # Re-initialize writers to write the contact.csv from the rebuilt JSONL
            full_writer = CSVWriter(path=self.full_csv_path, csv_fields=full_csv_fields)
            contact_writer = CSVWriter(path=self.contact_csv_path, csv_fields=contact_csv_fields)

            if not contact_csv_exists:
                print("Generating contact.csv from rebuilt JSONL...")
                for record in self.read_jsonl():
                    contact_row = {k: v for k, v in record.items() if k in contact_csv_fields}
                    contact_writer.writerow(contact_row)

            return seen, full_writer, contact_writer

         # ── Case 3: All files missing — fresh start ──────────────────────────────
        return seen, full_writer, contact_writer
