import asyncio

import pytest

from architecture_scraper.adapters.sites.hdr import HdrAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://www.hdrinc.com/sitemap.xml?page=2</loc></sitemap>
  <sitemap><loc>https://www.hdrinc.com/sitemap.xml?page=1</loc></sitemap>
  <sitemap><loc>https://www.hdrinc.com/sitemap.xml?page=2</loc></sitemap>
  <sitemap><loc>https://example.com/sitemap.xml?page=3</loc></sitemap>
  <sitemap><loc>https://www.hdrinc.com/sitemap.xml</loc></sitemap>
</sitemapindex>
"""

SITEMAP_PAGES = {
    "https://www.hdrinc.com/sitemap.xml?page=1": """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
          <url>
            <loc>https://www.hdrinc.com/portfolio/project-one</loc>
            <image:image>
              <image:loc>https://www.hdrinc.com/portfolio/project-image.jpg</image:loc>
            </image:image>
          </url>
          <url><loc>https://www.hdrinc.com/portfolio/project-two/</loc></url>
          <url><loc>https://www.hdrinc.com/portfolio</loc></url>
        </urlset>
    """,
    "https://www.hdrinc.com/sitemap.xml?page=2": """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://www.hdrinc.com/portfolio/project-three</loc></url>
          <url><loc>https://www.hdrinc.com/portfolio/project-one</loc></url>
          <url><loc>https://example.com/portfolio/wrong-host</loc></url>
          <url><loc>https://www.hdrinc.com/portfolio/nested/path</loc></url>
          <url><loc>https://www.hdrinc.com/portfolio/query?source=sitemap</loc></url>
        </urlset>
    """,
}


def make_config() -> SiteConfig:
    return SiteConfig(
        "hdr",
        "https://www.hdrinc.com/portfolio",
        adapter="architecture_scraper.adapters.sites.hdr:HdrAdapter",
    )


def test_discovers_projects_from_all_sitemap_pages() -> None:
    listing_html = "<html>HDR portfolio</html>"
    requested_urls: list[str] = []

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            requested_urls.append(url)
            assert render == "never"
            if url == make_config().projects_url:
                return FetchResult(url, url, listing_html)
            if url == HdrAdapter.SITEMAP_INDEX_URL:
                return FetchResult(url, url, SITEMAP_INDEX)
            return FetchResult(url, url, SITEMAP_PAGES[url])

    async def exercise() -> None:
        result = await HdrAdapter(make_config()).discover(
            FakeFetcher()  # type: ignore[arg-type]
        )

        assert result.project_urls == [
            "https://www.hdrinc.com/portfolio/project-one",
            "https://www.hdrinc.com/portfolio/project-two",
            "https://www.hdrinc.com/portfolio/project-three",
        ]
        assert result.listing_pages[0].html == listing_html

    asyncio.run(exercise())

    assert requested_urls == [
        make_config().projects_url,
        HdrAdapter.SITEMAP_INDEX_URL,
        "https://www.hdrinc.com/sitemap.xml?page=1",
        "https://www.hdrinc.com/sitemap.xml?page=2",
    ]


@pytest.mark.parametrize(
    ("method", "arguments", "message"),
    [
        (
            "_parse_sitemap_index",
            ("<sitemapindex>",),
            "sitemap index returned invalid XML",
        ),
        (
            "_parse_sitemap_page",
            ("<urlset>", 1),
            "sitemap page 1 returned invalid XML",
        ),
    ],
)
def test_rejects_invalid_sitemap_xml(
    method: str,
    arguments: tuple[object, ...],
    message: str,
) -> None:
    with pytest.raises(RuntimeError, match=message):
        getattr(HdrAdapter, method)(*arguments)


def test_rejects_index_without_sitemap_pages() -> None:
    listing_html = "<html>HDR portfolio</html>"

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            if url == make_config().projects_url:
                return FetchResult(url, url, listing_html)
            return FetchResult(
                url,
                url,
                "<sitemapindex><sitemap>"
                "<loc>https://example.com/sitemap.xml?page=1</loc>"
                "</sitemap></sitemapindex>",
            )

    async def exercise() -> None:
        with pytest.raises(RuntimeError, match="contained no sitemap pages"):
            await HdrAdapter(make_config()).discover(
                FakeFetcher()  # type: ignore[arg-type]
            )

    asyncio.run(exercise())


def test_rejects_sitemaps_without_portfolio_urls() -> None:
    listing_html = "<html>HDR portfolio</html>"

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            if url == make_config().projects_url:
                return FetchResult(url, url, listing_html)
            if url == HdrAdapter.SITEMAP_INDEX_URL:
                return FetchResult(
                    url,
                    url,
                    "<sitemapindex><sitemap>"
                    "<loc>https://www.hdrinc.com/sitemap.xml?page=1</loc>"
                    "</sitemap></sitemapindex>",
                )
            return FetchResult(
                url,
                url,
                "<urlset><url><loc>https://www.hdrinc.com/news/item</loc>"
                "</url></urlset>",
            )

    async def exercise() -> None:
        with pytest.raises(RuntimeError, match="contained no portfolio URLs"):
            await HdrAdapter(make_config()).discover(
                FakeFetcher()  # type: ignore[arg-type]
            )

    asyncio.run(exercise())
