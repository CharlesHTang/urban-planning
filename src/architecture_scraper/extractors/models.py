from dataclasses import dataclass, field
from typing import TypeAlias

FactValue: TypeAlias = str | list[str]


@dataclass(frozen=True, slots=True)
class ExtractedProject:
    """Common project fields returned by every site-specific extractor."""

    project_name: str
    headline: str | None = None
    description: str | None = None
    location_raw: str | None = None
    client_raw: str | None = None
    status_raw: str | None = None
    size_raw: str | None = None
    services: list[str] = field(default_factory=list)
    markets: list[str] = field(default_factory=list)
    facts: dict[str, FactValue] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ExtractionError:
    firm: str
    source_url: str
    source_file: str
    message: str


@dataclass(frozen=True, slots=True)
class ExtractionSummary:
    extracted_projects: int
    errors: list[ExtractionError]
