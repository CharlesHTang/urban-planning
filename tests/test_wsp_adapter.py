import asyncio

import pytest

from architecture_scraper.adapters.sites.wsp import WspAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


SITEMAP = """<?xml version="1.0" encoding="utf-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://www.wsp.com/en-gl/projects</loc></url>
  <url><loc>https://www.wsp.com/en-gl/projects/project-one</loc></url>
  <url><loc>https://www.wsp.com/en-gl/projects/project-two</loc></url>
  <url><loc>https://www.wsp.com/en-gb/projects/other-locale</loc></url>
  <url><loc>https://example.com/en-gl/projects/wrong-host</loc></url>
</urlset>
"""


def test_discovers_only_en_gl_project_details_from_sitemap() -> None:
    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            assert url == WspAdapter.SITEMAP_URL
            assert render == "never"
            return FetchResult(url, url, SITEMAP)

    async def exercise() -> None:
        config = SiteConfig(
            "wsp",
            "https://www.wsp.com/en-gl/projects#sort=date%20descending",
            adapter="architecture_scraper.adapters.sites.wsp:WspAdapter",
        )
        fake_fetcher = FakeFetcher()
        result = await WspAdapter(config).discover(
            fake_fetcher  # type: ignore[arg-type]
        )

        assert result.project_urls == [
            "https://www.wsp.com/en-gl/projects/project-one",
            "https://www.wsp.com/en-gl/projects/project-two",
        ]
        assert result.listing_pages[0].html == SITEMAP

    asyncio.run(exercise())


def test_rejects_invalid_sitemap_xml() -> None:
    with pytest.raises(RuntimeError, match="invalid XML"):
        WspAdapter._parse_sitemap("<urlset>")

