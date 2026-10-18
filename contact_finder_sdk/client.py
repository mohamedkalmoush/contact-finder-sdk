import asyncio
import aiohttp
from contact_finder_sdk.config import (
    SCRAPEEG_URL, RAPIDAPI_HOST, RAPIDAPI_DEFAULT_PARAMS,
    MAX_RETRIES, RETRY_BACKOFF_SECONDS, REQUEST_TIMEOUT, TRANSIENT_ERROR_PHRASES
)

class APIClient:
    def __init__(self, api_key: str, source: str = "website", max_retries: int = MAX_RETRIES, retry_backoff: int = RETRY_BACKOFF_SECONDS):
        self.source = source.lower()
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        if self.source == "website":
            self.base_url = SCRAPEEG_URL
            self.headers = {"X-Api-Key": api_key}
        elif self.source == "rapidapi":
            self.base_url = f"https://{RAPIDAPI_HOST}/"
            self.headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": RAPIDAPI_HOST, "Content-Type": "application/json"}
        else:
            raise ValueError("source must be 'website' or 'rapidapi'")


    @staticmethod
    def _is_transient_error(message: str) -> bool:
        return bool(message) and any(phrase in message.lower() for phrase in TRANSIENT_ERROR_PHRASES)

    def _build_params(self, url: str, **kwargs) -> dict:
        # Start with RapidAPI defaults, add URL, then override with user kwargs
        params = {"url": url, **RAPIDAPI_DEFAULT_PARAMS}
        for k, v in kwargs.items():
            if k in RAPIDAPI_DEFAULT_PARAMS:
                params[k] = str(v).lower()
        return params


    async def fetch(self, session: aiohttp.ClientSession, url: str, semaphore: asyncio.Semaphore, **kwargs) -> tuple[str, dict | None]:
        params = self._build_params(url, **kwargs)
        last_error = None

        async with semaphore:
            for attempt in range(1, self.max_retries + 1):
                try:
                    async with session.get(self.base_url, headers=self.headers, params=params, timeout=REQUEST_TIMEOUT) as response:

                        # 1. HANDLE WEBSITE API ERRORS (401, 403, 429, 500)
                        if response.status >= 400:
                            try:
                                err_json = await response.json()
                                last_error = err_json.get("detail", f"HTTP {response.status}")
                            except Exception:
                                last_error = f"HTTP {response.status}: {await response.text()}"

                            # Stop immediately on Auth or Credit errors
                            if response.status in (401, 403):
                                return url, {"error": last_error}

                            # Retry on Rate Limits or Server Errors
                            if attempt < self.max_retries:
                                await asyncio.sleep(self.retry_backoff * attempt)
                                continue
                            return url, {"error": last_error}

                        # 2. HANDLE ENGINE JSON (HTTP 200 OK)
                        result = await response.json(content_type=None)
                        api_error = (result or {}).get("error")

                        # Retry if the engine itself returned a transient error
                        if api_error and self._is_transient_error(api_error) and attempt < self.max_retries:
                            await asyncio.sleep(self.retry_backoff * attempt)
                            last_error = api_error
                            continue

                        return url, result

                except (aiohttp.ClientResponseError, aiohttp.ClientError, asyncio.TimeoutError) as err:
                    # 3. HANDLE NETWORK ERRORS (DNS, Connection Refused, Timeout)
                    last_error = str(err)
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_backoff * attempt)
                        continue
                    return url, {"error": last_error}

        return url, {"error": last_error or "request failed after retries"}
