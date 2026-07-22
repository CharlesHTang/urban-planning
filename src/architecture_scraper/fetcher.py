import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from time import monotonic

from curl_cffi import AsyncSession
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from .config import RenderMode


@dataclass(frozen=True, slots=True)
class FetchResult:
    requested_url: str
    url: str
    html: str


class Fetcher:
    """Shared HTTP and browser transport; it never parses page content."""

    def __init__(
        self,
        *,
        concurrency: int,
        request_delay: float,
        timeout: float,
        impersonate: str,
    ) -> None:
        self._concurrency = concurrency
        self._request_delay = request_delay
        self._timeout = timeout
        self._impersonate = impersonate
        self._session: AsyncSession | None = None
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._rate_lock = asyncio.Lock()
        self._browser_lock = asyncio.Lock()
        self._next_request_at = 0.0

    async def __aenter__(self) -> "Fetcher":
        self._session = AsyncSession(
            max_clients=self._concurrency,
            timeout=self._timeout,
            impersonate=self._impersonate,
        )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._browser is not None:
            await self._browser.close()
        if self._playwright is not None:
            await self._playwright.stop()
        if self._session is not None:
            await self._session.close()

    async def fetch(self, url: str, *, render: RenderMode) -> FetchResult:
        """Return the complete response HTML without extracting anything."""
        if render == "always":
            return await self._fetch_browser(url)

        try:
            return await self._fetch_http(url)
        except Exception:
            if render == "never":
                raise
            return await self._fetch_browser(url)

    @asynccontextmanager
    async def browser_page(self, url: str) -> AsyncIterator[Page]:
        """Open a customizable Playwright page for a site adapter."""
        await self._wait_for_rate_limit()
        browser = await self._get_browser()
        context: BrowserContext = await browser.new_context()
        page = await context.new_page()
        try:
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self._timeout * 1000,
            )
            if response is not None and not response.ok:
                raise RuntimeError(f"Browser request returned HTTP {response.status}")
            yield page
        finally:
            await context.close()

    async def _fetch_http(self, url: str) -> FetchResult:
        if self._session is None:
            raise RuntimeError("Fetcher must be used as an async context manager")
        await self._wait_for_rate_limit()
        response = await self._session.get(url, allow_redirects=True)
        response.raise_for_status()
        return FetchResult(url, str(response.url), response.text)

    async def _fetch_browser(self, url: str) -> FetchResult:
        async with self.browser_page(url) as page:
            return FetchResult(url, page.url, await page.content())

    async def _get_browser(self) -> Browser:
        async with self._browser_lock:
            if self._browser is None:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(headless=True)
        return self._browser

    async def _wait_for_rate_limit(self) -> None:
        async with self._rate_lock:
            delay = self._next_request_at - monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
            self._next_request_at = monotonic() + self._request_delay
