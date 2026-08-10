from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class HdrAdapter(SiteAdapter):
    """Discover HDR projects from its public sitemap index."""

    BASE_URL = "https://www.hdrinc.com"
    SITEMAP_INDEX_URL = f"{BASE_URL}/sitemap.xml"
    SITEMAP_PATH = "/sitemap.xml"
    MAX_SITEMAPS = 100

    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        listing_response = await fetcher.fetch(
            self.config.projects_url,
            render=self.config.listing_render,
        )
        listing = self.listing_from_fetch(listing_response)

        index_response = await fetcher.fetch(
            self.SITEMAP_INDEX_URL,
            render="never",
        )
        sitemap_urls = self._parse_sitemap_index(index_response.html)
        if not sitemap_urls:
            raise RuntimeError("HDR sitemap index contained no sitemap pages")
        if len(sitemap_urls) > self.MAX_SITEMAPS:
            raise RuntimeError(
                f"HDR sitemap index exceeded {self.MAX_SITEMAPS} pages"
            )

        project_urls: list[str] = []
        for page_number, sitemap_url in enumerate(sitemap_urls, start=1):
            response = await fetcher.fetch(sitemap_url, render="never")
            project_urls.extend(
                self._parse_sitemap_page(response.html, page_number)
            )

        unique_urls = list(dict.fromkeys(project_urls))
        if not unique_urls:
            raise RuntimeError("HDR sitemaps contained no portfolio URLs")
        return DiscoveryResult([listing], unique_urls)

    @classmethod
    def _parse_sitemap_index(cls, xml: str) -> list[str]:
        root = cls._parse_xml(xml, "sitemap index")
        sitemap_urls: list[str] = []
        for url in cls._locations(root, "sitemap"):
            if cls._sitemap_page_number(url) is not None:
                sitemap_urls.append(url)

        return sorted(
            dict.fromkeys(sitemap_urls),
            key=cls._sitemap_page_number,
        )

    @classmethod
    def _parse_sitemap_page(
        cls,
        xml: str,
        page_number: int,
    ) -> list[str]:
        root = cls._parse_xml(xml, f"sitemap page {page_number}")
        project_urls: list[str] = []
        for url in cls._locations(root, "url"):
            parsed = urlparse(url)
            path = parsed.path.rstrip("/")
            parts = path.strip("/").split("/")
            if (
                parsed.scheme == "https"
                and parsed.netloc == "www.hdrinc.com"
                and not parsed.query
                and not parsed.fragment
                and len(parts) == 2
                and parts[0] == "portfolio"
                and parts[1]
            ):
                project_urls.append(f"{cls.BASE_URL}{path}")

        return list(dict.fromkeys(project_urls))

    @classmethod
    def _sitemap_page_number(cls, url: str) -> int | None:
        parsed = urlparse(url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        if (
            parsed.scheme != "https"
            or parsed.netloc != "www.hdrinc.com"
            or parsed.path != cls.SITEMAP_PATH
            or parsed.fragment
            or set(query) != {"page"}
            or len(query["page"]) != 1
            or not query["page"][0].isdigit()
        ):
            return None

        page_number = int(query["page"][0])
        return page_number if page_number > 0 else None

    @classmethod
    def _locations(
        cls,
        root: ElementTree.Element,
        parent_name: str,
    ) -> list[str]:
        locations: list[str] = []
        for parent in root:
            if cls._local_name(parent.tag) != parent_name:
                continue
            for child in parent:
                if cls._local_name(child.tag) == "loc" and child.text:
                    locations.append(child.text.strip())
        return locations

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    @staticmethod
    def _parse_xml(xml: str, source: str) -> ElementTree.Element:
        try:
            return ElementTree.fromstring(xml)
        except ElementTree.ParseError as error:
            raise RuntimeError(f"HDR {source} returned invalid XML") from error
