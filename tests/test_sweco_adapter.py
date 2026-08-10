import asyncio

import pytest

from architecture_scraper.adapters.sites.sweco import SwecoAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://www.swecogroup.com/showroom_cpt-sitemap2.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.swecogroup.com/post-sitemap1.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://example.com/showroom_cpt-sitemap1.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.swecogroup.com/showroom_cpt-sitemap1.xml</loc>
  </sitemap>
</sitemapindex>
"""

PORTFOLIO_SITEMAPS = {
    "https://www.swecogroup.com/showroom_cpt-sitemap1.xml": """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
          <url>
            <loc>https://www.swecogroup.com/portfolio/architecture/project-one/</loc>
            <image:image>
              <image:loc>https://www.swecogroup.com/portfolio/image.jpg</image:loc>
            </image:image>
          </url>
          <url>
            <loc>https://www.swecogroup.com/portfolio/urban-planning/project-two</loc>
          </url>
        </urlset>
    """,
    "https://www.swecogroup.com/showroom_cpt-sitemap2.xml": """
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url>
            <loc>https://www.swecogroup.com/portfolio/transport/project-three/</loc>
          </url>
          <url>
            <loc>https://www.swecogroup.com/portfolio/architecture/project-one/</loc>
          </url>
          <url><loc>https://example.com/portfolio/design/wrong-host/</loc></url>
          <url><loc>https://www.swecogroup.com/portfolio/project-listing/</loc></url>
          <url>
            <loc>https://www.swecogroup.com/portfolio/design/project/query</loc>
          </url>
        </urlset>
    """,
}


def make_config() -> SiteConfig:
    return SiteConfig(
        "sweco",
        "https://www.swecogroup.com/portfolio/",
        adapter="architecture_scraper.adapters.sites.sweco:SwecoAdapter",
    )


def test_discovers_projects_from_all_portfolio_sitemaps() -> None:
    listing_html = "<html>Sweco portfolio</html>"
    requested_urls: list[str] = []

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            requested_urls.append(url)
            assert render == "never"
            if url == make_config().projects_url:
                return FetchResult(url, url, listing_html)
            if url == SwecoAdapter.SITEMAP_INDEX_URL:
                return FetchResult(url, url, SITEMAP_INDEX)
            return FetchResult(url, url, PORTFOLIO_SITEMAPS[url])

    async def exercise() -> None:
        result = await SwecoAdapter(make_config()).discover(
            FakeFetcher()  # type: ignore[arg-type]
        )

        assert result.project_urls == [
            "https://www.swecogroup.com/portfolio/architecture/project-one/",
            "https://www.swecogroup.com/portfolio/urban-planning/project-two/",
            "https://www.swecogroup.com/portfolio/transport/project-three/",
        ]
        assert result.listing_pages[0].html == listing_html

    asyncio.run(exercise())

    assert requested_urls == [
        make_config().projects_url,
        SwecoAdapter.SITEMAP_INDEX_URL,
        "https://www.swecogroup.com/showroom_cpt-sitemap1.xml",
        "https://www.swecogroup.com/showroom_cpt-sitemap2.xml",
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
            "_parse_portfolio_sitemap",
            ("<urlset>", 1),
            "portfolio sitemap 1 returned invalid XML",
        ),
    ],
)
def test_rejects_invalid_sitemap_xml(
    method: str,
    arguments: tuple[object, ...],
    message: str,
) -> None:
    with pytest.raises(RuntimeError, match=message):
        getattr(SwecoAdapter, method)(*arguments)


def test_rejects_index_without_portfolio_sitemaps() -> None:
    listing_html = "<html>Sweco portfolio</html>"

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            if url == make_config().projects_url:
                return FetchResult(url, url, listing_html)
            return FetchResult(
                url,
                url,
                "<sitemapindex><sitemap>"
                "<loc>https://www.swecogroup.com/post-sitemap1.xml</loc>"
                "</sitemap></sitemapindex>",
            )

    async def exercise() -> None:
        with pytest.raises(RuntimeError, match="no portfolio sitemaps"):
            await SwecoAdapter(make_config()).discover(
                FakeFetcher()  # type: ignore[arg-type]
            )

    asyncio.run(exercise())


def test_rejects_empty_portfolio_sitemap() -> None:
    listing_html = "<html>Sweco portfolio</html>"

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            if url == make_config().projects_url:
                return FetchResult(url, url, listing_html)
            if url == SwecoAdapter.SITEMAP_INDEX_URL:
                return FetchResult(
                    url,
                    url,
                    "<sitemapindex><sitemap>"
                    "<loc>https://www.swecogroup.com/"
                    "showroom_cpt-sitemap1.xml</loc>"
                    "</sitemap></sitemapindex>",
                )
            return FetchResult(
                url,
                url,
                "<urlset><url><loc>https://www.swecogroup.com/news/item/</loc>"
                "</url></urlset>",
            )

    async def exercise() -> None:
        with pytest.raises(RuntimeError, match="contained no project URLs"):
            await SwecoAdapter(make_config()).discover(
                FakeFetcher()  # type: ignore[arg-type]
            )

    asyncio.run(exercise())
