import asyncio
import json

import pytest

from architecture_scraper.adapters.sites.arcadis import ArcadisAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


def make_config() -> SiteConfig:
    return SiteConfig(
        "arcadis",
        "https://www.arcadis.com/en/projects",
        adapter="architecture_scraper.adapters.sites.arcadis:ArcadisAdapter",
    )


def test_discovers_all_paginated_project_grid_urls() -> None:
    listing_html = "<html>Arcadis projects</html>"
    api_calls: list[tuple[str, object, dict[str, str] | None]] = []
    api_pages = {
        0: {
            "total": 5,
            "items": [
                {"url": "/en/projects/europe/project-one"},
                {
                    "url": (
                        "https://www.arcadis.com/"
                        "en/projects/australia/project-two"
                    )
                },
            ],
        },
        2: {
            "total": 5,
            "items": [
                {"url": "/en/projects/asia/project-three"},
                {"url": "/en/projects/americas/project-four"},
            ],
        },
        4: {
            "total": 5,
            "items": [{"url": "/en/projects/europe/project-five"}],
        },
    }

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            assert url == make_config().projects_url
            assert render == "never"
            return FetchResult(url, url, listing_html)

        async def post_json(
            self,
            url: str,
            payload: object,
            *,
            headers: dict[str, str] | None = None,
        ) -> FetchResult:
            api_calls.append((url, payload, headers))
            assert isinstance(payload, dict)
            body = json.dumps(api_pages[payload["skip"]])
            return FetchResult(url, url, body)

    async def exercise() -> None:
        adapter = ArcadisAdapter(make_config())
        adapter.PAGE_SIZE = 2
        result = await adapter.discover(FakeFetcher())  # type: ignore[arg-type]

        assert result.project_urls == [
            "https://www.arcadis.com/en/projects/europe/project-one",
            "https://www.arcadis.com/en/projects/australia/project-two",
            "https://www.arcadis.com/en/projects/asia/project-three",
            "https://www.arcadis.com/en/projects/americas/project-four",
            "https://www.arcadis.com/en/projects/europe/project-five",
        ]
        assert result.listing_pages[0].html == listing_html

    asyncio.run(exercise())

    assert [call[1]["skip"] for call in api_calls] == [0, 2, 4]  # type: ignore[index]
    assert all(call[0] == ArcadisAdapter.API_URL for call in api_calls)
    assert all(
        call[2]
        == {
            "Origin": ArcadisAdapter.BASE_URL,
            "Referer": make_config().projects_url,
        }
        for call in api_calls
    )


def test_rejects_invalid_api_json() -> None:
    with pytest.raises(RuntimeError, match="page 1 returned invalid JSON"):
        ArcadisAdapter._parse_api_page("{", 1)


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ('{"items": []}', "contained no valid total"),
        ('{"total": 1}', "contained no items list"),
        (
            '{"total": 1, "items": [{"url": "https://example.com/project"}]}',
            "contained an unexpected URL",
        ),
    ],
)
def test_rejects_invalid_api_data(body: str, message: str) -> None:
    with pytest.raises(RuntimeError, match=message):
        ArcadisAdapter._parse_api_page(body, 1)
