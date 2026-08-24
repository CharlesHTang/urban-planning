from pathlib import Path

import pytest

from architecture_scraper.config import load_sites


def test_loads_site_without_selectors(tmp_path: Path) -> None:
    config = tmp_path / "sites.yml"
    config.write_text(
        """
sites:
  - name: studio
    projects_url: https://studio.test/work
""",
        encoding="utf-8",
    )

    site = load_sites(config)[0]

    assert site.adapter == "capture_only"
    assert site.extractor is None
    assert site.listing_render == "never"
    assert site.detail_render == "never"


def test_rejects_unknown_render_mode(tmp_path: Path) -> None:
    config = tmp_path / "sites.yml"
    config.write_text(
        """
sites:
  - name: studio
    projects_url: https://studio.test/work
    listing_render: sometimes
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="render modes"):
        load_sites(config)


def test_rejects_duplicate_site_names(tmp_path: Path) -> None:
    config = tmp_path / "sites.yml"
    config.write_text(
        """
sites:
  - name: studio
    projects_url: https://studio.test/work
  - name: studio
    projects_url: https://studio.test/projects
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unique"):
        load_sites(config)


def test_loads_optional_extractor_reference(tmp_path: Path) -> None:
    config = tmp_path / "sites.yml"
    config.write_text(
        """
sites:
  - name: studio
    projects_url: https://studio.test/work
    extractor: architecture_scraper.extractors.sites.studio:StudioExtractor
""",
        encoding="utf-8",
    )

    assert load_sites(config)[0].extractor == (
        "architecture_scraper.extractors.sites.studio:StudioExtractor"
    )


def test_rejects_empty_extractor_reference(tmp_path: Path) -> None:
    config = tmp_path / "sites.yml"
    config.write_text(
        """
sites:
  - name: studio
    projects_url: https://studio.test/work
    extractor: ""
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="extractor must be a non-empty string"):
        load_sites(config)
