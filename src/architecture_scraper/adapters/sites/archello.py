import re
from urllib.parse import urlparse
from xml.etree import ElementTree

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class ArchelloAdapter(SiteAdapter):
    """Discover Archello projects from its public sitemap index."""

    BASE_URL = "https://archello.com"
    SITEMAP_INDEX_URL = f"{BASE_URL}/sitemaps/index.xml"
    MAX_PROJECT_SITEMAPS = 1_000
    PROJECT_SITEMAP_PATH = re.compile(
        r"^/sitemaps/projects(?:\.(\d+))?\.xml$"
    )

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
                "Archello sitemap index contained no project sitemaps"
            )
        if len(sitemap_urls) > self.MAX_PROJECT_SITEMAPS:
            raise RuntimeError(
                "Archello sitemap index exceeded "
                f"{self.MAX_PROJECT_SITEMAPS} project sitemaps"
            )

        project_urls: list[str] = []
        for sitemap_number, sitemap_url in enumerate(sitemap_urls, start=1):
            response = await fetcher.fetch(sitemap_url, render="never")
            page_urls = self._parse_project_sitemap(
                response.html,
                sitemap_number,
            )
            if not page_urls:
                raise RuntimeError(
                    f"Archello project sitemap {sitemap_number} "
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

        for element in root.iter():
            if not element.tag.endswith("loc") or not element.text:
                continue
            url = element.text.strip()
            parsed = urlparse(url)
            if (
                parsed.scheme == "https"
                and parsed.netloc == "archello.com"
                and not parsed.query
                and not parsed.fragment
                and cls.PROJECT_SITEMAP_PATH.fullmatch(parsed.path)
            ):
                sitemap_urls.append(url)

        return sorted(
            dict.fromkeys(sitemap_urls),
            key=cls._sitemap_sort_key,
        )

    @classmethod
    def _parse_project_sitemap(
        cls,
        xml: str,
        sitemap_number: int,
    ) -> list[str]:
        root = cls._parse_xml(xml, f"project sitemap {sitemap_number}")
        project_urls: list[str] = []

        for element in root.iter():
            if not element.tag.endswith("loc") or not element.text:
                continue
            parsed = urlparse(element.text.strip())
            path = parsed.path.rstrip("/")
            parts = path.strip("/").split("/")
            if (
                parsed.scheme == "https"
                and parsed.netloc == "archello.com"
                and not parsed.query
                and not parsed.fragment
                and len(parts) == 2
                and parts[0] == "project"
                and parts[1]
            ):
                project_urls.append(f"{cls.BASE_URL}{path}")

        return list(dict.fromkeys(project_urls))

    @staticmethod
    def _parse_xml(xml: str, source: str) -> ElementTree.Element:
        try:
            return ElementTree.fromstring(xml)
        except ElementTree.ParseError as error:
            raise RuntimeError(
                f"Archello {source} returned invalid XML"
            ) from error

    @classmethod
    def _sitemap_sort_key(cls, url: str) -> int:
        match = cls.PROJECT_SITEMAP_PATH.fullmatch(urlparse(url).path)
        if match is None or match.group(1) is None:
            return 0
        return int(match.group(1))
