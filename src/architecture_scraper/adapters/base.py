from abc import ABC, abstractmethod

from playwright.async_api import Page

from ..config import SiteConfig
from ..fetcher import FetchResult, Fetcher
from ..models import DiscoveryResult, RawPage


class SiteAdapter(ABC):
    """The only layer intended to contain website-specific behavior."""

    def __init__(self, config: SiteConfig) -> None:
        self.config = config

    @abstractmethod
    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        """Capture listing pages and return any discovered project URLs."""

    def listing_from_fetch(self, result: FetchResult) -> RawPage:
        return RawPage(
            site=self.config.name,
            kind="listing",
            requested_url=result.requested_url,
            url=result.url,
            html=result.html,
        )

    async def listing_from_page(
        self, page: Page, *, requested_url: str | None = None
    ) -> RawPage:
        """Capture the fully rendered HTML after custom browser interactions."""
        return RawPage(
            site=self.config.name,
            kind="listing",
            requested_url=requested_url or self.config.projects_url,
            url=page.url,
            html=await page.content(),
        )
