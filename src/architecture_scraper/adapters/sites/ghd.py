import json
from urllib.parse import urlparse

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class GhdAdapter(SiteAdapter):
    """Discover global-English projects from GHD's public search endpoint."""

    API_URL = "https://aughd.sc-apj.ghd.com/api/discover/v2/"
    BASE_URL = "https://www.ghd.com"
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
        for page_number in range(1, self.MAX_API_PAGES + 1):
            response = await fetcher.post_json(
                self.API_URL,
                self._api_payload(page_number),
                headers={
                    "Origin": self.BASE_URL,
                    "Referer": self.config.projects_url,
                },
            )
            total, page_urls = self._parse_api_page(response.html, page_number)
            if expected_total is None:
                expected_total = total
            elif total != expected_total:
                raise RuntimeError("GHD project API total changed during pagination")

            project_urls.extend(page_urls)
            if len(project_urls) >= expected_total:
                unique_urls = list(dict.fromkeys(project_urls))
                if len(unique_urls) != expected_total:
                    raise RuntimeError(
                        f"GHD project API returned {len(unique_urls)} "
                        f"of {expected_total} projects"
                    )
                return DiscoveryResult([listing], unique_urls)
            if not page_urls:
                raise RuntimeError(
                    "GHD project API ended before returning all projects"
                )

        raise RuntimeError(f"GHD project API exceeded {self.MAX_API_PAGES} pages")

    def _api_payload(self, page_number: int) -> dict[str, object]:
        return {
            "widget": {
                "items": [
                    {
                        "entity": "content",
                        "rfk_id": "ghd_search_results_page",
                        "sources": ["1050582"],
                        "search": {
                            "content": {},
                            "query": {},
                            "filter": {
                                "type": "and",
                                "filters": [
                                    {
                                        "name": "type",
                                        "type": "eq",
                                        "value": "Projects",
                                    }
                                ],
                            },
                            "sort": {
                                "value": [
                                    {
                                        "name": "created_date",
                                        "order": "desc",
                                    }
                                ],
                                "choices": True,
                            },
                            "limit": self.PAGE_SIZE,
                            "offset": self.PAGE_SIZE * (page_number - 1),
                            "facet": {"all": True, "max": 30},
                        },
                    }
                ]
            },
            "context": {"locale": {"country": "jm", "language": "en"}},
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
                f"GHD project API page {page_number} returned invalid JSON"
            ) from error

        widgets = data.get("widgets") if isinstance(data, dict) else None
        widget = widgets[0] if isinstance(widgets, list) and widgets else None
        if not isinstance(widget, dict):
            raise RuntimeError(
                f"GHD project API page {page_number} contained no result widget"
            )

        total = widget.get("total_item")
        items = widget.get("content")
        if not isinstance(total, int) or isinstance(total, bool) or total < 0:
            raise RuntimeError(
                f"GHD project API page {page_number} contained no valid total"
            )
        if not isinstance(items, list):
            raise RuntimeError(
                f"GHD project API page {page_number} contained no content list"
            )

        project_urls: list[str] = []
        for item in items:
            url = item.get("url") if isinstance(item, dict) else None
            if not isinstance(url, str):
                raise RuntimeError(
                    f"GHD project API page {page_number} contained no URL"
                )
            parsed = urlparse(url)
            path_parts = parsed.path.rstrip("/").split("/")
            is_global_path = (
                len(path_parts) == 3
                and path_parts[1] == "projects"
                and bool(path_parts[2])
            )
            is_english_path = (
                len(path_parts) == 4
                and path_parts[1:3] == ["en", "projects"]
                and bool(path_parts[3])
            )
            if (
                parsed.scheme != "https"
                or parsed.netloc != "www.ghd.com"
                or parsed.query
                or parsed.fragment
                or not (is_global_path or is_english_path)
            ):
                raise RuntimeError(
                    f"GHD project API page {page_number} contained "
                    f"an unexpected URL: {url}"
                )
            slug = path_parts[-1]
            project_urls.append(f"{cls.BASE_URL}/en/projects/{slug}")

        return total, project_urls
