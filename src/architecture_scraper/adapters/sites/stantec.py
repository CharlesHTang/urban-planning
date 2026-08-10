import json
from urllib.parse import urlencode, urljoin, urlparse

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class StantecAdapter(SiteAdapter):
    """Discover projects from Stantec's public project-grid API."""

    BASE_URL = "https://www.stantec.com"
    API_URL = (
        f"{BASE_URL}/content/stantec/en/projects/"
        "_jcr_content.more.json"
    )
    PROJECT_PATH_PREFIX = "/en/projects/"
    MAX_API_PAGES = 500

    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        listing_response = await fetcher.fetch(
            self.config.projects_url,
            render=self.config.listing_render,
        )
        listing = self.listing_from_fetch(listing_response)

        project_urls: list[str] = []
        expected_total: int | None = None
        for page_number in range(1, self.MAX_API_PAGES + 1):
            response = await fetcher.fetch(
                self._api_page_url(page_number),
                render="never",
            )
            total, current_page, page_urls = self._parse_api_page(
                response.html,
                page_number,
            )
            if current_page != page_number:
                raise RuntimeError(
                    f"Stantec project API returned page {current_page} "
                    f"when page {page_number} was requested"
                )
            if expected_total is None:
                expected_total = total

            project_urls.extend(page_urls)
            if len(project_urls) >= expected_total:
                unique_urls = list(dict.fromkeys(project_urls))
                if len(unique_urls) != expected_total:
                    raise RuntimeError(
                        "Stantec project API returned "
                        f"{len(unique_urls)} of {expected_total} projects"
                    )
                return DiscoveryResult([listing], unique_urls)
            if not page_urls:
                raise RuntimeError(
                    "Stantec project API ended before returning all projects"
                )

        raise RuntimeError(
            f"Stantec project API exceeded {self.MAX_API_PAGES} pages"
        )

    def _api_page_url(self, page_number: int) -> str:
        return f"{self.API_URL}?{urlencode({'currPage': page_number})}"

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
                f"Stantec project API page {page_number} returned invalid JSON"
            ) from error

        if not isinstance(data, dict):
            raise RuntimeError(
                f"Stantec project API page {page_number} was not an object"
            )

        total = data.get("totalResults")
        current_page = data.get("currPage")
        items = data.get("pages")
        if not isinstance(total, int) or isinstance(total, bool) or total < 0:
            raise RuntimeError(
                f"Stantec project API page {page_number} "
                "contained no valid total"
            )
        if (
            not isinstance(current_page, int)
            or isinstance(current_page, bool)
            or current_page < 1
        ):
            raise RuntimeError(
                f"Stantec project API page {page_number} "
                "contained no valid current page"
            )
        if not isinstance(items, list):
            raise RuntimeError(
                f"Stantec project API page {page_number} "
                "contained no pages list"
            )

        project_urls: list[str] = []
        for item in items:
            path = item.get("link") if isinstance(item, dict) else None
            if not isinstance(path, str) or not path:
                raise RuntimeError(
                    f"Stantec project API page {page_number} "
                    "contained no project link"
                )

            url = urljoin(cls.BASE_URL, path)
            parsed = urlparse(url)
            if (
                parsed.scheme != "https"
                or parsed.netloc != "www.stantec.com"
                or not parsed.path.startswith(cls.PROJECT_PATH_PREFIX)
                or not parsed.path.endswith(".html")
            ):
                raise RuntimeError(
                    f"Stantec project API page {page_number} "
                    f"contained an unexpected URL: {url}"
                )
            project_urls.append(f"{cls.BASE_URL}{parsed.path}")

        return total, current_page, project_urls
