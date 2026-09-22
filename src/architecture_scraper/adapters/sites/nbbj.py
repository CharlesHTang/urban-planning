import json
import re

from bs4 import BeautifulSoup

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class NbbjAdapter(SiteAdapter):
    BASE_URL = "https://www.nbbj.com"
    PROJECT_UID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        response = await fetcher.fetch(
            self.config.projects_url,
            render=self.config.listing_render,
        )
        listing = self.listing_from_fetch(response)
        return DiscoveryResult([listing], self._parse_listing(response.html))

    @classmethod
    def _parse_listing(cls, html: str) -> list[str]:
        node = BeautifulSoup(html, "html.parser").find(
            "script",
            id="__NEXT_DATA__",
        )
        if node is None:
            raise RuntimeError("NBBJ listing contained no __NEXT_DATA__ record")
        try:
            payload = json.loads(node.string or node.get_text())
            items = payload["props"]["pageProps"]["finalItems"]
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise RuntimeError("NBBJ listing data was malformed") from error
        if not isinstance(items, list):
            raise RuntimeError("NBBJ listing contained no project list")

        urls: list[str] = []
        for item in items:
            if not isinstance(item, dict) or item.get("type") != "project":
                continue
            uid = item.get("uid")
            if not isinstance(uid, str) or not cls.PROJECT_UID_PATTERN.fullmatch(uid):
                raise RuntimeError("NBBJ listing contained an invalid project UID")
            urls.append(f"{cls.BASE_URL}/work/{uid}")
        if not urls:
            raise RuntimeError("NBBJ listing contained no project URLs")
        return list(dict.fromkeys(urls))
