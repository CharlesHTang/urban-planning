import json
from urllib.parse import urljoin, urlparse

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class ArupAdapter(SiteAdapter):
    """Discover projects from Arup's public project-listing API."""

    BASE_URL = "https://www.arup.com"
    API_URL = f"{BASE_URL}/en-US/api/projects"
    PROJECT_PATH_PREFIX = "/en-us/projects/"
    INITIAL_FILTERS = (
        "ArticleTypesTaxonomies: { Id: { in : [103] } } "
        "ExcludeFromSearchListing: { notEq : true }"
    )
    PAGE_SIZE = 20
    MAX_API_PAGES = 100

    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        listing_response = await fetcher.fetch(
            self.config.projects_url,
            render=self.config.listing_render,
        )
        listing = self.listing_from_fetch(listing_response)

        project_urls: list[str] = []
        expected_total: int | None = None
        expected_pages: int | None = None
        for page_number in range(1, self.MAX_API_PAGES + 1):
            response = await fetcher.post_json(
                self.API_URL,
                self._api_payload(page_number),
                headers={
                    "Origin": self.BASE_URL,
                    "Referer": self.config.projects_url,
                },
            )
            total, current_page, total_pages, page_urls = self._parse_api_page(
                response.html,
                page_number,
            )
            if current_page != page_number:
                raise RuntimeError(
                    f"Arup project API returned page {current_page} "
                    f"when page {page_number} was requested"
                )
            if expected_total is None:
                expected_total = total
                expected_pages = total_pages
                if expected_pages > self.MAX_API_PAGES:
                    raise RuntimeError(
                        "Arup project API exceeded "
                        f"{self.MAX_API_PAGES} pages"
                    )

            project_urls.extend(page_urls)
            if page_number >= expected_pages:
                unique_urls = list(dict.fromkeys(project_urls))
                if len(unique_urls) != expected_total:
                    raise RuntimeError(
                        "Arup project API returned "
                        f"{len(unique_urls)} of {expected_total} projects"
                    )
                return DiscoveryResult([listing], unique_urls)
            if not page_urls:
                raise RuntimeError(
                    "Arup project API ended before returning all projects"
                )

        raise RuntimeError(
            f"Arup project API exceeded {self.MAX_API_PAGES} pages"
        )

    def _api_payload(self, page_number: int) -> dict[str, object]:
        return {
            "pageNumber": page_number,
            "pageSize": self.PAGE_SIZE,
            "lang": "en-US",
            "filters": [],
            "keywords": "",
            "initialFilters": self.INITIAL_FILTERS,
        }

    @classmethod
    def _parse_api_page(
        cls,
        response_body: str,
        page_number: int,
    ) -> tuple[int, int, int, list[str]]:
        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Arup project API page {page_number} returned invalid JSON"
            ) from error

        if not isinstance(data, dict):
            raise RuntimeError(
                f"Arup project API page {page_number} was not an object"
            )

        total = data.get("total")
        current_page = data.get("currentPage")
        page_size = data.get("pageSize")
        total_pages = data.get("numberOfPages")
        groups = data.get("grouped")
        if not cls._is_non_negative_int(total):
            raise RuntimeError(
                f"Arup project API page {page_number} contained no valid total"
            )
        if not cls._is_positive_int(current_page):
            raise RuntimeError(
                f"Arup project API page {page_number} "
                "contained no valid current page"
            )
        if not cls._is_positive_int(page_size):
            raise RuntimeError(
                f"Arup project API page {page_number} "
                "contained no valid page size"
            )
        if not cls._is_positive_int(total_pages):
            raise RuntimeError(
                f"Arup project API page {page_number} "
                "contained no valid page count"
            )
        if not isinstance(groups, list):
            raise RuntimeError(
                f"Arup project API page {page_number} "
                "contained no grouped list"
            )

        project_urls: list[str] = []
        for group in groups:
            if not isinstance(group, list):
                raise RuntimeError(
                    f"Arup project API page {page_number} "
                    "contained an invalid project group"
                )
            for item in group:
                path = item.get("url") if isinstance(item, dict) else None
                if not isinstance(path, str) or not path:
                    raise RuntimeError(
                        f"Arup project API page {page_number} "
                        "contained no project URL"
                    )

                url = urljoin(cls.BASE_URL, path)
                parsed = urlparse(url)
                normalized_path = parsed.path.rstrip("/")
                parts = normalized_path.strip("/").split("/")
                if (
                    parsed.scheme != "https"
                    or parsed.netloc != "www.arup.com"
                    or not normalized_path.startswith(cls.PROJECT_PATH_PREFIX)
                    or len(parts) != 3
                    or parts[:2] != ["en-us", "projects"]
                    or not parts[2]
                    or parts[2] == "all-projects"
                ):
                    raise RuntimeError(
                        f"Arup project API page {page_number} "
                        f"contained an unexpected URL: {url}"
                    )
                project_urls.append(f"{cls.BASE_URL}{normalized_path}/")

        return total, current_page, total_pages, project_urls

    @staticmethod
    def _is_positive_int(value: object) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and value > 0

    @staticmethod
    def _is_non_negative_int(value: object) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0
