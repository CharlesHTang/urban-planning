import pytest

from architecture_scraper.cli import _parse_args, _print_summary, _select_sites
from architecture_scraper.config import SiteConfig
from architecture_scraper.models import RunSummary


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


@pytest.mark.parametrize(
    ("arguments", "expected_resume"),
    [
        (["collect", "sites.yml", "--site", "ghd"], False),
        (["collect", "sites.yml", "--site", "ghd", "--resume"], True),
        (
            [
                "fetch-details",
                "sites.yml",
                "ghd",
                "project_urls.txt",
            ],
            False,
        ),
        (
            [
                "fetch-details",
                "sites.yml",
                "ghd",
                "project_urls.txt",
                "--resume",
            ],
            True,
        ),
    ],
)
def test_parses_resume_option(
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
    expected_resume: bool,
) -> None:
    monkeypatch.setattr("sys.argv", ["architecture-scraper", *arguments])

    assert _parse_args().resume is expected_resume


def test_prints_saved_skipped_and_error_counts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    summary = RunSummary(
        saved_pages=3,
        discovered_urls=5,
        errors=[],
        skipped_pages=2,
    )

    _print_summary("ghd", summary)

    assert capsys.readouterr().out == (
        "ghd: saved 3 raw pages; skipped 2 existing detail pages; 0 errors\n"
    )
