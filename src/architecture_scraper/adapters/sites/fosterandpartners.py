import asyncio
import json
import re

from ...config import SiteConfig
from ...fetcher import FetchResult, Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class FosterAndPartnersAdapter(SiteAdapter):
    API_URL = "https://content.fosterandpartners.com/api/projects"
    FRONTEND_URL = "https://www.fosterandpartners.com"
    PAGE_SIZE = 100
    MAX_API_PAGES = 10
    REFERENCE_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    def __init__(self, config: SiteConfig) -> None:
        super().__init__(config)
        self._detail_access_ready = False
        self._detail_access_lock = asyncio.Lock()

    @property
    def api_headers(self) -> dict[str, str]:
        return {
            "Origin": self.FRONTEND_URL,
            "Referer": f"{self.FRONTEND_URL}/projects",
        }

    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        response = await fetcher.fetch(
            self.config.projects_url,
            render=self.config.listing_render,
        )
        listing = self.listing_from_fetch(response)

        urls: list[str] = []
        expected_total: int | None = None
        for page_number in range(1, self.MAX_API_PAGES + 1):
            api_response = await fetcher.post_json(
                self.API_URL,
                {
                    "pageSize": self.PAGE_SIZE,
                    "pageIndex": page_number,
                    "orderDirection": "descending",
                },
                headers=self.api_headers,
            )
            total, page_urls = self._parse_api_page(
                api_response.html,
                page_number,
            )
            if expected_total is None:
                expected_total = total
            elif total != expected_total:
                raise RuntimeError("Foster + Partners project total changed mid-run")
            urls.extend(page_urls)
            if len(urls) >= total:
                self._detail_access_ready = True
                return DiscoveryResult([listing], urls[:total])
            if not page_urls:
                raise RuntimeError(
                    "Foster + Partners API ended before returning all projects"
                )
        raise RuntimeError(
            f"Foster + Partners API exceeded {self.MAX_API_PAGES} pages"
        )

    async def fetch_detail(self, fetcher: Fetcher, url: str) -> FetchResult:
        for attempt in range(2):
            try:
                return await fetcher.fetch(url, render="never")
            except Exception:
                if attempt == 1:
                    raise
                self._detail_access_ready = False
                await self._prepare_detail_access(fetcher)
        raise AssertionError("unreachable")

    async def _prepare_detail_access(self, fetcher: Fetcher) -> None:
        async with self._detail_access_lock:
            if self._detail_access_ready:
                return
            await fetcher.fetch(self.config.projects_url, render="never")
            await fetcher.post_json(
                self.API_URL,
                {
                    "pageSize": 1,
                    "pageIndex": 1,
                    "orderDirection": "descending",
                },
                headers=self.api_headers,
            )
            self._detail_access_ready = True

    @classmethod
    def _parse_api_page(
        cls,
        response_body: str,
        page_number: int,
    ) -> tuple[int, list[str]]:
        try:
            payload = json.loads(response_body)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Foster + Partners API page {page_number} returned invalid JSON"
            ) from error
        total = payload.get("totalCount") if isinstance(payload, dict) else None
        items = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(total, int) or total < 0 or not isinstance(items, list):
            raise RuntimeError(
                f"Foster + Partners API page {page_number} was malformed"
            )

        urls: list[str] = []
        for item in items:
            reference = item.get("reference") if isinstance(item, dict) else None
            if (
                not isinstance(reference, str)
                or not cls.REFERENCE_PATTERN.fullmatch(reference)
            ):
                raise RuntimeError(
                    f"Foster + Partners API page {page_number} contained "
                    "an invalid project reference"
                )
            urls.append(f"{cls.API_URL}/{reference}")
        return total, urls
