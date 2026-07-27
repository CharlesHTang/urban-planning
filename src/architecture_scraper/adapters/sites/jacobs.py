from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlparse

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag != "a":
            return
        href = next((value for name, value in attrs if name == "href"), None)
        if href:
            self.hrefs.append(href)


class JacobsAdapter(SiteAdapter):
    """Discover projects from Jacobs's server-rendered project listing."""

    BASE_URL = "https://www.jacobs.com"
    LISTING_URL = f"{BASE_URL}/projects"
    MAX_LISTING_PAGES = 100

    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        first_response = await fetcher.fetch(
            self.config.projects_url,
            render=self.config.listing_render,
        )
        listing_pages = [self.listing_from_fetch(first_response)]
        project_urls, last_page = self._parse_listing(first_response.html)

        if not project_urls:
            raise RuntimeError(
                "Jacobs projects page contained no project detail URLs"
            )
        if last_page >= self.MAX_LISTING_PAGES:
            raise RuntimeError(
                f"Jacobs listing exceeded {self.MAX_LISTING_PAGES} pages"
            )

        for page_number in range(1, last_page + 1):
            response = await fetcher.fetch(
                f"{self.config.projects_url}?page={page_number}",
                render=self.config.listing_render,
            )
            page_urls, _ = self._parse_listing(response.html)
            if not page_urls:
                raise RuntimeError(
                    f"Jacobs listing page {page_number + 1} "
                    "contained no project detail URLs"
                )
            listing_pages.append(self.listing_from_fetch(response))
            project_urls.extend(page_urls)

        return DiscoveryResult(
            listing_pages,
            list(dict.fromkeys(project_urls)),
        )

    @classmethod
    def _parse_listing(cls, html: str) -> tuple[list[str], int]:
        parser = _AnchorParser()
        parser.feed(html)

        project_urls: list[str] = []
        last_page = 0
        for href in parser.hrefs:
            parsed = urlparse(urljoin(cls.LISTING_URL, href))
            path = parsed.path.rstrip("/")
            parts = path.strip("/").split("/")

            if (
                parsed.scheme == "https"
                and parsed.netloc == "www.jacobs.com"
                and len(parts) == 2
                and parts[0] == "projects"
                and parts[1]
            ):
                project_urls.append(f"{cls.BASE_URL}{path}")

            if (
                parsed.netloc == "www.jacobs.com"
                and path == "/projects"
            ):
                for value in parse_qs(parsed.query).get("page", []):
                    if value.isdigit():
                        last_page = max(last_page, int(value))

        return list(dict.fromkeys(project_urls)), last_page
