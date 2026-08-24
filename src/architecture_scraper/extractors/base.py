from abc import ABC, abstractmethod

from ..config import SiteConfig
from .models import ExtractedProject


class ProjectExtractor(ABC):
    """The only layer intended to contain site-specific HTML selectors."""

    VERSION = 1

    def __init__(self, config: SiteConfig) -> None:
        self.config = config

    @abstractmethod
    def extract(self, html: str, *, source_url: str) -> ExtractedProject:
        """Extract one project from one already-downloaded detail page."""


def clean_text(value: str | None) -> str | None:
    """Collapse HTML whitespace and preserve a missing value as None."""
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None
