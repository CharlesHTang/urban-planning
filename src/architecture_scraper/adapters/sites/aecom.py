import json

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class AecomAdapter(SiteAdapter):
    """Discover every public AECOM project through its WordPress REST API."""

    API_URL = "https://aecom.com/wp-json/wp/v2/project"
    PAGE_SIZE = 100
    MAX_API_PAGES = 100

    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        listing_response = await fetcher.fetch(
            self.config.projects_url,
            render=self.config.listing_render,
        )
        listing = self.listing_from_fetch(listing_response)

        project_urls: list[str] = []
        for page_number in range(1, self.MAX_API_PAGES + 1):
            response = await fetcher.fetch(
                self._api_page_url(page_number),
                render="never",
            )
            records = self._parse_api_page(response.html, page_number)
            project_urls.extend(record["link"] for record in records)

            if len(records) < self.PAGE_SIZE:
                return DiscoveryResult([listing], project_urls)

        raise RuntimeError(
            f"AECOM project API exceeded {self.MAX_API_PAGES} pages"
        )

    def _api_page_url(self, page_number: int) -> str:
        return (
            f"{self.API_URL}?_fields=link"
            f"&per_page={self.PAGE_SIZE}&page={page_number}"
        )

    @staticmethod
    def _parse_api_page(html: str, page_number: int) -> list[dict[str, str]]:
        try:
            records = json.loads(html)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"AECOM project API page {page_number} returned invalid JSON"
            ) from error

        if not isinstance(records, list):
            raise RuntimeError(
                f"AECOM project API page {page_number} was not a list"
            )

        parsed: list[dict[str, str]] = []
        for record in records:
            link = record.get("link") if isinstance(record, dict) else None
            if not isinstance(link, str) or not link:
                raise RuntimeError(
                    f"AECOM project API page {page_number} contained no link"
                )
            parsed.append({"link": link})
        return parsed

