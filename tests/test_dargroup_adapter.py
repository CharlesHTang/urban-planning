import asyncio

import pytest

from architecture_scraper.adapters.sites.dargroup import DarGroupAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://sidaracollaborative.com/projects</loc></url>
  <url><loc>https://sidaracollaborative.com/projects/project-one</loc></url>
  <url><loc>https://sidaracollaborative.com/projects/project-two</loc></url>
  <url><loc>https://sidaracollaborative.com/projects/project-one</loc></url>
  <url><loc>https://sidaracollaborative.com/projects/project/nested</loc></url>
  <url><loc>https://example.com/projects/wrong-host</loc></url>
</urlset>
"""


def make_config() -> SiteConfig:
    return SiteConfig(
        "dargroup",
        "https://www.dargroup.com/work",
        adapter="architecture_scraper.adapters.sites.dargroup:DarGroupAdapter",
    )


def test_discovers_sidara_projects_after_dar_group_rename() -> None:
    requested_urls: list[str] = []

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            requested_urls.append(url)
            assert render == "never"
            if url == DarGroupAdapter.LISTING_URL:
                return FetchResult(url, url, "listing")
            assert url == DarGroupAdapter.SITEMAP_URLS[0]
            return FetchResult(url, url, SITEMAP)

    async def exercise() -> None:
        result = await DarGroupAdapter(make_config()).discover(
            FakeFetcher()  # type: ignore[arg-type]
        )
        assert result.project_urls == [
            "https://sidaracollaborative.com/projects/project-one",
            "https://sidaracollaborative.com/projects/project-two",
        ]
        assert result.listing_pages[0].html == "listing"

    asyncio.run(exercise())
    assert requested_urls == [
        DarGroupAdapter.LISTING_URL,
        DarGroupAdapter.SITEMAP_URLS[0],
    ]


def test_rejects_invalid_project_sitemap_xml() -> None:
    with pytest.raises(RuntimeError, match="project sitemap 1 returned invalid XML"):
        DarGroupAdapter._parse_project_sitemap("<urlset>", 1)
