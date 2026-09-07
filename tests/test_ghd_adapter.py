import asyncio
import json

import pytest

from architecture_scraper.adapters.sites.ghd import GhdAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


def make_config() -> SiteConfig:
    return SiteConfig(
        "ghd",
        "https://www.ghd.com/en/projects",
        adapter="architecture_scraper.adapters.sites.ghd:GhdAdapter",
    )


def test_discovers_all_paginated_project_urls() -> None:
    api_calls: list[tuple[str, object, dict[str, str] | None]] = []
    api_pages = {
        0: _api_page(
            3,
            "https://www.ghd.com/projects/project-one",
            "https://www.ghd.com/en/projects/project-two",
        ),
        2: _api_page(
            3,
            "https://www.ghd.com/en/projects/project-three",
        ),
    }

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            assert url == make_config().projects_url
            assert render == "never"
            return FetchResult(url, url, "listing")

        async def post_json(
            self,
            url: str,
            payload: object,
            *,
            headers: dict[str, str] | None = None,
        ) -> FetchResult:
            api_calls.append((url, payload, headers))
            assert isinstance(payload, dict)
            search = payload["widget"]["items"][0]["search"]  # type: ignore[index]
            return FetchResult(url, url, json.dumps(api_pages[search["offset"]]))

    async def exercise() -> None:
        adapter = GhdAdapter(make_config())
        adapter.PAGE_SIZE = 2
        result = await adapter.discover(FakeFetcher())  # type: ignore[arg-type]
        assert result.project_urls == [
            "https://www.ghd.com/en/projects/project-one",
            "https://www.ghd.com/en/projects/project-two",
            "https://www.ghd.com/en/projects/project-three",
        ]
        assert result.listing_pages[0].html == "listing"

    asyncio.run(exercise())
    assert len(api_calls) == 2
    assert all(call[0] == GhdAdapter.API_URL for call in api_calls)
    assert all(
        call[2]
        == {"Origin": GhdAdapter.BASE_URL, "Referer": make_config().projects_url}
        for call in api_calls
    )


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("{", "page 1 returned invalid JSON"),
        ('{"widgets": []}', "contained no result widget"),
        ('{"widgets": [{"content": []}]}', "contained no valid total"),
        (
            '{"widgets": [{"total_item": 1, "content": '
            '[{"url": "https://example.com/project"}]}]}',
            "contained an unexpected URL",
        ),
    ],
)
def test_rejects_invalid_api_data(body: str, message: str) -> None:
    with pytest.raises(RuntimeError, match=message):
        GhdAdapter._parse_api_page(body, 1)


def _api_page(total: int, *urls: str) -> dict[str, object]:
    return {
        "widgets": [
            {
                "total_item": total,
                "content": [{"url": url} for url in urls],
            }
        ]
    }
