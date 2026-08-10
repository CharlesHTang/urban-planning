import asyncio

import pytest

from architecture_scraper.adapters.sites.archello import ArchelloAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://archello.com/sitemaps/projects.2.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://archello.com/sitemaps/brands.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://example.com/sitemaps/projects.1.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://archello.com/sitemaps/projects.xml</loc>
  </sitemap>
</sitemapindex>
"""

PROJECT_SITEMAPS = {
    "https://archello.com/sitemaps/projects.xml": """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
          <url>
            <loc>https://archello.com/project/project-one</loc>
            <image:image>
              <image:loc>https://archello.example/project-image.jpg</image:loc>
            </image:image>
          </url>
          <url>
            <loc>https://archello.com/project/project-two/</loc>
          </url>
        </urlset>
    """,
    "https://archello.com/sitemaps/projects.2.xml": """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url>
            <loc>https://archello.com/project/project-three</loc>
          </url>
          <url>
            <loc>https://archello.com/project/project-one</loc>
          </url>
          <url>
            <loc>https://example.com/project/wrong-host</loc>
          </url>
          <url>
            <loc>https://archello.com/project/nested/path</loc>
          </url>
        </urlset>
    """,
}


def make_config() -> SiteConfig:
    return SiteConfig(
        "archello",
        "https://archello.com/projects",
        adapter=(
            "architecture_scraper.adapters.sites.archello:"
            "ArchelloAdapter"
        ),
    )


def test_discovers_projects_from_all_project_sitemaps() -> None:
    listing_html = "<html>Archello projects</html>"
    requested_urls: list[str] = []

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            requested_urls.append(url)
            assert render == "never"
            if url == make_config().projects_url:
                return FetchResult(url, url, listing_html)
            if url == ArchelloAdapter.SITEMAP_INDEX_URL:
                return FetchResult(url, url, SITEMAP_INDEX)
            return FetchResult(url, url, PROJECT_SITEMAPS[url])

    async def exercise() -> None:
        result = await ArchelloAdapter(make_config()).discover(
            FakeFetcher()  # type: ignore[arg-type]
        )

        assert result.project_urls == [
            "https://archello.com/project/project-one",
            "https://archello.com/project/project-two",
            "https://archello.com/project/project-three",
        ]
        assert result.listing_pages[0].html == listing_html

    asyncio.run(exercise())

    assert requested_urls == [
        make_config().projects_url,
        ArchelloAdapter.SITEMAP_INDEX_URL,
        "https://archello.com/sitemaps/projects.xml",
        "https://archello.com/sitemaps/projects.2.xml",
    ]


@pytest.mark.parametrize(
    ("method", "message"),
    [
        ("_parse_sitemap_index", "sitemap index returned invalid XML"),
        ("_parse_project_sitemap", "project sitemap 1 returned invalid XML"),
    ],
)
def test_rejects_invalid_sitemap_xml(method: str, message: str) -> None:
    parser = getattr(ArchelloAdapter, method)
    arguments = ("<urlset>",) if method == "_parse_sitemap_index" else (
        "<urlset>",
        1,
    )

    with pytest.raises(RuntimeError, match=message):
        parser(*arguments)


def test_rejects_index_without_project_sitemaps() -> None:
    listing_html = "<html>Archello projects</html>"

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            if url == make_config().projects_url:
                return FetchResult(url, url, listing_html)
            return FetchResult(
                url,
                url,
                "<sitemapindex><sitemap>"
                "<loc>https://archello.com/sitemaps/brands.xml</loc>"
                "</sitemap></sitemapindex>",
            )

    async def exercise() -> None:
        with pytest.raises(RuntimeError, match="contained no project sitemaps"):
            await ArchelloAdapter(make_config()).discover(
                FakeFetcher()  # type: ignore[arg-type]
            )

    asyncio.run(exercise())
