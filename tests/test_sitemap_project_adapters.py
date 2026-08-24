import asyncio

import pytest

from architecture_scraper.adapters.sites.dlrgroup import DlrGroupAdapter
from architecture_scraper.adapters.sites.gensler import GenslerAdapter
from architecture_scraper.adapters.sites.hks import HksAdapter
from architecture_scraper.adapters.sites.hok import HokAdapter
from architecture_scraper.adapters.sites.mottmac import MottMacAdapter
from architecture_scraper.adapters.sites.perkinseastman import (
    PerkinsEastmanAdapter,
)
from architecture_scraper.adapters.sites.perkinswill import PerkinsWillAdapter
from architecture_scraper.adapters.sites.populous import PopulousAdapter
from architecture_scraper.adapters.sites.ramboll import RambollAdapter
from architecture_scraper.adapters.sites.smithgroup import SmithGroupAdapter
from architecture_scraper.adapters.sites.som import SomAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


ADAPTER_CASES = [
    (
        RambollAdapter,
        "https://www.ramboll.com/projects/transport/project-one",
        "https://www.ramboll.com/projects/transport/project-one/more",
    ),
    (
        GenslerAdapter,
        "https://www.gensler.com/projects/project-one",
        "https://www.gensler.com/projects/all",
    ),
    (
        PerkinsWillAdapter,
        "https://perkinswill.com/project/project-one/",
        "https://perkinswill.com/projects/project-one/",
    ),
    (
        HksAdapter,
        "https://www.hksinc.com/what-we-do/projects/project-one/",
        "https://www.hksinc.com/what-we-do/projects/",
    ),
    (
        HokAdapter,
        "https://www.hok.com/projects/view/project-one/",
        "https://www.hok.com/projects/project-one/",
    ),
    (
        DlrGroupAdapter,
        "https://www.dlrgroup.com/work/project-one/",
        "https://www.dlrgroup.com/work/project-one/more/",
    ),
    (
        SomAdapter,
        "https://www.som.com/projects/project-one/",
        "https://www.som.com/story/project-one/",
    ),
    (
        MottMacAdapter,
        "https://www.mottmac.com/en/projects/project-one/",
        "https://www.mottmac.com/en/projects/",
    ),
    (
        PerkinsEastmanAdapter,
        "https://www.perkinseastman.com/projects/project-one/",
        "https://www.perkinseastman.com/projects/",
    ),
    (
        PopulousAdapter,
        "https://populous.com/showcases/project-one",
        "https://populous.com/portfolio/project-one",
    ),
    (
        SmithGroupAdapter,
        "https://www.smithgroup.com/projects/project-one",
        "https://www.smithgroup.com/our-work/project-one",
    ),
]


def urlset(*urls: str) -> str:
    entries = "".join(f"<url><loc>{url}</loc></url>" for url in urls)
    return (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{entries}</urlset>"
    )


@pytest.mark.parametrize(("adapter", "valid", "invalid"), ADAPTER_CASES)
def test_site_project_url_filters(
    adapter: type,
    valid: str,
    invalid: str,
) -> None:
    xml = urlset(
        valid,
        valid,
        invalid,
        f"{valid}?tracking=1",
        valid.replace(adapter.HOST, "example.com"),
    )

    assert adapter._parse_project_sitemap(xml, 1) == [valid]


@pytest.mark.parametrize(("adapter", "valid", "invalid"), ADAPTER_CASES)
def test_site_sitemap_parser_rejects_invalid_xml(
    adapter: type,
    valid: str,
    invalid: str,
) -> None:
    with pytest.raises(RuntimeError, match="project sitemap 1 returned invalid XML"):
        adapter._parse_project_sitemap("<urlset>", 1)


def test_discovers_and_deduplicates_multiple_direct_sitemaps() -> None:
    listing_html = "<html>HOK projects</html>"
    sitemap_pages = {
        HokAdapter.SITEMAP_URLS[0]: urlset(
            "https://www.hok.com/projects/view/project-one/",
            "https://www.hok.com/projects/view/project-two/",
        ),
        HokAdapter.SITEMAP_URLS[1]: urlset(
            "https://www.hok.com/projects/view/project-two/",
            "https://www.hok.com/projects/view/project-three/",
        ),
    }
    requested_urls: list[str] = []
    config = SiteConfig(
        "hok",
        "https://www.hok.com/projects/",
        adapter="architecture_scraper.adapters.sites.hok:HokAdapter",
    )

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            requested_urls.append(url)
            assert render == "never"
            if url == config.projects_url:
                return FetchResult(url, url, listing_html)
            return FetchResult(url, url, sitemap_pages[url])

    async def exercise() -> None:
        result = await HokAdapter(config).discover(
            FakeFetcher()  # type: ignore[arg-type]
        )
        assert result.project_urls == [
            "https://www.hok.com/projects/view/project-one/",
            "https://www.hok.com/projects/view/project-two/",
            "https://www.hok.com/projects/view/project-three/",
        ]
        assert result.listing_pages[0].html == listing_html

    asyncio.run(exercise())
    assert requested_urls == [config.projects_url, *HokAdapter.SITEMAP_URLS]


def test_uses_direct_sitemap_as_listing_when_project_index_is_stale() -> None:
    sitemap_xml = urlset("https://www.som.com/projects/project-one/")
    config = SiteConfig(
        "som",
        "https://www.som.com/projects",
        adapter="architecture_scraper.adapters.sites.som:SomAdapter",
    )

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            assert url == SomAdapter.SITEMAP_URLS[0]
            assert render == "never"
            return FetchResult(url, url, sitemap_xml)

    async def exercise() -> None:
        result = await SomAdapter(config).discover(
            FakeFetcher()  # type: ignore[arg-type]
        )
        assert result.project_urls == [
            "https://www.som.com/projects/project-one/"
        ]
        assert result.listing_pages[0].requested_url == SomAdapter.SITEMAP_URLS[0]
        assert result.listing_pages[0].html == sitemap_xml

    asyncio.run(exercise())


def test_discovers_smithgroup_projects_from_sorted_sitemap_pages() -> None:
    listing_html = "<html>SmithGroup projects</html>"
    index_xml = """
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <sitemap><loc>https://www.smithgroup.com/sitemap.xml?page=2</loc></sitemap>
          <sitemap><loc>https://www.smithgroup.com/sitemap.xml?page=1</loc></sitemap>
          <sitemap><loc>https://example.com/sitemap.xml?page=3</loc></sitemap>
        </sitemapindex>
    """
    pages = {
        "https://www.smithgroup.com/sitemap.xml?page=1": urlset(
            "https://www.smithgroup.com/projects/project-one",
            "https://www.smithgroup.com/projects/project-two",
        ),
        "https://www.smithgroup.com/sitemap.xml?page=2": urlset(
            "https://www.smithgroup.com/projects/project-two",
            "https://www.smithgroup.com/projects/project-three",
        ),
    }
    requested_urls: list[str] = []
    config = SiteConfig(
        "smithgroup",
        "https://www.smithgroup.com/our-work/projects",
        adapter=(
            "architecture_scraper.adapters.sites.smithgroup:"
            "SmithGroupAdapter"
        ),
    )

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            requested_urls.append(url)
            assert render == "never"
            if url == SmithGroupAdapter.LISTING_URL:
                return FetchResult(url, url, listing_html)
            if url == SmithGroupAdapter.SITEMAP_INDEX_URL:
                return FetchResult(url, url, index_xml)
            return FetchResult(url, url, pages[url])

    async def exercise() -> None:
        result = await SmithGroupAdapter(config).discover(
            FakeFetcher()  # type: ignore[arg-type]
        )
        assert result.project_urls == [
            "https://www.smithgroup.com/projects/project-one",
            "https://www.smithgroup.com/projects/project-two",
            "https://www.smithgroup.com/projects/project-three",
        ]

    asyncio.run(exercise())
    assert requested_urls == [
        SmithGroupAdapter.LISTING_URL,
        SmithGroupAdapter.SITEMAP_INDEX_URL,
        "https://www.smithgroup.com/sitemap.xml?page=1",
        "https://www.smithgroup.com/sitemap.xml?page=2",
    ]
