import asyncio
import json

import pytest

from architecture_scraper.adapters.sites.stantec import StantecAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


def make_config() -> SiteConfig:
    return SiteConfig(
        "stantec",
        "https://www.stantec.com/en/projects",
        adapter="architecture_scraper.adapters.sites.stantec:StantecAdapter",
    )


def api_page(total: int, page: int, links: list[str]) -> str:
    return json.dumps(
        {
            "totalResults": total,
            "currPage": page,
            "pages": [{"link": link} for link in links],
        }
    )


def test_discovers_all_paginated_project_api_urls() -> None:
    listing_html = "<html>Stantec projects</html>"
    pages = {
        1: api_page(
            5,
            1,
            [
                "/en/projects/canada-projects/a/project-one.html",
                (
                    "https://www.stantec.com/en/projects/"
                    "united-states-projects/b/project-two.html"
                ),
            ],
        ),
        2: api_page(
            5,
            2,
            [
                "/en/projects/australia-projects/c/project-three.html",
                "/en/projects/uk-projects/d/project-four.html?source=api",
            ],
        ),
        3: api_page(
            5,
            3,
            ["/en/projects/new-zealand-projects/e/project-five.html"],
        ),
    }
    requested_urls: list[str] = []

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            requested_urls.append(url)
            assert render == "never"
            if url == make_config().projects_url:
                return FetchResult(url, url, listing_html)

            page_number = int(url.split("currPage=")[1])
            return FetchResult(url, url, pages[page_number])

    async def exercise() -> None:
        result = await StantecAdapter(make_config()).discover(
            FakeFetcher()  # type: ignore[arg-type]
        )

        assert result.project_urls == [
            (
                "https://www.stantec.com/en/projects/"
                "canada-projects/a/project-one.html"
            ),
            (
                "https://www.stantec.com/en/projects/"
                "united-states-projects/b/project-two.html"
            ),
            (
                "https://www.stantec.com/en/projects/"
                "australia-projects/c/project-three.html"
            ),
            (
                "https://www.stantec.com/en/projects/"
                "uk-projects/d/project-four.html"
            ),
            (
                "https://www.stantec.com/en/projects/"
                "new-zealand-projects/e/project-five.html"
            ),
        ]
        assert result.listing_pages[0].html == listing_html

    asyncio.run(exercise())

    assert requested_urls == [
        make_config().projects_url,
        f"{StantecAdapter.API_URL}?currPage=1",
        f"{StantecAdapter.API_URL}?currPage=2",
        f"{StantecAdapter.API_URL}?currPage=3",
    ]


def test_rejects_invalid_api_json() -> None:
    with pytest.raises(RuntimeError, match="page 1 returned invalid JSON"):
        StantecAdapter._parse_api_page("{", 1)


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ('{"currPage": 1, "pages": []}', "contained no valid total"),
        (
            '{"totalResults": 1, "pages": []}',
            "contained no valid current page",
        ),
        (
            '{"totalResults": 1, "currPage": 1}',
            "contained no pages list",
        ),
        (
            api_page(1, 1, ["https://example.com/en/projects/wrong.html"]),
            "contained an unexpected URL",
        ),
    ],
)
def test_rejects_invalid_api_data(body: str, message: str) -> None:
    with pytest.raises(RuntimeError, match=message):
        StantecAdapter._parse_api_page(body, 1)


def test_rejects_wrong_api_page_number() -> None:
    listing_html = "<html>Stantec projects</html>"

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            if url == make_config().projects_url:
                return FetchResult(url, url, listing_html)
            return FetchResult(
                url,
                url,
                api_page(
                    1,
                    2,
                    ["/en/projects/canada-projects/a/project.html"],
                ),
            )

    async def exercise() -> None:
        with pytest.raises(RuntimeError, match="page 2 when page 1 was requested"):
            await StantecAdapter(make_config()).discover(
                FakeFetcher()  # type: ignore[arg-type]
            )

    asyncio.run(exercise())
