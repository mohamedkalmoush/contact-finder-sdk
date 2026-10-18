import time
import asyncio
import aiohttp
from tqdm.asyncio import tqdm
from contact_finder_sdk.config import Config, CONCURRENCY, REQUEST_TIMEOUT
from contact_finder_sdk.utils import URLManager
from contact_finder_sdk.parsers import ResponseParser
from contact_finder_sdk.storage import StorageManager
from contact_finder_sdk.client import APIClient

class ContactFinder:
    # def __init__(self, api_key: str, host: str = "website-contact-finder.p.rapidapi.com", concurrency: int = 25, project_name: str = "default_project", use_vps: bool = False):
    def __init__(self, api_key: str, source: str = "website", concurrency: int = 25, project_name: str = "default_project"):
        # 1. Create an isolated config for this instance
        self.local_config = Config()
        self.local_config.set_project(project_name)
        self.url_manager = URLManager(project_config=self.local_config)

        # 2. Initialize StorageManager AFTER config is updated so it grabs the new paths
        self.storage = StorageManager(dedup_key="url", auto_store=True, project_config=self.local_config)
        self.client = APIClient(api_key=api_key, source=source)
        self.concurrency = concurrency
        self.dedup_key = "url"
        self.parser = ResponseParser()

    # Added a synchronous wrapper so users don't have to use asyncio
    def run(self, urls: list[str] = None, file_path: str = None, url_field_name: str = "url", dedup_key: str = "url", on_success=None, parse_mode: str = "raw", auto_store: bool = True, project_name: str = None, **api_kwargs):
        """Synchronous entry point for the SDK."""
        # Apply per-run file configurations
        self.url_manager.field_name = url_field_name.lower()
        self.storage.dedup_key = dedup_key.lower()
        self.dedup_key = dedup_key.lower()

        # If user passes a new project name at runtime, update config and rebuild storage
        if project_name:
            self.local_config.set_project(project_name)
            self.url_manager.config = self.local_config
            self.storage = StorageManager(dedup_key=dedup_key.lower(), auto_store=auto_store, project_config=self.local_config)

        self.on_success = on_success
        self.parse_mode = parse_mode
        self.auto_store = auto_store.lower() == "true" if isinstance(auto_store, str) else bool(auto_store)
        self.storage.auto_store = self.auto_store

        asyncio.run(self.run_async(urls, file_path, **api_kwargs))

    async def run_async(self, urls: list[str] = None, file_path: str = None, **api_kwargs):
        urls = urls or self.url_manager.load_urls(file_path)
        urls = URLManager.remove_duplicates(urls)     # remove urls duplicates

        print('Total websites to process: ', len(urls))
        print(f"Scraping: {len(urls)} URLs")

        if self.auto_store:
            self.url_manager.ensure_data_dir()

        # Always generate fields for both full and contact CSVs for storage
        full_csv_fields = self.parser.build_csv_fields()
        contact_csv_fields = list(self.parser.parse_contact({}).keys())

        seen, full_writer, contact_writer = self.storage.build_seen_and_sync_files(full_csv_fields=full_csv_fields, contact_csv_fields=contact_csv_fields)
        success_count = skip_count = fail_count = cached_count = 0

        # 1. Load cache from disk (fallback to full.jsonl if raw is missing)
        is_fallback = False
        cache = {}

        records = self.storage.read_jsonl(self.storage.raw_jsonl_path)
        if not records and self.parse_mode in ("full", "contact"):
            is_fallback = True
            print("⚠️ raw.jsonl missing. Falling back to full.jsonl.")
            records = self.storage.read_jsonl(self.storage.jsonl_path)

        for record in records:
            if raw_url := (record.get("data") or {}).get("url") or record.get("url"):
                cache[self.url_manager.normalize_url(raw_url)] = record

        # 2. Partition URLs and trigger callbacks
        pending_urls, cached_count, skip_count = [], 0, 0
        for target_url in urls:
            normalized_url = self.url_manager.normalize_url(target_url)
            if normalized_url in cache:
                if self.on_success:
                    if is_fallback:
                        row = cache[normalized_url] if self.parse_mode == "full" else {k: v for k, v in cache[normalized_url].items() if k in contact_csv_fields}
                    else:
                        row = self.parser.parse(cache[normalized_url], self.parse_mode)
                    self.on_success(row)
                cached_count += 1
            elif normalized_url in seen and self.parse_mode != "raw":
                skip_count += 1
            else:
                pending_urls.append(target_url)

        if not pending_urls:
            print(f"Nothing new to scrape. {cached_count} cached, {skip_count} already seen.")
            return

        semaphore = asyncio.Semaphore(self.concurrency)
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            # Pass api_kwargs (like profile="false") down to the client
            tasks = [asyncio.ensure_future(self.client.fetch(session, url, semaphore, **api_kwargs)) for url in pending_urls]

            # Kept your exact tqdm setup and commented out pbar lines
            with tqdm(total=len(urls), initial=cached_count + skip_count, desc=f"{'Scraping':<32}", unit="URL", dynamic_ncols=True, colour="green", miniters=1,) as pbar:
                for coro in asyncio.as_completed(tasks):
                    url, json_data = await coro
                    api_error = ((json_data or {}).get("data") or json_data or {}).get("error")

                    if json_data and not api_error:
                        # 1. ALWAYS parse as "full" for SDK storage (Master Record)
                        full_row = self.parser.parse(json_data, parse_mode="full")
                        if not self.parser.has_contact_data(full_row):
                            fail_count += 1
                            self.storage.log_failed_url(url, "No contact info found")
                            pbar.set_description(f"⚠ EMPTY {(d:=full_row.get('domain') or url)[:20]+(' .. ' if len(d)>20 else ''):<24}")
                            pbar.set_postfix(saved=success_count, cached=cached_count, skipped=skip_count, failed=fail_count, refresh=False)
                            pbar.update(1)
                            continue

                        # 2. INSTANTLY call the user's function with THEIR requested parse_mode
                        if self.on_success:
                            callback_row = self.parser.parse(json_data, parse_mode=self.parse_mode)
                            self.on_success(callback_row)

                        normalized_value = self.url_manager.normalize_url(full_row.get(self.dedup_key))

                        if normalized_value and normalized_value in seen:
                            # Already in master files. We will restore raw.jsonl below, but skip master files to prevent duplicates.
                            success_count += 1
                            pbar.set_description(f"⟳ {(d:=full_row.get('domain') or url)[:20]+(' .. ' if len(d)>20 else ''):<24}")
                        else:
                            self.storage.append_to_jsonl(full_row)                                          # 2. Save to master full JSONL
                            full_writer.writerow(full_row)                                                  # 3. Save to full CSV
                            contact_row = {k: v for k, v in full_row.items() if k in contact_csv_fields}    # 4. Filter and save to contact CSV
                            contact_writer.writerow(contact_row)

                            if normalized_value:
                                seen.add(normalized_value)
                            success_count += 1
                            pbar.set_description(f"✔ {(d:=full_row.get('domain') or url)[:20]+(' .. ' if len(d)>20 else ''):<24}")

                        # ALWAYS save raw API response to raw.jsonl (restores cache if missing, without duplicating master files)
                        self.storage.append_to_jsonl(json_data, file_path=self.storage.raw_jsonl_path)
                    else:
                        fail_count += 1
                        self.storage.log_failed_url(url, api_error or "request failed")
                        pbar.set_description(f"✖ {url[:20]+(' .. ' if len(url)>20 else ''):<24}")

                    pbar.set_postfix(saved=success_count, cached=cached_count, skipped=skip_count, failed=fail_count, refresh=False)
                    pbar.update(1)

        print(f"Done. saved={success_count} | cached={cached_count} | skipped={skip_count} | failed={fail_count}")
        if self.auto_store:
            print(f"Files: {self.storage.jsonl_path}, {self.storage.raw_jsonl_path}, {self.storage.full_csv_path}, {self.storage.contact_csv_path}")
            if fail_count: print(f"Failed log: {self.storage.failed_log_path}")
