import asyncio
import aiohttp
from contact_finder_sdk.config import (
    RAPIDAPI_URL, RAPIDAPI_HOST, RAPIDAPI_DEFAULT_PARAMS,
    MAX_RETRIES, RETRY_BACKOFF_SECONDS, TRANSIENT_ERROR_PHRASES,
)

class APIClient:
    """Handles async HTTP requests to RapidAPI with retry logic."""

    def __init__(self, api_key: str, host: str = RAPIDAPI_HOST, max_retries: int = MAX_RETRIES, retry_backoff: int = RETRY_BACKOFF_SECONDS):
        self.base_url = f"https://{host}/"
        self.headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": host,
            "Content-Type": "application/json"
        }
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

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
                    async with session.get(self.base_url, headers=self.headers, params=params) as response:
                        response.raise_for_status()
                        result = await response.json(content_type=None)

                    api_error = (result or {}).get("error")
                    if api_error and self._is_transient_error(api_error) and attempt < self.max_retries:
                        await asyncio.sleep(self.retry_backoff * attempt)
                        last_error = api_error
                        continue
                    return url, result

                except (aiohttp.ClientResponseError, aiohttp.ClientError, asyncio.TimeoutError) as err:
                    last_error = str(err)
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_backoff * attempt)
                        continue
                    return url, {"error": last_error}

        return url, {"error": last_error or "request failed after retries"}
