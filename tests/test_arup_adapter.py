import asyncio
import json

import pytest

from architecture_scraper.adapters.sites.arup import ArupAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


def make_config() -> SiteConfig:
    return SiteConfig(
        "arup",
        "https://www.arup.com/en-us/projects/all-projects/",
        adapter="architecture_scraper.adapters.sites.arup:ArupAdapter",
    )


def api_page(
    total: int,
    current_page: int,
    total_pages: int,
    groups: list[list[str]],
) -> str:
    return json.dumps(
        {
            "grouped": [
                [{"url": url} for url in group]
                for group in groups
            ],
            "total": total,
            "currentPage": current_page,
            "pageSize": 2,
            "numberOfPages": total_pages,
        }
    )


def test_discovers_all_paginated_project_api_urls() -> None:
    listing_html = "<html>Arup projects</html>"
    pages = {
        1: api_page(
            5,
            1,
            3,
            [[
                "/en-us/projects/project-one/",
                "https://www.arup.com/en-us/projects/project-two/",
            ]],
        ),
        2: api_page(
            5,
            2,
            3,
            [
                ["/en-us/projects/project-three/?source=api"],
                ["/en-us/projects/project-four/"],
            ],
        ),
        3: api_page(
            5,
            3,
            3,
            [["/en-us/projects/project-five/"]],
        ),
    }
    api_calls: list[tuple[str, object, dict[str, str] | None]] = []

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
            page_number = payload["pageNumber"]
            assert isinstance(page_number, int)
            return FetchResult(url, url, pages[page_number])

    async def exercise() -> None:
        adapter = ArupAdapter(make_config())
        adapter.PAGE_SIZE = 2
        result = await adapter.discover(FakeFetcher())  # type: ignore[arg-type]

        assert result.project_urls == [
            "https://www.arup.com/en-us/projects/project-one/",
            "https://www.arup.com/en-us/projects/project-two/",
            "https://www.arup.com/en-us/projects/project-three/",
            "https://www.arup.com/en-us/projects/project-four/",
            "https://www.arup.com/en-us/projects/project-five/",
        ]
        assert result.listing_pages[0].html == listing_html

    asyncio.run(exercise())

    assert [call[1]["pageNumber"] for call in api_calls] == [1, 2, 3]  # type: ignore[index]
    assert all(call[0] == ArupAdapter.API_URL for call in api_calls)
    assert all(
        call[2]
        == {
            "Origin": ArupAdapter.BASE_URL,
            "Referer": make_config().projects_url,
        }
        for call in api_calls
    )


def test_rejects_invalid_api_json() -> None:
    with pytest.raises(RuntimeError, match="page 1 returned invalid JSON"):
        ArupAdapter._parse_api_page("{", 1)


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (
            '{"currentPage": 1, "pageSize": 20, '
            '"numberOfPages": 1, "grouped": []}',
            "contained no valid total",
        ),
        (
            '{"total": 1, "pageSize": 20, '
            '"numberOfPages": 1, "grouped": []}',
            "contained no valid current page",
        ),
        (
            '{"total": 1, "currentPage": 1, '
            '"numberOfPages": 1, "grouped": []}',
            "contained no valid page size",
        ),
        (
            '{"total": 1, "currentPage": 1, '
            '"pageSize": 20, "grouped": []}',
            "contained no valid page count",
        ),
        (
            '{"total": 1, "currentPage": 1, '
            '"pageSize": 20, "numberOfPages": 1}',
            "contained no grouped list",
        ),
        (
            api_page(
                1,
                1,
                1,
                [["https://example.com/en-us/projects/wrong-host/"]],
            ),
            "contained an unexpected URL",
        ),
    ],
)
def test_rejects_invalid_api_data(body: str, message: str) -> None:
    with pytest.raises(RuntimeError, match=message):
        ArupAdapter._parse_api_page(body, 1)


def test_rejects_incomplete_api_result_count() -> None:
    listing_html = "<html>Arup projects</html>"

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            return FetchResult(url, url, listing_html)

        async def post_json(
            self,
            url: str,
            payload: object,
            *,
            headers: dict[str, str] | None = None,
        ) -> FetchResult:
            return FetchResult(
                url,
                url,
                api_page(2, 1, 1, [["/en-us/projects/only-project/"]]),
            )

    async def exercise() -> None:
        with pytest.raises(RuntimeError, match="returned 1 of 2 projects"):
            await ArupAdapter(make_config()).discover(
                FakeFetcher()  # type: ignore[arg-type]
            )

    asyncio.run(exercise())
