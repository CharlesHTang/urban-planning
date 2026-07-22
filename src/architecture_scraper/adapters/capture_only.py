from ..fetcher import Fetcher
from ..models import DiscoveryResult
from .base import SiteAdapter


class CaptureOnlyAdapter(SiteAdapter):
    """Save the complete known projects page and defer URL discovery."""

    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        result = await fetcher.fetch(
            self.config.projects_url,
            render=self.config.listing_render,
        )
        return DiscoveryResult(listing_pages=[self.listing_from_fetch(result)])

