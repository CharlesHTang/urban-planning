import json
from pathlib import Path

from ..storage import _safe_name
from .models import ExtractionError


class ExtractionStore:
    """Write deterministic per-firm project and error JSONL files."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def write(
        self,
        site: str,
        records: list[dict[str, object]],
        errors: list[ExtractionError],
    ) -> tuple[Path, Path]:
        directory = self.root / _safe_name(site)
        directory.mkdir(parents=True, exist_ok=True)

        projects_path = directory / f"{_safe_name(site)}_projects.jsonl"
        errors_path = directory / f"{_safe_name(site)}_errors.jsonl"
        self._write_jsonl(projects_path, records)
        self._write_jsonl(
            errors_path,
            [
                {
                    "firm": error.firm,
                    "source_url": error.source_url,
                    "source_file": error.source_file,
                    "message": error.message,
                }
                for error in errors
            ],
        )
        return projects_path, errors_path

    @staticmethod
    def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
        content = "".join(
            json.dumps(record, ensure_ascii=False) + "\n"
            for record in records
        )
        path.write_text(content, encoding="utf-8")
