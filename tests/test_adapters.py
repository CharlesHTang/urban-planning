import asyncio

from architecture_scraper.adapters.capture_only import CaptureOnlyAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


def test_capture_only_adapter_saves_full_listing_html() -> None:
    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            assert render == "never"
            return FetchResult(url, url, "<html><body>complete page</body></html>")

    async def exercise() -> None:
        config = SiteConfig("studio", "https://studio.test/work")
        fake_fetcher = FakeFetcher()
        result = await CaptureOnlyAdapter(config).discover(
            fake_fetcher  # type: ignore[arg-type]
        )

        assert result.project_urls == []
        assert result.listing_pages[0].html == (
            "<html><body>complete page</body></html>"
        )

    asyncio.run(exercise())
