from dataclasses import dataclass, field
from typing import Literal, TypeAlias

PageKind: TypeAlias = Literal["listing", "detail"]


@dataclass(frozen=True, slots=True)
class RawPage:
    site: str
    kind: PageKind
    requested_url: str
    url: str
    html: str


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    listing_pages: list[RawPage]
    project_urls: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ScrapeError:
    site: str
    url: str
    message: str


@dataclass(frozen=True, slots=True)
class RunSummary:
    saved_pages: int
    discovered_urls: int
    errors: list[ScrapeError]

