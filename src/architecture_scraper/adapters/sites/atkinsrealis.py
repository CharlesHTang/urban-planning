import json
from urllib.parse import urlencode, urljoin, urlparse

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class AtkinsRealisAdapter(SiteAdapter):
    """Discover projects from AtkinsRéalis's public project API."""

    BASE_URL = "https://www.atkinsrealis.com"
    API_URL = f"{BASE_URL}/site-services/api/projects"
    PROJECT_PATH_PREFIX = "/en/projects/"
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
            response = await fetcher.fetch(
                self._api_page_url(page_number),
                render="never",
            )
            total, total_pages, page_urls = self._parse_api_page(
                response.html,
                page_number,
            )
            if expected_total is None:
                expected_total = total
                expected_pages = total_pages
                if expected_pages > self.MAX_API_PAGES:
                    raise RuntimeError(
                        "AtkinsRéalis project API exceeded "
                        f"{self.MAX_API_PAGES} pages"
                    )

            project_urls.extend(page_urls)
            if page_number >= expected_pages:
                unique_urls = list(dict.fromkeys(project_urls))
                if len(unique_urls) != expected_total:
                    raise RuntimeError(
                        "AtkinsRéalis project API returned "
                        f"{len(unique_urls)} of {expected_total} projects"
                    )
                return DiscoveryResult([listing], unique_urls)
            if not page_urls:
                raise RuntimeError(
                    "AtkinsRéalis project API ended before returning "
                    "all projects"
                )

        raise RuntimeError(
            f"AtkinsRéalis project API exceeded {self.MAX_API_PAGES} pages"
        )

    def _api_page_url(self, page_number: int) -> str:
        query = urlencode(
            {
                "async": 1,
                "searchinput": "",
                "page": page_number,
                "content-type": "application/json",
            }
        )
        return f"{self.API_URL}?{query}"

    @classmethod
    def _parse_api_page(
        cls,
        response_body: str,
        page_number: int,
    ) -> tuple[int, int, list[str]]:
        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"AtkinsRéalis project API page {page_number} "
                "returned invalid JSON"
            ) from error

        if not isinstance(data, dict):
            raise RuntimeError(
                f"AtkinsRéalis project API page {page_number} "
                "was not an object"
            )
        meta = data.get("meta")
        items = data.get("data")
        if not isinstance(meta, dict):
            raise RuntimeError(
                f"AtkinsRéalis project API page {page_number} "
                "contained no metadata"
            )

        total = meta.get("totalCount")
        total_pages = meta.get("totalPage")
        if not isinstance(total, int) or total < 0:
            raise RuntimeError(
                f"AtkinsRéalis project API page {page_number} "
                "contained no valid total"
            )
        if not isinstance(total_pages, int) or total_pages < 1:
            raise RuntimeError(
                f"AtkinsRéalis project API page {page_number} "
                "contained no valid page count"
            )
        if not isinstance(items, list):
            raise RuntimeError(
                f"AtkinsRéalis project API page {page_number} "
                "contained no data list"
            )

        project_urls: list[str] = []
        for item in items:
            path = item.get("link") if isinstance(item, dict) else None
            if not isinstance(path, str) or not path:
                raise RuntimeError(
                    f"AtkinsRéalis project API page {page_number} "
                    "contained no project link"
                )
            url = urljoin(cls.BASE_URL, path)
            parsed = urlparse(url)
            if (
                parsed.scheme != "https"
                or parsed.netloc != "www.atkinsrealis.com"
                or not parsed.path.startswith(cls.PROJECT_PATH_PREFIX)
            ):
                raise RuntimeError(
                    f"AtkinsRéalis project API page {page_number} "
                    f"contained an unexpected URL: {url}"
                )
            project_urls.append(f"{cls.BASE_URL}{parsed.path.rstrip('/')}")

        return total, total_pages, project_urls
