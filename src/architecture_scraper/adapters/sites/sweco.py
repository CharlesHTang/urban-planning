import re
from urllib.parse import urlparse
from xml.etree import ElementTree

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class SwecoAdapter(SiteAdapter):
    """Discover Sweco projects from its public portfolio sitemaps."""

    BASE_URL = "https://www.swecogroup.com"
    SITEMAP_INDEX_URL = f"{BASE_URL}/sitemaps.xml"
    PORTFOLIO_SITEMAP_PATH = re.compile(
        r"^/showroom_cpt-sitemap(\d+)\.xml$"
    )
    MAX_PORTFOLIO_SITEMAPS = 100

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
            raise RuntimeError(
                "Sweco sitemap index contained no portfolio sitemaps"
            )
        if len(sitemap_urls) > self.MAX_PORTFOLIO_SITEMAPS:
            raise RuntimeError(
                "Sweco sitemap index exceeded "
                f"{self.MAX_PORTFOLIO_SITEMAPS} portfolio sitemaps"
            )

        project_urls: list[str] = []
        for sitemap_number, sitemap_url in enumerate(sitemap_urls, start=1):
            response = await fetcher.fetch(sitemap_url, render="never")
            page_urls = self._parse_portfolio_sitemap(
                response.html,
                sitemap_number,
            )
            if not page_urls:
                raise RuntimeError(
                    f"Sweco portfolio sitemap {sitemap_number} "
                    "contained no project URLs"
                )
            project_urls.extend(page_urls)

        return DiscoveryResult(
            [listing],
            list(dict.fromkeys(project_urls)),
        )

    @classmethod
    def _parse_sitemap_index(cls, xml: str) -> list[str]:
        root = cls._parse_xml(xml, "sitemap index")
        sitemap_urls: list[str] = []
        for url in cls._locations(root, "sitemap"):
            parsed = urlparse(url)
            if (
                parsed.scheme == "https"
                and parsed.netloc == "www.swecogroup.com"
                and not parsed.query
                and not parsed.fragment
                and cls.PORTFOLIO_SITEMAP_PATH.fullmatch(parsed.path)
            ):
                sitemap_urls.append(url)

        return sorted(
            dict.fromkeys(sitemap_urls),
            key=cls._sitemap_sort_key,
        )

    @classmethod
    def _parse_portfolio_sitemap(
        cls,
        xml: str,
        sitemap_number: int,
    ) -> list[str]:
        root = cls._parse_xml(xml, f"portfolio sitemap {sitemap_number}")
        project_urls: list[str] = []
        for url in cls._locations(root, "url"):
            parsed = urlparse(url)
            path = parsed.path.rstrip("/")
            parts = path.strip("/").split("/")
            if (
                parsed.scheme == "https"
                and parsed.netloc == "www.swecogroup.com"
                and not parsed.query
                and not parsed.fragment
                and len(parts) == 3
                and parts[0] == "portfolio"
                and parts[1]
                and parts[2]
            ):
                project_urls.append(f"{cls.BASE_URL}{path}/")

        return list(dict.fromkeys(project_urls))

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
            raise RuntimeError(
                f"Sweco {source} returned invalid XML"
            ) from error

    @classmethod
    def _sitemap_sort_key(cls, url: str) -> int:
        match = cls.PORTFOLIO_SITEMAP_PATH.fullmatch(urlparse(url).path)
        return int(match.group(1)) if match else 0
