import asyncio
import json

import pytest

from architecture_scraper.adapters.sites.nikken import NikkenAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


def make_config() -> SiteConfig:
    return SiteConfig(
        "nikken",
        "https://www.nikken.co.jp/en/projects",
        adapter="architecture_scraper.adapters.sites.nikken:NikkenAdapter",
    )


def test_discovers_english_urls_from_json_index() -> None:
    index = {
        "array": [
            {"link": "/ja/projects/project-one.html"},
            {"link": "/ja/projects/office/project-two.html"},
        ]
    }
    requested_urls: list[str] = []

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            requested_urls.append(url)
            if url == make_config().projects_url:
                assert render == "never"
                return FetchResult(url, "https://www.nikken.jp/en/projects/", "listing")
            assert url == NikkenAdapter.INDEX_URL
            assert render == "never"
            return FetchResult(url, url, json.dumps(index))

    async def exercise() -> None:
        result = await NikkenAdapter(make_config()).discover(
            FakeFetcher()  # type: ignore[arg-type]
        )
        assert result.project_urls == [
            "https://www.nikken.jp/en/projects/project-one.html",
            "https://www.nikken.jp/en/projects/office/project-two.html",
        ]
        assert result.listing_pages[0].html == "listing"

    asyncio.run(exercise())
    assert requested_urls == [make_config().projects_url, NikkenAdapter.INDEX_URL]


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("{", "returned invalid JSON"),
        ('{"items": []}', "contained no project list"),
        (
            '{"array": [{"link": "https://example.com/project"}]}',
            "contained an unexpected URL",
        ),
    ],
)
def test_rejects_invalid_index(body: str, message: str) -> None:
    with pytest.raises(RuntimeError, match=message):
        NikkenAdapter._parse_index(body)
