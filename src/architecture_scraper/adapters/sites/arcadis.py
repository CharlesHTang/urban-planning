import json
from urllib.parse import urljoin, urlparse

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class ArcadisAdapter(SiteAdapter):
    """Discover projects shown in Arcadis's global-English project grid."""

    API_URL = "https://www.arcadis.com/en/api/v1/search"
    BASE_URL = "https://www.arcadis.com"
    PROJECT_PATH_PREFIX = "/en/projects/"
    PAGE_SIZE = 100
    MAX_API_PAGES = 100

    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        listing_response = await fetcher.fetch(
            self.config.projects_url,
            render=self.config.listing_render,
        )
        listing = self.listing_from_fetch(listing_response)

        project_urls: list[str] = []
        expected_total: int | None = None
        for page_number in range(self.MAX_API_PAGES):
            skip = page_number * self.PAGE_SIZE
            response = await fetcher.post_json(
                self.API_URL,
                self._api_payload(skip),
                headers={
                    "Origin": self.BASE_URL,
                    "Referer": self.config.projects_url,
                },
            )
            total, page_urls = self._parse_api_page(response.html, page_number + 1)
            if expected_total is None:
                expected_total = total
            project_urls.extend(page_urls)

            if len(project_urls) >= expected_total:
                return DiscoveryResult([listing], project_urls[:expected_total])
            if not page_urls:
                raise RuntimeError(
                    "Arcadis project API ended before returning all projects"
                )

        raise RuntimeError(
            f"Arcadis project API exceeded {self.MAX_API_PAGES} pages"
        )

    def _api_payload(self, skip: int) -> dict[str, object]:
        query_string = (
            f"main.sk={skip}&main.t={self.PAGE_SIZE}"
            "&main.fa=&main.fi=ContentType.ProjectPageModel"
        )
        return {
            "culture": "en",
            "scope": "main",
            "queryString": query_string,
            "filters": [
                {
                    "type": "ContentType",
                    "values": ["ProjectPageModel"],
                }
            ],
            "facets": [
                {"type": "Service", "values": []},
                {"type": "Country", "values": []},
            ],
            "skip": skip,
            "take": self.PAGE_SIZE,
            "sort": "newest",
            "query": "",
        }

    @classmethod
    def _parse_api_page(
        cls,
        response_body: str,
        page_number: int,
    ) -> tuple[int, list[str]]:
        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Arcadis project API page {page_number} returned invalid JSON"
            ) from error

        if not isinstance(data, dict):
            raise RuntimeError(
                f"Arcadis project API page {page_number} was not an object"
            )
        total = data.get("total")
        items = data.get("items")
        if not isinstance(total, int) or total < 0:
            raise RuntimeError(
                f"Arcadis project API page {page_number} contained no valid total"
            )
        if not isinstance(items, list):
            raise RuntimeError(
                f"Arcadis project API page {page_number} contained no items list"
            )

        project_urls: list[str] = []
        for item in items:
            path = item.get("url") if isinstance(item, dict) else None
            if not isinstance(path, str) or not path:
                raise RuntimeError(
                    f"Arcadis project API page {page_number} contained no URL"
                )
            url = urljoin(cls.BASE_URL, path)
            parsed = urlparse(url)
            if (
                parsed.scheme != "https"
                or parsed.netloc != "www.arcadis.com"
                or not parsed.path.startswith(cls.PROJECT_PATH_PREFIX)
            ):
                raise RuntimeError(
                    f"Arcadis project API page {page_number} contained "
                    f"an unexpected URL: {url}"
                )
            project_urls.append(url)

        return total, project_urls
