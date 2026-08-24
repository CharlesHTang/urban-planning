import json
from pathlib import Path

import pytest

from architecture_scraper.config import SiteConfig
from architecture_scraper.extractors import (
    ExtractedProject,
    ExtractionRunner,
    ExtractionStore,
    ProjectExtractor,
    clean_text,
    load_extractor,
)
from architecture_scraper.extractors.loader import _import_extractor
from architecture_scraper.models import RawPage
from architecture_scraper.storage import PageStore


class FakeExtractor(ProjectExtractor):
    VERSION = 3

    def extract(self, html: str, *, source_url: str) -> ExtractedProject:
        if "broken" in html:
            raise ValueError("missing project content")
        return ExtractedProject(
            project_name="Project One",
            description=clean_text(html),
            location_raw="Example City, Example Country",
            services=["Architecture", "Planning"],
            facts={"Year": "2025", "Awards": ["Award One"]},
        )


def make_config(*, extractor: str | None = None) -> SiteConfig:
    return SiteConfig(
        "studio",
        "https://studio.test/projects",
        extractor=extractor,
    )


def test_extracts_manifest_details_and_records_page_errors(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    output_root = tmp_path / "extracted"
    good_page = RawPage(
        site="studio",
        kind="detail",
        requested_url="https://studio.test/projects/one",
        url="https://studio.test/projects/one/",
        html="  A complete\n project description.  ",
    )
    bad_page = RawPage(
        site="studio",
        kind="detail",
        requested_url="https://studio.test/projects/two",
        url="https://studio.test/projects/two/",
        html="broken",
    )
    with PageStore(raw_root) as page_store:
        good_path = page_store.save(good_page)
        page_store.save(good_page)
        page_store.save(bad_page)
        page_store.save(
            RawPage(
                site="other",
                kind="detail",
                requested_url="https://other.test/project",
                url="https://other.test/project",
                html="ignored",
            )
        )

    summary = ExtractionRunner(
        make_config(),
        raw_root,
        ExtractionStore(output_root),
        extractor=FakeExtractor(make_config()),
    ).run()

    assert summary.extracted_projects == 1
    assert len(summary.errors) == 1
    assert summary.errors[0].source_url == bad_page.url
    assert summary.errors[0].message == "missing project content"

    project_record = json.loads(
        (output_root / "studio" / "studio_projects.jsonl").read_text(
            encoding="utf-8"
        )
    )
    assert project_record["firm"] == "studio"
    assert project_record["project_name"] == "Project One"
    assert project_record["description"] == "A complete project description."
    assert project_record["services"] == ["Architecture", "Planning"]
    assert project_record["facts"] == {
        "Year": "2025",
        "Awards": ["Award One"],
    }
    assert project_record["source_url"] == good_page.url
    assert project_record["requested_url"] == good_page.requested_url
    assert project_record["source_file"] == good_path.relative_to(raw_root).as_posix()
    assert project_record["scrape_date"] == project_record["captured_at"][:10]
    assert project_record["extractor_version"] == 3

    error_record = json.loads(
        (output_root / "studio" / "studio_errors.jsonl").read_text(
            encoding="utf-8"
        )
    )
    assert error_record["source_url"] == bad_page.url
    assert error_record["source_file"].endswith(".html")


def test_invalid_project_is_an_error_instead_of_a_record(tmp_path: Path) -> None:
    class EmptyNameExtractor(ProjectExtractor):
        def extract(self, html: str, *, source_url: str) -> ExtractedProject:
            return ExtractedProject(project_name=" ")

    raw_root = tmp_path / "raw"
    with PageStore(raw_root) as page_store:
        page_store.save(
            RawPage(
                site="studio",
                kind="detail",
                requested_url="https://studio.test/projects/one",
                url="https://studio.test/projects/one",
                html="<html>project</html>",
            )
        )

    output_root = tmp_path / "extracted"
    summary = ExtractionRunner(
        make_config(),
        raw_root,
        ExtractionStore(output_root),
        extractor=EmptyNameExtractor(make_config()),
    ).run()

    assert summary.extracted_projects == 0
    assert summary.errors[0].message == "Extracted project has no project name"
    assert (
        output_root / "studio" / "studio_projects.jsonl"
    ).read_text(encoding="utf-8") == ""


def test_extraction_store_overwrites_previous_output(tmp_path: Path) -> None:
    store = ExtractionStore(tmp_path)
    store.write("Studio One", [{"project_name": "Old"}], [])
    projects_path, errors_path = store.write(
        "Studio One",
        [{"project_name": "Current"}],
        [],
    )

    assert json.loads(projects_path.read_text(encoding="utf-8")) == {
        "project_name": "Current"
    }
    assert errors_path.read_text(encoding="utf-8") == ""


def test_loads_configured_extractor() -> None:
    reference = f"{__name__}:FakeExtractor"
    extractor = load_extractor(make_config(extractor=reference))

    assert isinstance(extractor, FakeExtractor)
    assert _import_extractor(reference) is FakeExtractor


def test_rejects_missing_or_invalid_extractor_reference() -> None:
    with pytest.raises(ValueError, match="No extractor configured"):
        load_extractor(make_config())
    with pytest.raises(ValueError, match="use module:ClassName"):
        _import_extractor("not_a_reference")
    with pytest.raises(TypeError, match="not a ProjectExtractor subclass"):
        _import_extractor("architecture_scraper.models:RawPage")


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("  one\n two\tthree  ") == "one two three"
    assert clean_text("   ") is None
    assert clean_text(None) is None
