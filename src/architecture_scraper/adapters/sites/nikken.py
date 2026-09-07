import json
import re
from urllib.parse import urlparse

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class NikkenAdapter(SiteAdapter):
    """Discover English project pages from Nikken's public project index."""

    BASE_URL = "https://www.nikken.jp"
    INDEX_URL = f"{BASE_URL}/ja/json/projects.json"
    PROJECT_PATH_PATTERN = re.compile(
        r"^/ja/projects/(?:[^/]+/)?[^/]+\.html$"
    )

    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        listing_response = await fetcher.fetch(
            self.config.projects_url,
            render=self.config.listing_render,
        )
        index_response = await fetcher.fetch(self.INDEX_URL, render="never")
        project_urls = self._parse_index(index_response.html)
        return DiscoveryResult(
            [self.listing_from_fetch(listing_response)],
            project_urls,
        )

    @classmethod
    def _parse_index(cls, response_body: str) -> list[str]:
        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as error:
            raise RuntimeError("Nikken project index returned invalid JSON") from error

        items = data.get("array") if isinstance(data, dict) else None
        if not isinstance(items, list):
            raise RuntimeError("Nikken project index contained no project list")

        project_urls: list[str] = []
        for item in items:
            path = item.get("link") if isinstance(item, dict) else None
            if not isinstance(path, str):
                raise RuntimeError("Nikken project index contained no project URL")

            parsed = urlparse(path)
            if (
                parsed.scheme
                or parsed.netloc
                or parsed.query
                or parsed.fragment
                or not cls.PROJECT_PATH_PATTERN.fullmatch(parsed.path)
            ):
                raise RuntimeError(
                    f"Nikken project index contained an unexpected URL: {path}"
                )

            english_path = parsed.path.replace("/ja/", "/en/", 1)
            project_urls.append(f"{cls.BASE_URL}{english_path}")

        if not project_urls:
            raise RuntimeError("Nikken project index contained no project URLs")
        return list(dict.fromkeys(project_urls))
