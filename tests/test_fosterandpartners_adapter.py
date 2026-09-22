import asyncio
import json

from architecture_scraper.adapters.sites.fosterandpartners import (
    FosterAndPartnersAdapter,
)
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


def test_parses_foster_project_api_page() -> None:
    body = json.dumps(
        {
            "totalCount": 2,
            "data": [
                {"reference": "project-one"},
                {"reference": "project-two"},
            ],
        }
    )

    total, urls = FosterAndPartnersAdapter._parse_api_page(body, 1)

    assert total == 2
    assert urls == [
        "https://content.fosterandpartners.com/api/projects/project-one",
        "https://content.fosterandpartners.com/api/projects/project-two",
    ]


def test_prepares_api_session_when_fetching_details_directly() -> None:
    config = SiteConfig(
        "fosterandpartners",
        "https://www.fosterandpartners.com/projects",
    )
    adapter = FosterAndPartnersAdapter(config)
    detail_url = f"{adapter.API_URL}/project-one"
    detail_attempts = 0
    posted = False

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            nonlocal detail_attempts
            if url == detail_url:
                detail_attempts += 1
                if detail_attempts == 1:
                    raise RuntimeError("session required")
                return FetchResult(url, url, '{"title":"Project One"}')
            assert url == config.projects_url
            return FetchResult(url, url, "listing")

        async def post_json(
            self,
            url: str,
            payload: object,
            *,
            headers: dict[str, str] | None = None,
        ) -> FetchResult:
            nonlocal posted
            posted = True
            return FetchResult(url, url, "{}")

    result = asyncio.run(
        adapter.fetch_detail(FakeFetcher(), detail_url)  # type: ignore[arg-type]
    )

    assert result.html == '{"title":"Project One"}'
    assert detail_attempts == 2
    assert posted is True
