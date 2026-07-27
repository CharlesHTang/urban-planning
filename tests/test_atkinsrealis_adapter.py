import asyncio
import json

import pytest

from architecture_scraper.adapters.sites.atkinsrealis import (
    AtkinsRealisAdapter,
)
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


def make_config() -> SiteConfig:
    return SiteConfig(
        "atkinsrealis",
        "https://www.atkinsrealis.com/en/projects",
        adapter=(
            "architecture_scraper.adapters.sites.atkinsrealis:"
            "AtkinsRealisAdapter"
        ),
    )


def api_page(
    total: int,
    total_pages: int,
    links: list[str],
) -> str:
    return json.dumps(
        {
            "meta": {
                "totalCount": total,
                "totalPage": total_pages,
            },
            "data": [{"link": link} for link in links],
        }
    )


def test_discovers_all_paginated_project_api_urls() -> None:
    listing_html = "<html>AtkinsRéalis projects</html>"
    pages = {
        1: api_page(
            5,
            3,
            [
                "/en/projects/project-one",
                "https://www.atkinsrealis.com/en/projects/project-two",
            ],
        ),
        2: api_page(
            5,
            3,
            [
                "/en/projects/project-three/",
                "/en/projects/project-four?source=api",
            ],
        ),
        3: api_page(5, 3, ["/en/projects/project-five"]),
    }
    requested_urls: list[str] = []

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            requested_urls.append(url)
            if url == make_config().projects_url:
                assert render == "never"
                return FetchResult(url, url, listing_html)

            assert render == "never"
            page_number = int(url.split("page=")[1].split("&")[0])
            return FetchResult(url, url, pages[page_number])

    async def exercise() -> None:
        result = await AtkinsRealisAdapter(make_config()).discover(
            FakeFetcher()  # type: ignore[arg-type]
        )

        assert result.project_urls == [
            "https://www.atkinsrealis.com/en/projects/project-one",
            "https://www.atkinsrealis.com/en/projects/project-two",
            "https://www.atkinsrealis.com/en/projects/project-three",
            "https://www.atkinsrealis.com/en/projects/project-four",
            "https://www.atkinsrealis.com/en/projects/project-five",
        ]
        assert result.listing_pages[0].html == listing_html

    asyncio.run(exercise())

    assert requested_urls[0] == make_config().projects_url
    assert len(requested_urls) == 4
    assert all(
        "content-type=application%2Fjson" in url
        for url in requested_urls[1:]
    )


def test_rejects_invalid_api_json() -> None:
    with pytest.raises(RuntimeError, match="page 1 returned invalid JSON"):
        AtkinsRealisAdapter._parse_api_page("{", 1)


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ('{"data": []}', "contained no metadata"),
        (
            '{"meta": {"totalPage": 1}, "data": []}',
            "contained no valid total",
        ),
        (
            '{"meta": {"totalCount": 1}, "data": []}',
            "contained no valid page count",
        ),
        (
            '{"meta": {"totalCount": 1, "totalPage": 1}}',
            "contained no data list",
        ),
        (
            api_page(1, 1, ["https://example.com/en/projects/wrong-host"]),
            "contained an unexpected URL",
        ),
    ],
)
def test_rejects_invalid_api_data(body: str, message: str) -> None:
    with pytest.raises(RuntimeError, match=message):
        AtkinsRealisAdapter._parse_api_page(body, 1)


def test_rejects_incomplete_api_result_count() -> None:
    listing_html = "<html>AtkinsRéalis projects</html>"

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            if url == make_config().projects_url:
                return FetchResult(url, url, listing_html)
            return FetchResult(
                url,
                url,
                api_page(2, 1, ["/en/projects/only-project"]),
            )

    async def exercise() -> None:
        with pytest.raises(RuntimeError, match="returned 1 of 2 projects"):
            await AtkinsRealisAdapter(make_config()).discover(
                FakeFetcher()  # type: ignore[arg-type]
            )

    asyncio.run(exercise())
