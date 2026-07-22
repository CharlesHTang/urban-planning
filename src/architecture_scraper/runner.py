import asyncio
from urllib.parse import urldefrag, urljoin, urlparse

from .adapters import load_adapter
from .config import SiteConfig
from .fetcher import Fetcher
from .models import RawPage, RunSummary, ScrapeError
from .storage import PageStore


class CollectionRunner:
    """Run site adapters and save complete, unparsed HTML pages."""

    def __init__(self, site: SiteConfig, store: PageStore) -> None:
        self.site = site
        self.store = store

    async def collect(self) -> RunSummary:
        adapter = load_adapter(self.site)
        async with self._new_fetcher() as fetcher:
            discovery = await adapter.discover(fetcher)
            for page in discovery.listing_pages:
                self.store.save(page)

            urls, invalid_errors = self._normalize_urls(discovery.project_urls)
            self.store.save_project_urls(self.site.name, urls)
            saved_details, fetch_errors = await self._fetch_details(urls, fetcher)

        return RunSummary(
            saved_pages=len(discovery.listing_pages) + saved_details,
            discovered_urls=len(urls),
            errors=invalid_errors + fetch_errors,
        )

    async def fetch_details(self, urls: list[str]) -> RunSummary:
        normalized, invalid_errors = self._normalize_urls(urls)
        self.store.save_project_urls(self.site.name, normalized)
        async with self._new_fetcher() as fetcher:
            saved, fetch_errors = await self._fetch_details(normalized, fetcher)
        return RunSummary(saved, len(normalized), invalid_errors + fetch_errors)

    async def _fetch_details(
        self, urls: list[str], fetcher: Fetcher
    ) -> tuple[int, list[ScrapeError]]:
        semaphore = asyncio.Semaphore(self.site.concurrency)

        async def fetch_one(url: str) -> ScrapeError | None:
            async with semaphore:
                try:
                    result = await fetcher.fetch(url, render=self.site.detail_render)
                    self.store.save(
                        RawPage(
                            site=self.site.name,
                            kind="detail",
                            requested_url=result.requested_url,
                            url=result.url,
                            html=result.html,
                        )
                    )
                    return None
                except Exception as error:
                    return ScrapeError(self.site.name, url, str(error))

        results = await asyncio.gather(*(fetch_one(url) for url in urls))
        errors = [error for error in results if error is not None]
        return len(urls) - len(errors), errors

    def _normalize_urls(
        self, urls: list[str]
    ) -> tuple[list[str], list[ScrapeError]]:
        normalized: list[str] = []
        errors: list[ScrapeError] = []
        seen: set[str] = set()
        for raw_url in urls:
            value = raw_url.strip()
            url = urldefrag(urljoin(self.site.projects_url, value)).url
            parsed = urlparse(url)
            if not value or parsed.scheme not in {"http", "https"} or not parsed.netloc:
                errors.append(ScrapeError(self.site.name, raw_url, "Invalid HTTP URL"))
            elif url not in seen:
                seen.add(url)
                normalized.append(url)
        return normalized, errors

    def _new_fetcher(self) -> Fetcher:
        return Fetcher(
            concurrency=self.site.concurrency,
            request_delay=self.site.request_delay,
            timeout=self.site.timeout,
            impersonate=self.site.impersonate,
        )
