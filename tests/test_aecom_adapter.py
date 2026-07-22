import asyncio
import json

import pytest

from architecture_scraper.adapters.sites.aecom import AecomAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


def test_discovers_all_paginated_api_links_and_keeps_full_listing() -> None:
    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            if url == "https://aecom.test/projects/":
                return FetchResult(url, url, "<html>complete listing</html>")

            page_number = int(url.rsplit("=", 1)[1])
            count = 100 if page_number == 1 else 2
            records = [
                {"link": f"https://aecom.test/projects/p-{page_number}-{index}/"}
                for index in range(count)
            ]
            return FetchResult(url, url, json.dumps(records))

    async def exercise() -> None:
        config = SiteConfig(
            "aecom",
            "https://aecom.test/projects/",
            adapter="architecture_scraper.adapters.sites.aecom:AecomAdapter",
        )
        fake_fetcher = FakeFetcher()
        result = await AecomAdapter(config).discover(
            fake_fetcher  # type: ignore[arg-type]
        )

        assert result.listing_pages[0].html == "<html>complete listing</html>"
        assert len(result.project_urls) == 102
        assert result.project_urls[-1].endswith("/p-2-1/")

    asyncio.run(exercise())


def test_rejects_malformed_api_records() -> None:
    with pytest.raises(RuntimeError, match="contained no link"):
        AecomAdapter._parse_api_page('[{"id": 1}]', 1)

