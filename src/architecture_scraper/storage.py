import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from .models import PageKind, RawPage


class PageStore:
    """Store each raw page as HTML and append its location to a manifest."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._manifest: TextIO | None = None

    def __enter__(self) -> "PageStore":
        self.root.mkdir(parents=True, exist_ok=True)
        self._manifest = (self.root / "manifest.jsonl").open("a", encoding="utf-8")
        return self

    def __exit__(self, *_: object) -> None:
        if self._manifest is not None:
            self._manifest.close()

    def save(self, page: RawPage) -> Path:
        if self._manifest is None:
            raise RuntimeError("PageStore must be used as a context manager")

        relative_path = self._page_path(page)
        full_path = self.root / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = full_path.with_suffix(f"{full_path.suffix}.tmp")
        temporary_path.write_text(page.html, encoding="utf-8")
        temporary_path.replace(full_path)

        record = {
            "site": page.site,
            "kind": page.kind,
            "requested_url": page.requested_url,
            "url": page.url,
            "path": relative_path.as_posix(),
            "captured_at": datetime.now(UTC).isoformat(),
        }
        self._manifest.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._manifest.flush()
        return full_path

    def has_page(self, site: str, kind: PageKind, requested_url: str) -> bool:
        """Return whether a non-empty page has already been saved."""
        path = self.root / self._page_path_for(site, kind, requested_url)
        return path.is_file() and path.stat().st_size > 0

    def save_project_urls(self, site: str, urls: list[str]) -> Path:
        directory = self.root / _safe_name(site)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "project_urls.txt"
        content = "".join(f"{url}\n" for url in urls)
        path.write_text(content, encoding="utf-8")
        return path

    def _page_path(self, page: RawPage) -> Path:
        return self._page_path_for(page.site, page.kind, page.requested_url)

    @staticmethod
    def _page_path_for(site: str, kind: PageKind, requested_url: str) -> Path:
        digest = hashlib.sha256(requested_url.encode()).hexdigest()[:16]
        return Path(_safe_name(site), kind, f"{digest}.html")


def _safe_name(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-.")
    return safe or "site"
