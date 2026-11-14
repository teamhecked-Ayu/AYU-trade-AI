from __future__ import annotations

from typing import Protocol, Sequence
import asyncio
import requests
from bs4 import BeautifulSoup


class SentimentDataProvider(Protocol):
    async def fetch_texts(self, query: str) -> Sequence[str]: ...


class RSSSentimentDataProvider:
    """Fetches recent public headlines from configured RSS/search endpoints."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def _fetch_sync(self, query: str) -> list[str]:
        url = "https://news.google.com/rss/search"
        response = requests.get(
            url,
            params={"q": query, "hl": "en", "gl": "US", "ceid": "US:en"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "xml")
        texts = [item.get_text(" ", strip=True) for item in soup.find_all("title")]
        return [text for text in texts if text][:50]

    async def fetch_texts(self, query: str) -> Sequence[str]:
        return await asyncio.to_thread(self._fetch_sync, query)
