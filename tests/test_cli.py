import pytest

from architecture_scraper.cli import _parse_args, _select_sites
from architecture_scraper.config import SiteConfig


def test_select_sites_returns_all_sites_when_name_is_omitted() -> None:
    sites = [
        SiteConfig("one", "https://one.test/projects"),
        SiteConfig("two", "https://two.test/projects"),
    ]

    assert _select_sites(sites, None) == sites


def test_select_sites_returns_only_named_site() -> None:
    sites = [
        SiteConfig("one", "https://one.test/projects"),
        SiteConfig("two", "https://two.test/projects"),
    ]

    assert _select_sites(sites, "two") == [sites[1]]


def test_select_sites_rejects_unknown_name() -> None:
    sites = [SiteConfig("one", "https://one.test/projects")]

    with pytest.raises(ValueError, match="No site named 'missing'"):
        _select_sites(sites, "missing")


def test_parses_extract_command(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "architecture-scraper",
            "extract",
            "sites.yml",
            "--site",
            "sweco",
            "--raw",
            "raw-pages",
            "-o",
            "data/1_extract",
        ],
    )

    args = _parse_args()

    assert args.command == "extract"
    assert args.site == "sweco"
    assert args.raw.name == "raw-pages"
    assert args.output.as_posix() == "data/1_extract"
