from urllib.parse import urlparse
from xml.etree import ElementTree

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class WspAdapter(SiteAdapter):
    """Discover WSP Global projects through its public en-gl sitemap."""

    SITEMAP_URL = "https://www.wsp.com/sitemap/sitemap-en-gl.xml"
    PROJECT_PATH_PREFIX = "/en-gl/projects/"

    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        response = await fetcher.fetch(self.SITEMAP_URL, render="never")
        project_urls = self._parse_sitemap(response.html)
        if not project_urls:
            raise RuntimeError("WSP sitemap contained no en-gl project URLs")

        listing = self.listing_from_fetch(response)
        return DiscoveryResult([listing], project_urls)

    @classmethod
    def _parse_sitemap(cls, xml: str) -> list[str]:
        try:
            root = ElementTree.fromstring(xml)
        except ElementTree.ParseError as error:
            raise RuntimeError("WSP sitemap returned invalid XML") from error

        project_urls: list[str] = []
        for element in root.iter():
            if not element.tag.endswith("loc") or not element.text:
                continue
            url = element.text.strip()
            parsed = urlparse(url)
            if (
                parsed.scheme == "https"
                and parsed.netloc == "www.wsp.com"
                and parsed.path.startswith(cls.PROJECT_PATH_PREFIX)
            ):
                project_urls.append(url)
        return project_urls

