import re
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree

from ..fetcher import Fetcher
from ..models import DiscoveryResult, RawPage
from .base import SiteAdapter


class SitemapProjectAdapter(SiteAdapter):
    """Shared discovery for sites that publish project URLs in XML sitemaps."""

    SITE_LABEL = "Site"
    HOST = ""
    PROJECT_PATH_PATTERN = re.compile(r"$^")
    EXCLUDED_PROJECT_PATHS: frozenset[str] = frozenset()

    SITEMAP_URLS: tuple[str, ...] = ()
    SITEMAP_INDEX_URL: str | None = None
    SITEMAP_URL_PATTERN: re.Pattern[str] | None = None
    MAX_SITEMAPS = 100

    CAPTURE_LISTING_PAGE = True
    LISTING_URL: str | None = None

    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        listing_pages: list[RawPage] = []
        if self.CAPTURE_LISTING_PAGE:
            listing_response = await fetcher.fetch(
                self.LISTING_URL or self.config.projects_url,
                render=self.config.listing_render,
            )
            listing_pages.append(self.listing_from_fetch(listing_response))

        sitemap_urls = list(self.SITEMAP_URLS)
        if self.SITEMAP_INDEX_URL is not None:
            index_response = await fetcher.fetch(
                self.SITEMAP_INDEX_URL,
                render="never",
            )
            if not listing_pages:
                listing_pages.append(self.listing_from_fetch(index_response))
            sitemap_urls.extend(self._parse_sitemap_index(index_response.html))

        sitemap_urls = list(dict.fromkeys(sitemap_urls))
        if not sitemap_urls:
            raise RuntimeError(
                f"{self.SITE_LABEL} contained no project sitemaps"
            )
        if len(sitemap_urls) > self.MAX_SITEMAPS:
            raise RuntimeError(
                f"{self.SITE_LABEL} exceeded {self.MAX_SITEMAPS} project sitemaps"
            )

        project_urls: list[str] = []
        for sitemap_number, sitemap_url in enumerate(sitemap_urls, start=1):
            response = await fetcher.fetch(sitemap_url, render="never")
            if not listing_pages:
                listing_pages.append(self.listing_from_fetch(response))
            page_urls = self._parse_project_sitemap(
                response.html,
                sitemap_number,
            )
            if not page_urls:
                raise RuntimeError(
                    f"{self.SITE_LABEL} project sitemap {sitemap_number} "
                    "contained no project URLs"
                )
            project_urls.extend(page_urls)

        return DiscoveryResult(
            listing_pages,
            list(dict.fromkeys(project_urls)),
        )

    @classmethod
    def _parse_sitemap_index(cls, xml: str) -> list[str]:
        if cls.SITEMAP_URL_PATTERN is None:
            raise RuntimeError(
                f"{cls.SITE_LABEL} has no sitemap index URL pattern"
            )

        root = cls._parse_xml(xml, "sitemap index")
        sitemap_urls: list[str] = []
        for url in cls._locations(root, "sitemap"):
            parsed = urlparse(url)
            if (
                parsed.scheme == "https"
                and parsed.netloc == cls.HOST
                and not parsed.fragment
                and cls.SITEMAP_URL_PATTERN.fullmatch(url)
            ):
                sitemap_urls.append(url)

        if not sitemap_urls:
            raise RuntimeError(
                f"{cls.SITE_LABEL} sitemap index contained no project sitemaps"
            )
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
        for url in cls._locations(root, "url"):
            parsed = urlparse(url)
            if (
                parsed.scheme == "https"
                and parsed.netloc == cls.HOST
                and not parsed.query
                and not parsed.fragment
                and parsed.path not in cls.EXCLUDED_PROJECT_PATHS
                and cls.PROJECT_PATH_PATTERN.fullmatch(parsed.path)
            ):
                project_urls.append(url)
        return list(dict.fromkeys(project_urls))

    @classmethod
    def _parse_xml(cls, xml: str, source: str) -> ElementTree.Element:
        try:
            return ElementTree.fromstring(xml)
        except ElementTree.ParseError as error:
            raise RuntimeError(
                f"{cls.SITE_LABEL} {source} returned invalid XML"
            ) from error

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
    def _sitemap_sort_key(url: str) -> tuple[int, int | str]:
        pages = parse_qs(urlparse(url).query).get("page", [])
        if len(pages) == 1 and pages[0].isdigit():
            return 0, int(pages[0])
        return 1, url
