import json
from dataclasses import asdict, dataclass
from pathlib import Path

from ..config import SiteConfig
from .base import ProjectExtractor
from .loader import load_extractor
from .models import ExtractedProject, ExtractionError, ExtractionSummary
from .storage import ExtractionStore


@dataclass(frozen=True, slots=True)
class _ManifestEntry:
    requested_url: str
    url: str
    path: str
    captured_at: str


class ExtractionRunner:
    """Extract project records from detail HTML listed in the raw manifest."""

    def __init__(
        self,
        site: SiteConfig,
        raw_root: str | Path,
        store: ExtractionStore,
        *,
        extractor: ProjectExtractor | None = None,
    ) -> None:
        self.site = site
        self.raw_root = Path(raw_root)
        self.store = store
        self.extractor = extractor or load_extractor(site)

    def run(self) -> ExtractionSummary:
        entries = self._load_manifest_entries()
        if not entries:
            raise RuntimeError(
                f"No raw detail pages found for site {self.site.name!r}"
            )

        records: list[dict[str, object]] = []
        errors: list[ExtractionError] = []
        for entry in entries:
            try:
                html = self._read_html(entry.path)
                project = self.extractor.extract(html, source_url=entry.url)
                self._validate_project(project)
                records.append(self._record(project, entry))
            except Exception as error:
                errors.append(
                    ExtractionError(
                        firm=self.site.name,
                        source_url=entry.url,
                        source_file=entry.path,
                        message=str(error),
                    )
                )

        self.store.write(self.site.name, records, errors)
        return ExtractionSummary(len(records), errors)

    def _load_manifest_entries(self) -> list[_ManifestEntry]:
        manifest_path = self.raw_root / "manifest.jsonl"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Raw manifest not found: {manifest_path}")

        entries: dict[str, _ManifestEntry] = {}
        for line_number, line in enumerate(
            manifest_path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise RuntimeError(
                    f"Raw manifest line {line_number} is invalid JSON"
                ) from error
            if not isinstance(record, dict):
                raise RuntimeError(
                    f"Raw manifest line {line_number} is not an object"
                )
            if (
                record.get("site") != self.site.name
                or record.get("kind") != "detail"
            ):
                continue

            entry = self._manifest_entry(record, line_number)
            # Redirect aliases can produce different hash-based files for the
            # same final project URL. Extract each final page only once.
            entries[entry.url] = entry
        return list(entries.values())

    @staticmethod
    def _manifest_entry(
        record: dict[str, object],
        line_number: int,
    ) -> _ManifestEntry:
        values: dict[str, str] = {}
        for field in ("requested_url", "url", "path", "captured_at"):
            value = record.get(field)
            if not isinstance(value, str) or not value.strip():
                raise RuntimeError(
                    f"Raw manifest line {line_number} has no valid {field}"
                )
            values[field] = value.strip()
        return _ManifestEntry(**values)

    def _read_html(self, relative_path: str) -> str:
        root = self.raw_root.resolve()
        path = (root / relative_path).resolve()
        if not path.is_relative_to(root):
            raise ValueError(
                f"Raw page path escapes the raw directory: {relative_path}"
            )
        return path.read_text(encoding="utf-8")

    def _record(
        self,
        project: ExtractedProject,
        entry: _ManifestEntry,
    ) -> dict[str, object]:
        return {
            "firm": self.site.name,
            **asdict(project),
            "source_url": entry.url,
            "requested_url": entry.requested_url,
            "source_file": entry.path,
            "captured_at": entry.captured_at,
            "scrape_date": entry.captured_at.split("T", 1)[0],
            "extractor_version": self.extractor.VERSION,
        }

    def _validate_project(self, project: ExtractedProject) -> None:
        if not isinstance(project, ExtractedProject):
            raise TypeError("Extractor did not return an ExtractedProject")
        if (
            not isinstance(project.project_name, str)
            or not project.project_name.strip()
        ):
            raise ValueError("Extracted project has no project name")
        if (
            not isinstance(self.extractor.VERSION, int)
            or isinstance(self.extractor.VERSION, bool)
            or self.extractor.VERSION < 1
        ):
            raise ValueError("Extractor VERSION must be a positive integer")

        for field_name in (
            "headline",
            "description",
            "location_raw",
            "client_raw",
            "status_raw",
            "size_raw",
        ):
            value = getattr(project, field_name)
            if value is not None and not isinstance(value, str):
                raise TypeError(
                    f"Extracted {field_name} must be a string or None"
                )

        for field_name in ("services", "markets", "warnings"):
            values = getattr(project, field_name)
            if not isinstance(values, list) or not all(
                isinstance(value, str) for value in values
            ):
                raise TypeError(f"Extracted {field_name} must be a list of strings")
        if not isinstance(project.facts, dict) or not all(
            isinstance(key, str)
            and (
                isinstance(value, str)
                or (
                    isinstance(value, list)
                    and all(isinstance(item, str) for item in value)
                )
            )
            for key, value in project.facts.items()
        ):
            raise TypeError(
                "Extracted facts must map strings to strings or string lists"
            )
