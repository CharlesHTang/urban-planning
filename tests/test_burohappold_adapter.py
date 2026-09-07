import asyncio

import pytest

from architecture_scraper.adapters.sites.burohappold import BuroHappoldAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://www.burohappold.com/projects-sitemap2.xml</loc></sitemap>
  <sitemap><loc>https://www.burohappold.com/post-sitemap.xml</loc></sitemap>
  <sitemap><loc>https://example.com/projects-sitemap.xml</loc></sitemap>
  <sitemap><loc>https://www.burohappold.com/projects-sitemap.xml</loc></sitemap>
</sitemapindex>
"""

PROJECT_SITEMAPS = {
    "https://www.burohappold.com/projects-sitemap.xml": """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://www.burohappold.com/projects/</loc></url>
          <url><loc>https://www.burohappold.com/projects/project-one/</loc></url>
          <url><loc>https://www.burohappold.com/projects/project-two/</loc></url>
          <url><loc>https://www.burohappold.com/de/projects/wrong-locale/</loc></url>
        </urlset>
    """,
    "https://www.burohappold.com/projects-sitemap2.xml": """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://www.burohappold.com/projects/project-two/</loc></url>
          <url><loc>https://www.burohappold.com/projects/project-three/</loc></url>
          <url><loc>https://example.com/projects/wrong-host/</loc></url>
        </urlset>
    """,
}


def make_config() -> SiteConfig:
    return SiteConfig(
        "burohappold",
        "https://www.burohappold.com/projects",
        adapter=(
            "architecture_scraper.adapters.sites.burohappold:"
            "BuroHappoldAdapter"
        ),
    )


def test_discovers_projects_from_all_project_sitemaps() -> None:
    requested_urls: list[str] = []

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            requested_urls.append(url)
            assert render == "never"
            if url == make_config().projects_url:
                return FetchResult(url, url, "listing")
            if url == BuroHappoldAdapter.SITEMAP_INDEX_URL:
                return FetchResult(url, url, SITEMAP_INDEX)
            return FetchResult(url, url, PROJECT_SITEMAPS[url])

    async def exercise() -> None:
        result = await BuroHappoldAdapter(make_config()).discover(
            FakeFetcher()  # type: ignore[arg-type]
        )
        assert result.project_urls == [
            "https://www.burohappold.com/projects/project-one/",
            "https://www.burohappold.com/projects/project-two/",
            "https://www.burohappold.com/projects/project-three/",
        ]
        assert result.listing_pages[0].html == "listing"

    asyncio.run(exercise())
    assert requested_urls == [
        make_config().projects_url,
        BuroHappoldAdapter.SITEMAP_INDEX_URL,
        "https://www.burohappold.com/projects-sitemap.xml",
        "https://www.burohappold.com/projects-sitemap2.xml",
    ]


@pytest.mark.parametrize(
    ("method", "arguments", "message"),
    [
        ("_parse_sitemap_index", ("<sitemapindex>",), "invalid XML"),
        ("_parse_project_sitemap", ("<urlset>", 1), "invalid XML"),
    ],
)
def test_rejects_invalid_sitemap_xml(
    method: str,
    arguments: tuple[object, ...],
    message: str,
) -> None:
    with pytest.raises(RuntimeError, match=message):
        getattr(BuroHappoldAdapter, method)(*arguments)
