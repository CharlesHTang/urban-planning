import asyncio

import pytest

from architecture_scraper.adapters.sites.thorntontomasetti import (
    ThorntonTomasettiAdapter,
)
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://www.thorntontomasetti.com/projects</loc></url>
  <url><loc>https://www.thorntontomasetti.com/project/project-one</loc></url>
  <url><loc>https://www.thorntontomasetti.com/project/project-two</loc></url>
  <url><loc>https://www.thorntomasetti.com/project/wrong-host</loc></url>
  <url><loc>https://www.thorntontomasetti.com/project/project/nested</loc></url>
</urlset>
"""


def make_config() -> SiteConfig:
    return SiteConfig(
        "thorntontomasetti",
        "https://www.thorntontomasetti.com/work",
        adapter=(
            "architecture_scraper.adapters.sites.thorntontomasetti:"
            "ThorntonTomasettiAdapter"
        ),
    )


def test_discovers_projects_and_uses_current_listing_url() -> None:
    requested_urls: list[str] = []

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            requested_urls.append(url)
            assert render == "never"
            if url == ThorntonTomasettiAdapter.LISTING_URL:
                return FetchResult(url, url, "listing")
            assert url == ThorntonTomasettiAdapter.SITEMAP_URLS[0]
            return FetchResult(url, url, SITEMAP)

    async def exercise() -> None:
        result = await ThorntonTomasettiAdapter(make_config()).discover(
            FakeFetcher()  # type: ignore[arg-type]
        )
        assert result.project_urls == [
            "https://www.thorntontomasetti.com/project/project-one",
            "https://www.thorntontomasetti.com/project/project-two",
        ]
        assert result.listing_pages[0].html == "listing"

    asyncio.run(exercise())
    assert requested_urls == [
        ThorntonTomasettiAdapter.LISTING_URL,
        ThorntonTomasettiAdapter.SITEMAP_URLS[0],
    ]


def test_rejects_invalid_project_sitemap_xml() -> None:
    with pytest.raises(RuntimeError, match="project sitemap 1 returned invalid XML"):
        ThorntonTomasettiAdapter._parse_project_sitemap("<urlset>", 1)
